import copy
import functools
import hashlib
import json
import logging
import os
import re
import uuid
import xml.sax.saxutils
from datetime import datetime
from datetime import timedelta
from gzip import GzipFile
from threading import RLock
from threading import Timer

import ijson
import pytz
import requests
import tzlocal
from lxml import etree

from .constants import VADER_STREAMS_BASE_URL
from .constants import VADER_STREAMS_CATEGORIES_JSON_FILE_NAME
from .constants import VADER_STREAMS_CATEGORIES_PATH
from .constants import VADER_STREAMS_CHANNELS_JSON_FILE_NAME
from .constants import VADER_STREAMS_CHANNELS_PATH
from .constants import VADER_STREAMS_EPG_BASE_URL
from .constants import VADER_STREAMS_MATCHCENTER_SCHEDULE_JSON_FILE_NAME
from .constants import VADER_STREAMS_MATCHCENTER_SCHEDULE_PATH
from .constants import VADER_STREAMS_XML_EPG_FILE_NAME
from .db import VaderStreamsSQL
from ...configuration import IPTVProxyConfiguration
from ...constants import CHANNEL_ICONS_DIRECTORY_PATH
from ...constants import DEFAULT_CHANNEL_ICON_FILE_PATH
from ...constants import VERSION
from ...constants import XML_TV_TEMPLATES
from ...db import IPTVProxyDatabase
from ...epg import IPTVProxyEPGChannel
from ...epg import IPTVProxyEPGProgram
from ...security import IPTVProxySecurityManager
from ...utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class VaderStreamsEPG(object):
    __slots__ = []

    _channel_name_map = {}
    _do_use_vader_streams_icons = False
    _groups = None
    _lock = RLock()
    _refresh_epg_timer = None

    @classmethod
    def _apply_optional_settings(cls, channel):
        channel.name = cls._channel_name_map.get(channel.name, channel.name)

        if not cls._do_use_vader_streams_icons:
            for file_name in os.listdir(CHANNEL_ICONS_DIRECTORY_PATH):
                if re.search(r'\A{0}.png\Z|\A{0}_|_{0}_|_{0}.png'.format(channel.number), file_name):
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
            'tv_source_data_url': '{0}{1}'.format(VADER_STREAMS_EPG_BASE_URL, VADER_STREAMS_XML_EPG_FILE_NAME)
        }

        yield '{0}\n'.format(xml_tv_templates['tv_header.xml.st'].substitute(tv_xml_template_fields))

        cutoff_date_time_in_local = datetime.now(tzlocal.get_localzone()).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0) + timedelta(days=int(number_of_days) + 1)
        cutoff_date_time_in_utc = cutoff_date_time_in_local.astimezone(pytz.utc)

        db = IPTVProxyDatabase()
        channel_records = VaderStreamsSQL.query_channels(db)
        db.close_connection()

        for channel_record in channel_records:
            xmltv_elements = []

            channel_xml_template_fields = {
                'channel_id': channel_record['id'],
                'channel_name': xml.sax.saxutils.escape(channel_record['name']),
                'channel_icon': '        <icon src="{0}" />\n'.format(
                    xml.sax.saxutils.escape(
                        channel_record['icon_url'].format('s'
                                                          if is_server_secure
                                                          else '',
                                                          server_hostname,
                                                          server_port,
                                                          '?http_token={0}'.format(
                                                              IPTVProxyConfiguration.get_configuration_parameter(
                                                                  'SERVER_PASSWORD'))
                                                          if authorization_required
                                                          else '')))
                if channel_record['icon_url']
                else ''
            }

            xmltv_elements.append(
                '{0}\n'.format(xml_tv_templates['channel.xml.st'].substitute(channel_xml_template_fields)))

            db = IPTVProxyDatabase()
            program_records = VaderStreamsSQL.query_programs_by_channel_id(db, channel_record['id'])
            db.close_connection()

            for program_record in program_records:
                if cutoff_date_time_in_utc >= datetime.strptime(program_record['start_date_time_in_utc'],
                                                                '%Y-%m-%d %H:%M:%S%z'):
                    programme_xml_template_fields = {
                        'programme_channel': channel_record['id'],
                        'programme_start': datetime.strptime(program_record['start_date_time_in_utc'],
                                                             '%Y-%m-%d %H:%M:%S%z').strftime('%Y%m%d%H%M%S %z'),
                        'programme_stop': datetime.strptime(program_record['end_date_time_in_utc'],
                                                            '%Y-%m-%d %H:%M:%S%z').strftime('%Y%m%d%H%M%S %z'),
                        'programme_title': xml.sax.saxutils.escape(program_record['title']),
                        'programme_sub_title': '        <sub-title>{0}</sub-title>\n'.format(
                            xml.sax.saxutils.escape(program_record['sub_title']))
                        if program_record['sub_title']
                        else '',
                        'programme_description': '        <desc>{0}</desc>\n'.format(
                            xml.sax.saxutils.escape(program_record['description']))
                        if program_record['description']
                        else ''
                    }

                    xmltv_elements.append(
                        '{0}\n'.format(xml_tv_templates['programme.xml.st'].substitute(programme_xml_template_fields)))

            yield ''.join(xmltv_elements)

        yield '{0}\n'.format(xml_tv_templates['tv_footer.xml.st'].substitute())

    @classmethod
    def _generate_epg(cls):
        with cls._lock:
            cls._groups = set()

            db = IPTVProxyDatabase()
            VaderStreamsSQL.delete_programs_temp(db)
            VaderStreamsSQL.delete_channels_temp(db)
            db.commit()
            db.close_connection()

            try:
                source_channel_id_to_channel_number = {}

                cls._parse_epg_json(source_channel_id_to_channel_number)
                cls._parse_epg_xml(source_channel_id_to_channel_number)

                db = IPTVProxyDatabase()
                VaderStreamsSQL.delete_programs(db)
                VaderStreamsSQL.delete_channels(db)

                VaderStreamsSQL.insert_select_channels(db)
                VaderStreamsSQL.insert_select_programs(db)

                VaderStreamsSQL.delete_programs_temp(db)
                VaderStreamsSQL.delete_channels_temp(db)

                VaderStreamsSQL.insert_setting(db, 'do_use_icons', int(cls._do_use_vader_streams_icons))
                VaderStreamsSQL.insert_setting(db,
                                               'channel_name_map_md5',
                                               hashlib.md5(json.dumps(cls._channel_name_map,
                                                                      sort_keys=True).encode()).hexdigest())
                VaderStreamsSQL.insert_setting(db, 'last_epg_refresh_date_time_in_utc',
                                               datetime.strftime(datetime.now(pytz.utc), '%Y-%m-%d %H:%M:%S%z'))
                db.commit()
                db.close_connection()
            finally:
                cls._initialize_refresh_epg_timer()

    @classmethod
    def _initialize_refresh_epg_timer(cls):
        current_date_time_in_utc = datetime.now(pytz.utc)

        do_generate_epg = False

        db = IPTVProxyDatabase()
        vader_streams_last_epg_refresh_date_time_in_utc_setting_records = VaderStreamsSQL.query_setting(
            db,
            'last_epg_refresh_date_time_in_utc')
        db.close_connection()

        if vader_streams_last_epg_refresh_date_time_in_utc_setting_records:
            last_epg_refresh_date_time_in_utc = datetime.strptime(
                vader_streams_last_epg_refresh_date_time_in_utc_setting_records[0]['value'], '%Y-%m-%d %H:%M:%S%z')

            if current_date_time_in_utc >= \
                    (last_epg_refresh_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()) + timedelta(days=1)).replace(hour=4,
                                                                              minute=0,
                                                                              second=0,
                                                                              microsecond=0):
                do_generate_epg = True
            else:
                refresh_epg_date_time_in_utc = ((current_date_time_in_utc.astimezone(
                    tzlocal.get_localzone()) + timedelta(days=1)).replace(hour=4,
                                                                          minute=0,
                                                                          second=0,
                                                                          microsecond=0)).astimezone(pytz.utc)

                cls._start_refresh_epg_timer((refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds())
        else:
            do_generate_epg = True

        if do_generate_epg:
            cls._generate_epg()

    @classmethod
    def _parse_categories_json(cls):
        categories_map = {}

        categories_json_stream = cls._request_epg_json(VADER_STREAMS_CATEGORIES_PATH,
                                                       VADER_STREAMS_CATEGORIES_JSON_FILE_NAME,
                                                       {})

        logger.debug('Processing VaderStreams JSON categories\n'
                     'File name => {0}'.format(VADER_STREAMS_CATEGORIES_JSON_FILE_NAME))

        ijson_parser = ijson.parse(categories_json_stream)

        for (prefix, event, value) in ijson_parser:
            if event == 'string':
                categories_map[int(prefix)] = value

        logger.debug('Processed VaderStreams JSON categories\n'
                     'File name => {0}'.format(VADER_STREAMS_CATEGORIES_JSON_FILE_NAME))

        return categories_map

    @classmethod
    def _parse_channels_json(cls, categories_map, source_channel_id_to_channel_number):
        for category_id in categories_map:
            channels_json_stream = cls._request_epg_json(VADER_STREAMS_CHANNELS_PATH,
                                                         VADER_STREAMS_CHANNELS_JSON_FILE_NAME,
                                                         dict(category_id=category_id))

            logger.debug('Processing VaderStreams JSON channels\n'
                         'File name => {0}'.format(VADER_STREAMS_CHANNELS_JSON_FILE_NAME))

            channel_category_id = None
            channel_icon_url = None
            channel_id = None
            channel_name = ''
            channel_number = None

            programs = []

            db = IPTVProxyDatabase()

            ijson_parser = ijson.parse(channels_json_stream)

            for (prefix, event, value) in ijson_parser:
                if (prefix, event) == ('item', 'end_map'):
                    try:
                        if 'sport' in channel_name.lower():
                            channel_group = 'VaderStreams - Sports'
                        elif 'movie' in channel_name.lower():
                            channel_group = 'VaderStreams - Premium Movies'
                        else:
                            channel_group = 'VaderStreams - {0}'.format(categories_map[channel_category_id])
                        cls._groups.add(channel_group)

                        channel = IPTVProxyEPGChannel(channel_group,
                                                      channel_icon_url,
                                                      '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                              '{0} - (VaderStreams)'.format(
                                                                                  channel_number))),
                                                      channel_name,
                                                      channel_number)
                        channel.programs = programs

                        cls._apply_optional_settings(channel)

                        VaderStreamsSQL.insert_channel(db, channel)

                        if channel_id in source_channel_id_to_channel_number:
                            source_channel_id_to_channel_number[channel_id].append(channel.number)
                        else:
                            source_channel_id_to_channel_number[channel_id] = [channel.number]
                    except KeyError:
                        pass
                    finally:
                        channel_category_id = None
                        channel_icon_url = None
                        channel_id = None
                        channel_name = None
                        channel_number = None

                        programs = []
                elif (prefix, event) == ('item.id', 'number'):
                    channel_number = value
                elif (prefix, event) == ('item.stream_icon', 'string'):
                    channel_icon_url = xml.sax.saxutils.unescape(value)
                elif (prefix, event) == ('item.channel_id', 'string'):
                    channel_id = xml.sax.saxutils.unescape(value)
                elif (prefix, event) == ('item.stream_display_name', 'string'):
                    channel_name = xml.sax.saxutils.unescape(value)

                elif (prefix, event) == ('item.category_id', 'number'):
                    channel_category_id = value

            db.commit()
            db.close_connection()

            logger.debug('Processed VaderStreams JSON channels\n'
                         'File name => {0}'.format(VADER_STREAMS_CHANNELS_JSON_FILE_NAME))

    @classmethod
    def _parse_epg_json(cls, source_channel_id_to_channel_number):
        categories_map = cls._parse_categories_json()
        cls._parse_channels_json(categories_map, source_channel_id_to_channel_number)
        cls._parse_matchcenter_schedule_json()

        logger.debug('Processed VaderStreams JSON EPG\n'
                     'File names => {0}, {1}, & {2}'.format(VADER_STREAMS_CATEGORIES_JSON_FILE_NAME,
                                                            VADER_STREAMS_CHANNELS_JSON_FILE_NAME,
                                                            VADER_STREAMS_MATCHCENTER_SCHEDULE_JSON_FILE_NAME))

    @classmethod
    def _parse_epg_xml(cls, source_channel_id_to_channel_number):
        epg_xml_stream = cls._request_epg_xml()

        logger.debug('Processing VaderStreams XML EPG\n'
                     'File name => {0}'.format(VADER_STREAMS_XML_EPG_FILE_NAME))

        with GzipFile(fileobj=epg_xml_stream) as input_file:
            tv_element = None

            db = IPTVProxyDatabase()

            for (event, element) in etree.iterparse(input_file,
                                                    events=('start', 'end'),
                                                    recover=True,
                                                    tag=('channel', 'programme', 'tv')):
                if event == 'end':
                    if element.tag == 'channel':
                        element.clear()
                        tv_element.clear()
                    elif element.tag == 'programme':
                        channel_id = element.get('channel')

                        try:
                            channel_numbers = source_channel_id_to_channel_number[channel_id]

                            for channel_number in channel_numbers:
                                program = IPTVProxyEPGProgram()

                                program.end_date_time_in_utc = datetime.strptime(element.get('stop'),
                                                                                 '%Y%m%d%H%M%S %z')
                                program.start_date_time_in_utc = datetime.strptime(element.get('start'),
                                                                                   '%Y%m%d%H%M%S %z')

                                for subElement in list(element):
                                    if subElement.tag == 'desc' and subElement.text:
                                        program.description = xml.sax.saxutils.unescape(subElement.text)
                                    elif subElement.tag == 'sub-title' and subElement.text:
                                        program.sub_title = xml.sax.saxutils.unescape(subElement.text)
                                    elif subElement.tag == 'title' and subElement.text:
                                        program.title = xml.sax.saxutils.unescape(subElement.text)

                                VaderStreamsSQL.insert_program(db,
                                                               '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                                       '{0} - (VaderStreams)'.format(
                                                                                           channel_number))),
                                                               program)
                        except KeyError:
                            pass
                        finally:
                            element.clear()
                            tv_element.clear()
                elif event == 'start':
                    if element.tag == 'tv':
                        tv_element = element

            db.commit()
            db.close_connection()

            logger.debug('Processed VaderStreams XML EPG\n'
                         'File name => {0}'.format(VADER_STREAMS_XML_EPG_FILE_NAME))

    @classmethod
    def _parse_matchcenter_schedule_json(cls):
        current_date_time_in_utc = datetime.now(pytz.utc)

        matchcenter_schedule_json_stream = cls._request_epg_json(
            VADER_STREAMS_MATCHCENTER_SCHEDULE_PATH,
            VADER_STREAMS_MATCHCENTER_SCHEDULE_JSON_FILE_NAME,
            dict(start=int(current_date_time_in_utc.timestamp()),
                 end=int(current_date_time_in_utc.timestamp()) + 172800))

        logger.debug('Processing VaderStreams JSON matchcenter schedule\n'
                     'File name => {0}'.format(VADER_STREAMS_MATCHCENTER_SCHEDULE_JSON_FILE_NAME))

        channel_numbers = []
        program = IPTVProxyEPGProgram()

        db = IPTVProxyDatabase()

        ijson_parser = ijson.parse(matchcenter_schedule_json_stream)

        for (prefix, event, value) in ijson_parser:
            if (prefix, event) == ('item', 'start_map'):
                program = IPTVProxyEPGProgram()
            elif (prefix, event) == ('item.streams', 'start_array'):
                channel_numbers = []
            elif (prefix, event) == ('item.streams.item.id', 'number'):
                channel_numbers.append(value)
            elif (prefix, event) == ('item.description', 'string'):
                program.description = xml.sax.saxutils.unescape(value)
            elif (prefix, event) == ('item.title', 'string'):
                program.title = xml.sax.saxutils.unescape(value)
            elif (prefix, event) == ('item.startTime', 'string'):
                program.start_date_time_in_utc = datetime.strptime(value[:-3] + value[-2:], '%Y-%m-%dT%H:%M:%S%z')
            elif (prefix, event) == ('item.endTime', 'string'):
                program.end_date_time_in_utc = datetime.strptime(value[:-3] + value[-2:], '%Y-%m-%dT%H:%M:%S%z')
            elif (prefix, event) == ('item', 'end_map'):
                for channel_number in channel_numbers:
                    VaderStreamsSQL.insert_program(db, '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                               '{0} - (VaderStreams)'.format(
                                                                                   channel_number))),
                                                   program)

        db.commit()
        db.close_connection()

        logger.debug('Processed VaderStreams JSON matchcenter schedule\n'
                     'File name => {0}'.format(VADER_STREAMS_MATCHCENTER_SCHEDULE_JSON_FILE_NAME))

    @classmethod
    def _refresh_epg(cls):
        logger.debug('VaderStreams EPG refresh timer triggered')

        cls._generate_epg()

    @classmethod
    def _request_epg_json(cls, epg_json_path, epg_json_file_name, request_parameters):
        username = IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_USERNAME')
        password = IPTVProxySecurityManager.decrypt_password(
            IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_PASSWORD')).decode()

        url = '{0}{1}'.format(VADER_STREAMS_BASE_URL, epg_json_path)

        logger.debug(
            'Downloading {0}\n'
            'URL => {1}\n'
            '  Parameters\n'
            '    username => {2}\n'
            '    password => {3}{4}'.format(epg_json_file_name,
                                            url,
                                            username,
                                            '\u2022' * len(password),
                                            '' if request_parameters is None or 'category_id' not in request_parameters
                                            else '\n    category => {0}'.format(request_parameters['category_id'])))

        session = requests.Session()
        response = IPTVProxyUtility.make_http_request(session.get,
                                                      url,
                                                      params={
                                                          'username': username,
                                                          'password': password,
                                                          **request_parameters
                                                      },
                                                      headers=session.headers,
                                                      cookies=session.cookies.get_dict(),
                                                      stream=True)

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            # noinspection PyUnresolvedReferences
            logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _request_epg_xml(cls):
        url = '{0}{1}'.format(VADER_STREAMS_EPG_BASE_URL, VADER_STREAMS_XML_EPG_FILE_NAME)

        logger.debug('Downloading {0}\n'
                     'URL => {1}'.format(VADER_STREAMS_XML_EPG_FILE_NAME, url))

        session = requests.Session()
        response = IPTVProxyUtility.make_http_request(session.get, url, headers=session.headers, stream=True)

        if response.status_code == requests.codes.OK:
            # noinspection PyUnresolvedReferences
            logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _start_refresh_epg_timer(cls, interval):
        if interval:
            logger.debug('Started VaderStreams EPG refresh timer\n'
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
        db = IPTVProxyDatabase()
        channel_name_records = VaderStreamsSQL.query_channel_by_channel_number(db, channel_number)
        db.close_connection()

        if channel_name_records:
            channel_name = channel_name_records[0]['name']
        else:
            channel_name = 'Channel {0:02}'.format(int(channel_number))

        return channel_name

    @classmethod
    def get_channel_numbers_range(cls):
        db = IPTVProxyDatabase()
        minimum_maximum_channel_number_records = VaderStreamsSQL.query_minimum_maximum_channel_numbers(db)
        db.close_connection()

        return (int(minimum_maximum_channel_number_records[0][0]), int(minimum_maximum_channel_number_records[0][1]))

    @classmethod
    def get_groups(cls):
        with cls._lock:
            return copy.copy(cls._groups)

    @classmethod
    def initialize(cls):
        cls._initialize_refresh_epg_timer()

        db = IPTVProxyDatabase()
        vader_streams_do_use_icons_setting_records = VaderStreamsSQL.query_setting(db, 'do_use_icons')
        vader_streams_channel_name_map_md5_setting_records = VaderStreamsSQL.query_setting(db, 'channel_name_map_md5')
        db.close_connection()

        if not vader_streams_do_use_icons_setting_records or not \
                vader_streams_channel_name_map_md5_setting_records or \
                hashlib.md5(json.dumps(cls._channel_name_map, sort_keys=True).encode()).hexdigest() != \
                vader_streams_channel_name_map_md5_setting_records[0]['value'] or \
                cls._do_use_vader_streams_icons != \
                bool(int(vader_streams_do_use_icons_setting_records[0]['value'])):
            cls._cancel_refresh_epg_timer()
            cls._generate_epg()

            logger.debug('Resetting EPG')
        else:
            db = IPTVProxyDatabase()
            group_records = VaderStreamsSQL.query_groups(db)
            db.close_connection()

            cls._groups = {group_record['group'] for group_record in group_records}

    @classmethod
    def is_channel_number_in_epg(cls, channel_number):
        db = IPTVProxyDatabase()
        channel_name_records = VaderStreamsSQL.query_channel_by_channel_number(db, channel_number)
        db.close_connection()

        if channel_name_records:
            return True
        else:
            return False

    @classmethod
    def reset_epg(cls):
        with cls._lock:
            cls._cancel_refresh_epg_timer()
            cls._start_refresh_epg_timer(0)

    @classmethod
    def set_channel_name_map(cls, channel_name_map):
        cls._channel_name_map = channel_name_map

    @classmethod
    def set_do_use_vader_streams_icons(cls, do_use_vader_streams_icons):
        cls._do_use_vader_streams_icons = do_use_vader_streams_icons
