import copy
import functools
import logging
import os
import re
import uuid
import xml.sax.saxutils
from datetime import datetime
from datetime import timedelta
from threading import RLock
from threading import Timer

import ijson
import pytz
import requests
import tzlocal
from lxml import etree
from persistent.list import PersistentList

from .constants import SMOOTH_STREAMS_EPG_BASE_URL
from .constants import SMOOTH_STREAMS_EPG_FILE_NAME
from .constants import SMOOTH_STREAMS_FOG_EPG_BASE_URL
from .constants import SMOOTH_STREAMS_FOG_EPG_FILE_NAME
from .db import SmoothStreamsDB
from ...configuration import IPTVProxyConfiguration
from ...constants import CHANNEL_ICONS_DIRECTORY_PATH
from ...constants import DEFAULT_CHANNEL_ICON_FILE_PATH
from ...constants import VERSION
from ...constants import XML_TV_TEMPLATES
from ...enums import IPTVProxyEPGSource
from ...epg import IPTVProxyEPGChannel
from ...epg import IPTVProxyEPGProgram
from ...utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class SmoothStreamsEPG():
    __slots__ = []

    _channel_name_map = {}
    _do_use_smooth_streams_icons = False
    _groups = {'SmoothStreams'}
    _lock = RLock()
    _refresh_epg_timer = None
    _source = None

    @classmethod
    def _apply_optional_settings(cls, channel):
        channel.name = cls._channel_name_map.get(channel.name, channel.name)

        if not cls._do_use_smooth_streams_icons:
            for file_name in os.listdir(CHANNEL_ICONS_DIRECTORY_PATH):
                if re.search('\A{0}.png\Z|\A{0}_|_{0}_|_{0}.png'.format(channel.number), file_name):
                    channel_icon_file_name = file_name
                    channel_icon_file_path = os.path.join(CHANNEL_ICONS_DIRECTORY_PATH, channel_icon_file_name)

                    break
            else:
                channel_icon_file_name = '0.png'
                channel_icon_file_path = DEFAULT_CHANNEL_ICON_FILE_PATH

            channel.icon_url = '{0}{1}{2}'.format('http{0}://{1}:{2}/', channel_icon_file_name, '{3}')

            try:
                channel.icon_data_uri = 'data:image/png;base64,{0}'.format(
                    IPTVProxyUtility.read_png_file(channel_icon_file_path, in_base_64=True).decode())
            except OSError:
                pass

    @classmethod
    def _cancel_refresh_epg_timer(cls):
        if cls._refresh_epg_timer:
            cls._refresh_epg_timer.cancel()
            cls._refresh_epg_timer = None

    @classmethod
    def _convert_epg_to_xml_tv(cls, is_server_secure, authorization_required, client_ip_address, number_of_days):
        current_date_time_in_utc = datetime.now(pytz.utc)

        if cls._source == IPTVProxyEPGSource.FOG.value:
            tv_source_data_url = '{0}{1}'.format(SMOOTH_STREAMS_FOG_EPG_BASE_URL, SMOOTH_STREAMS_FOG_EPG_FILE_NAME)
        else:
            tv_source_data_url = '{0}{1}'.format(SMOOTH_STREAMS_EPG_BASE_URL, SMOOTH_STREAMS_EPG_FILE_NAME)

        client_ip_address_type = IPTVProxyUtility.determine_ip_address_type(client_ip_address)
        server_hostname = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
        server_port = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure else ''))

        xml_tv_templates = copy.deepcopy(XML_TV_TEMPLATES)

        for template_file_name in xml_tv_templates:
            xml_tv_templates[template_file_name] = IPTVProxyUtility.read_template(template_file_name)

        tv_xml_template_fields = {
            'tv_date': current_date_time_in_utc.strftime('%Y%m%d%H%M%S %z'),
            'tv_version': VERSION,
            'tv_source_data_url': tv_source_data_url
        }

        yield '{0}\n'.format(xml_tv_templates['tv_header.xml.st'].substitute(tv_xml_template_fields))

        cutoff_date_time_in_local = datetime.now(tzlocal.get_localzone()).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0) + timedelta(days=int(number_of_days) + 1)
        cutoff_date_time_in_utc = cutoff_date_time_in_local.astimezone(pytz.utc)

        db = SmoothStreamsDB()
        epg = db.retrieve(['epg'])

        for channel in epg.values():
            xmltv_elements = []

            channel_xml_template_fields = {
                'channel_id': channel.id,
                'channel_name': xml.sax.saxutils.escape(channel.name),
                'channel_icon': '        <icon src="{0}" />\n'.format(
                    xml.sax.saxutils.escape(
                        channel.icon_url.format('s' if is_server_secure else '',
                                                server_hostname,
                                                server_port,
                                                '?http_token={0}'.format(
                                                    IPTVProxyConfiguration.get_configuration_parameter(
                                                        'SERVER_PASSWORD')) if authorization_required else '')))
                if channel.icon_url else ''
            }

            xmltv_elements.append(
                '{0}\n'.format(xml_tv_templates['channel.xml.st'].substitute(channel_xml_template_fields)))

            for program in channel.programs:
                if cutoff_date_time_in_utc >= program.start_date_time_in_utc:
                    programme_xml_template_fields = {
                        'programme_channel': channel.id,
                        'programme_start': program.start_date_time_in_utc.strftime('%Y%m%d%H%M%S %z'),
                        'programme_stop': program.end_date_time_in_utc.strftime('%Y%m%d%H%M%S %z'),
                        'programme_title': xml.sax.saxutils.escape(program.title),
                        'programme_sub_title': '        <sub-title>{0}</sub-title>\n'.format(
                            xml.sax.saxutils.escape(program.sub_title)) if program.sub_title else '',
                        'programme_description': '        <desc>{0}</desc>\n'.format(
                            xml.sax.saxutils.escape(program.description)) if program.description else ''
                    }

                    xmltv_elements.append(
                        '{0}\n'.format(xml_tv_templates['programme.xml.st'].substitute(programme_xml_template_fields)))

            yield ''.join(xmltv_elements)

        db.close()

        yield '{0}\n'.format(xml_tv_templates['tv_footer.xml.st'].substitute())

    @classmethod
    def _generate_epg(cls):
        with cls._lock:
            db = SmoothStreamsDB()
            do_commit_transaction = False

            try:
                if IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') == \
                        IPTVProxyEPGSource.FOG.value:
                    cls._parse_fog_epg_xml(db)

                    cls._source = IPTVProxyEPGSource.FOG.value
                elif IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') == \
                        IPTVProxyEPGSource.SMOOTH_STREAMS.value:
                    cls._parse_smooth_streams_epg_json(db)

                    cls._source = IPTVProxyEPGSource.SMOOTH_STREAMS.value

                db.persist(['channel_name_map'], cls._channel_name_map)
                db.persist(['do_use_smooth_streams_icons'], cls._do_use_smooth_streams_icons)
                db.persist(['last_epg_refresh_date_time_in_local'], datetime.now(tzlocal.get_localzone()))
                db.persist(['source'], cls._source)

                do_commit_transaction = True
            finally:
                db.close(do_commit_transaction=do_commit_transaction)

            cls._initialize_refresh_epg_timer()

    @classmethod
    def _initialize_refresh_epg_timer(cls):
        current_date_time_in_local = datetime.now(tzlocal.get_localzone())

        do_generate_epg = False

        db = SmoothStreamsDB()

        if db.has_keys(['epg']) and db.retrieve(['epg']) and db.has_keys(['last_epg_refresh_date_time_in_local']):
            last_epg_refresh_date_time_in_local = db.retrieve(['last_epg_refresh_date_time_in_local'])

            if current_date_time_in_local >= \
                    (last_epg_refresh_date_time_in_local + timedelta(days=1)).replace(hour=4,
                                                                                      minute=0,
                                                                                      second=0,
                                                                                      microsecond=0):
                do_generate_epg = True
            else:
                refresh_epg_date_time_in_local = (current_date_time_in_local + timedelta(days=1)).replace(hour=4,
                                                                                                          minute=0,
                                                                                                          second=0,
                                                                                                          microsecond=0)

                cls._start_refresh_epg_timer(
                    (refresh_epg_date_time_in_local - current_date_time_in_local).total_seconds())
        else:
            do_generate_epg = True

        db.close()

        if do_generate_epg:
            cls._generate_epg()

    @classmethod
    def _parse_fog_epg_xml(cls, db):
        epg_xml_stream = cls._request_fog_epg_xml()

        source_channel_id_to_channel_number = {}
        tv_element = None
        tv_date = None

        for event, element in etree.iterparse(epg_xml_stream,
                                              events=('start', 'end'),
                                              tag=('channel', 'programme', 'tv')):
            if event == 'end':
                if element.tag == 'channel':
                    channel_icon_url = '',
                    channel_id = element.get('id')
                    channel_name = ''
                    channel_number = ''

                    for subElement in list(element):
                        if subElement.tag == 'display-name':
                            channel_name = xml.sax.saxutils.unescape(subElement.text).strip()
                        elif subElement.tag == 'icon':
                            channel_icon_url = subElement.get('src')
                            channel_number = int(re.search('.*/([0-9]+)\.png', channel_icon_url).group(1))

                            source_channel_id_to_channel_number[channel_id] = channel_number

                    channel = IPTVProxyEPGChannel('SmoothStreams',
                                                  channel_icon_url,
                                                  '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                          '{0} - (SmoothStreams)'.format(
                                                                              channel_number))),
                                                  channel_name,
                                                  channel_number)

                    cls._apply_optional_settings(channel)

                    db.persist(['epg', channel.number], channel)
                    db.savepoint(1)

                    element.clear()
                    tv_element.clear()
                elif element.tag == 'programme':
                    channel_id = element.get('channel')

                    channel_number = source_channel_id_to_channel_number[channel_id]

                    program = IPTVProxyEPGProgram()

                    program.end_date_time_in_utc = datetime.strptime(element.get('stop'), '%Y%m%d%H%M%S %z')
                    program.start_date_time_in_utc = datetime.strptime(element.get('start'), '%Y%m%d%H%M%S %z')

                    for subElement in list(element):
                        if subElement.tag == 'desc' and subElement.text:
                            program.description = xml.sax.saxutils.unescape(subElement.text)
                        if subElement.tag == 'sub-title' and subElement.text:
                            program.sub_title = xml.sax.saxutils.unescape(subElement.text)
                        elif subElement.tag == 'title' and subElement.text:
                            program.title = xml.sax.saxutils.unescape(subElement.text)

                    db.retrieve(['epg', channel_number]).add_program(program)
                    db.savepoint(1)

                    element.clear()
                    tv_element.clear()
            elif event == 'start':
                if element.tag == 'tv':
                    tv_element = element

                    tv_date = datetime.strptime(element.get('date'), '%Y%m%d%H%M%S %z').replace(tzinfo=pytz.utc)

        logger.debug('Processed Fog XML EPG\n'
                     'File name      => {0}\n'
                     'Generated on   => {1}'.format(SMOOTH_STREAMS_FOG_EPG_FILE_NAME,
                                                    tv_date))

    @classmethod
    def _parse_smooth_streams_epg_json(cls, db):
        epg_json_stream = cls._request_smooth_streams_epg_json()

        data_id = None
        events_id = None

        generated_on = None

        channel_icon_url = None
        channel_name = ''
        channel_number = None

        programs = PersistentList()

        program_description = ''
        program_runtime = None
        program_title = ''
        program_start_date_time_in_utc = None

        ijson_parser = ijson.parse(epg_json_stream)

        for (prefix, event, value) in ijson_parser:
            if (prefix, event) == ('generated_on', 'string'):
                generated_on = datetime.fromtimestamp(int(value), pytz.utc)
            elif (prefix, event) == ('data', 'map_key'):
                data_id = value
            elif (prefix, event) == ('data.{0}.events'.format(data_id), 'map_key'):
                events_id = value
            elif (prefix, event) == ('data.{0}.events.{1}'.format(data_id, events_id), 'end_map'):
                program_end_date_time_in_utc = program_start_date_time_in_utc + timedelta(minutes=program_runtime)

                programs.append(IPTVProxyEPGProgram(program_description,
                                                    program_end_date_time_in_utc,
                                                    program_start_date_time_in_utc,
                                                    '',
                                                    program_title))
                program_description = ''
                program_runtime = None
                program_title = ''
                program_start_date_time_in_utc = None
            elif (prefix, event) == ('data.{0}.events.{1}.description'.format(data_id, events_id), 'string'):
                program_description = xml.sax.saxutils.unescape(value)
            elif (prefix, event) == ('data.{0}.events.{1}.name'.format(data_id, events_id), 'string'):
                program_title = xml.sax.saxutils.unescape(value)
            elif (prefix, event) == ('data.{0}.events.{1}.runtime'.format(data_id, events_id), 'number'):
                program_runtime = value
            elif (prefix, event) == ('data.{0}.events.{1}.runtime'.format(data_id, events_id), 'string'):
                program_runtime = int(value)
            elif (prefix, event) == ('data.{0}.events.{1}.time'.format(data_id, events_id), 'string'):
                program_start_date_time_in_utc = datetime.fromtimestamp(int(value), pytz.utc)
            elif (prefix, event) == ('data.{0}.img'.format(data_id), 'string'):
                channel_icon_url = value
            elif (prefix, event) == ('data.{0}'.format(data_id), 'end_map'):
                channel = IPTVProxyEPGChannel('SmoothStreams',
                                              channel_icon_url,
                                              '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                      '{0} - (SmoothStreams)'.format(channel_number))),
                                              channel_name,
                                              channel_number)
                channel.programs = programs

                cls._apply_optional_settings(channel)

                db.persist(['epg', channel.number], channel)
                db.savepoint(1 + len(programs))

                channel_icon_url = None
                channel_name = None
                channel_number = None

                programs = PersistentList()
            elif (prefix, event) == ('data.{0}.name'.format(data_id), 'string'):
                channel_name = xml.sax.saxutils.unescape(value).strip()
            elif (prefix, event) == ('data.{0}.number'.format(data_id), 'string'):
                channel_number = int(value)

        logger.debug('Processed SmoothStreams JSON EPG\n'
                     'File name      => {0}\n'
                     'Generated on   => {1}'.format(SMOOTH_STREAMS_EPG_FILE_NAME,
                                                    generated_on))

    @classmethod
    def _refresh_epg(cls):
        logger.debug('SmoothStreams EPG refresh timer triggered')

        cls._generate_epg()

    @classmethod
    def _request_fog_epg_xml(cls):
        url = '{0}{1}'.format(SMOOTH_STREAMS_FOG_EPG_BASE_URL, SMOOTH_STREAMS_FOG_EPG_FILE_NAME)

        logger.debug('Downloading {0}\n'
                     'URL => {1}'.format(SMOOTH_STREAMS_FOG_EPG_FILE_NAME, url))

        session = requests.Session()
        response = IPTVProxyUtility.make_http_request(session.get, url, headers=session.headers, stream=True)

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            # noinspection PyUnresolvedReferences
            logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _request_smooth_streams_epg_json(cls):
        url = '{0}{1}'.format(SMOOTH_STREAMS_EPG_BASE_URL, SMOOTH_STREAMS_EPG_FILE_NAME)

        logger.debug('Downloading {0}\n'
                     'URL => {1}'.format(SMOOTH_STREAMS_EPG_FILE_NAME, url))

        session = requests.Session()
        response = IPTVProxyUtility.make_http_request(session.get, url, headers=session.headers, stream=True)

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            # noinspection PyUnresolvedReferences
            logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _start_refresh_epg_timer(cls, interval):
        if interval:
            logger.debug('Started SmoothStreams EPG refresh timer\n'
                         'Interval => {0} seconds'.format(interval))

        cls._refresh_epg_timer = Timer(interval, cls._refresh_epg)
        cls._refresh_epg_timer.daemon = True
        cls._refresh_epg_timer.start()

    @classmethod
    def generate_epg_xml_file(cls, is_server_secure, authorization_required, client_ip_address, number_of_days):
        return functools.partial(cls._convert_epg_to_xml_tv,
                                 is_server_secure,
                                 authorization_required,
                                 client_ip_address,
                                 number_of_days)

    @classmethod
    def get_channel_name(cls, channel_number):
        channel_number = int(channel_number)

        db = SmoothStreamsDB()

        try:
            channel_name = db.retrieve(['epg', channel_number]).name
        except KeyError:
            channel_name = 'Channel {0:02}'.format(channel_number)

        db.close()

        return channel_name

    @classmethod
    def get_channel_numbers_range(cls):
        db = SmoothStreamsDB()
        channel_numbers = db.retrieve(['epg']).keys()
        channel_numbers_range = (channel_numbers[0], channel_numbers[-1])
        db.close()

        return channel_numbers_range

    @classmethod
    def get_groups(cls):
        with cls._lock:
            return copy.copy(cls._groups)

    @classmethod
    def initialize(cls):
        cls._initialize_refresh_epg_timer()

        db = SmoothStreamsDB()

        try:
            if cls._channel_name_map != db.retrieve(['channel_name_map']) or \
                    cls._do_use_smooth_streams_icons != db.retrieve(['do_use_smooth_streams_icons']) or \
                    IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') != \
                    db.retrieve(['source']):
                cls._cancel_refresh_epg_timer()
                cls._generate_epg()

                logger.debug('Resetting EPG')
            else:
                cls._source = db.retrieve(['source'])
        except KeyError:
            pass

        db.close()

    @classmethod
    def is_channel_number_in_epg(cls, channel_number):
        db = SmoothStreamsDB()
        channel_numbers = db.retrieve(['epg']).keys()
        is_channel_number_in_epg = int(channel_number) in channel_numbers
        db.close()

        return is_channel_number_in_epg

    @classmethod
    def reset_epg(cls):
        with cls._lock:
            cls._cancel_refresh_epg_timer()
            cls._start_refresh_epg_timer(0)

    @classmethod
    def set_channel_name_map(cls, channel_name_map):
        cls._channel_name_map = channel_name_map

    @classmethod
    def set_do_use_smooth_streams_icons(cls, do_use_smooth_streams_icons):
        cls._do_use_smooth_streams_icons = do_use_smooth_streams_icons
