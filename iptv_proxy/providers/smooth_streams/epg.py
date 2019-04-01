import copy
import functools
import hashlib
import html
import json
import logging
import os
import re
import sys
import traceback
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

from .constants import SMOOTH_STREAMS_EPG_BASE_URL
from .constants import SMOOTH_STREAMS_EPG_FILE_NAME
from .constants import SMOOTH_STREAMS_FOG_CHANNELS_JSON_FILE_NAME
from .constants import SMOOTH_STREAMS_FOG_EPG_BASE_URL
from .constants import SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME
from .db import SmoothStreamsSQL
from .enums import SmoothStreamsEPGSource
from ...configuration import IPTVProxyConfiguration
from ...constants import CHANNEL_ICONS_DIRECTORY_PATH
from ...constants import DEFAULT_CHANNEL_ICON_FILE_PATH
from ...constants import VERSION
from ...constants import XML_TV_TEMPLATES
from ...db import IPTVProxyDatabase
from ...epg import IPTVProxyEPGChannel
from ...epg import IPTVProxyEPGProgram
from ...utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class SmoothStreamsEPG(object):
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

        if cls._source == SmoothStreamsEPGSource.FOG.value:
            tv_source_data_url = '{0}{1}'.format(SMOOTH_STREAMS_FOG_EPG_BASE_URL, SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME)
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

        db = IPTVProxyDatabase()
        channel_records = SmoothStreamsSQL.query_channels(db)
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
            program_records = SmoothStreamsSQL.query_programs_by_channel_id(db, channel_record['id'])
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
                        else '',
                        'programme_category': '        <category>{0}</category>\n'.format(
                            xml.sax.saxutils.escape(program_record['category']))
                        if program_record['category']
                        else ''
                    }

                    xmltv_elements.append(
                        '{0}\n'.format(xml_tv_templates['programme.xml.st'].substitute(programme_xml_template_fields)))

            yield ''.join(xmltv_elements)

        yield '{0}\n'.format(xml_tv_templates['tv_footer.xml.st'].substitute())

    @classmethod
    def _generate_epg(cls):
        with cls._lock:
            was_exception_raised = False

            db = IPTVProxyDatabase()
            SmoothStreamsSQL.delete_programs_temp(db)
            SmoothStreamsSQL.delete_channels_temp(db)
            db.commit()
            db.close_connection()

            # noinspection PyBroadException
            try:
                if IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') == \
                        SmoothStreamsEPGSource.FOG.value:
                    cls._parse_fog_channels_json()
                    cls._parse_fog_epg_xml()

                    cls._source = SmoothStreamsEPGSource.FOG.value
                elif IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') == \
                        SmoothStreamsEPGSource.OTHER.value:
                    cls._parse_other_epg_xml()

                    cls._source = SmoothStreamsEPGSource.OTHER.value
                elif IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') == \
                        SmoothStreamsEPGSource.SMOOTH_STREAMS.value:
                    cls._parse_smooth_streams_epg_json()

                    cls._source = SmoothStreamsEPGSource.SMOOTH_STREAMS.value

                db = IPTVProxyDatabase()
                SmoothStreamsSQL.delete_programs(db)
                SmoothStreamsSQL.delete_channels(db)

                SmoothStreamsSQL.insert_select_channels(db)
                SmoothStreamsSQL.insert_select_programs(db)

                SmoothStreamsSQL.delete_programs_temp(db)
                SmoothStreamsSQL.delete_channels_temp(db)

                SmoothStreamsSQL.insert_setting(db, 'do_use_icons', int(cls._do_use_smooth_streams_icons))
                SmoothStreamsSQL.insert_setting(db,
                                                'channel_name_map_md5',
                                                hashlib.md5(json.dumps(cls._channel_name_map,
                                                                       sort_keys=True).encode()).hexdigest())
                SmoothStreamsSQL.insert_setting(db,
                                                'last_epg_refresh_date_time_in_utc',
                                                datetime.strftime(datetime.now(pytz.utc), '%Y-%m-%d %H:%M:%S%z'))
                SmoothStreamsSQL.insert_setting(db, 'epg_source', cls._source)
                if cls._source == SmoothStreamsEPGSource.OTHER.value:
                    SmoothStreamsSQL.insert_setting(db, 'epg_url', IPTVProxyConfiguration.get_configuration_parameter(
                        'SMOOTH_STREAMS_EPG_URL'))
                else:
                    SmoothStreamsSQL.delete_setting(db, 'epg_url')
                db.commit()
                db.close_connection()
            except Exception:
                was_exception_raised = True

                db = IPTVProxyDatabase()
                SmoothStreamsSQL.delete_programs_temp(db)
                SmoothStreamsSQL.delete_channels_temp(db)
                db.commit()
                db.close_connection()

                raise
            finally:
                cls._initialize_refresh_epg_timer(do_set_timer_for_retry=was_exception_raised)

    @classmethod
    def _initialize_refresh_epg_timer(cls, do_set_timer_for_retry=False):
        current_date_time_in_utc = datetime.now(pytz.utc)

        if do_set_timer_for_retry:
            refresh_epg_date_time_in_utc = (current_date_time_in_utc.astimezone(
                tzlocal.get_localzone()).replace(minute=0,
                                                 second=0,
                                                 microsecond=0) + timedelta(hours=1)).astimezone(pytz.utc)

            cls._start_refresh_epg_timer((refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds())
        else:
            do_generate_epg = False

            db = IPTVProxyDatabase()
            smooth_streams_last_epg_refresh_date_time_in_utc_setting_records = SmoothStreamsSQL.query_setting(
                db,
                'last_epg_refresh_date_time_in_utc')
            db.close_connection()

            if smooth_streams_last_epg_refresh_date_time_in_utc_setting_records:
                last_epg_refresh_date_time_in_utc = datetime.strptime(
                    smooth_streams_last_epg_refresh_date_time_in_utc_setting_records[0]['value'], '%Y-%m-%d %H:%M:%S%z')

                if current_date_time_in_utc >= last_epg_refresh_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()).replace(hour=4,
                                                         minute=0,
                                                         second=0,
                                                         microsecond=0) + timedelta(days=1):
                    do_generate_epg = True
                else:
                    refresh_epg_date_time_in_utc = (current_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()).replace(hour=4,
                                                         minute=0,
                                                         second=0,
                                                         microsecond=0) + timedelta(days=1)).astimezone(pytz.utc)

                    cls._start_refresh_epg_timer(
                        (refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds())
            else:
                do_generate_epg = True

            if do_generate_epg:
                cls._generate_epg()

    @classmethod
    def _parse_fog_channels_json(cls):
        epg_json_stream = cls._request_fog_channels_json()

        logger.debug('Processing Fog JSON channels\n'
                     'File name => {0}'.format(SMOOTH_STREAMS_FOG_CHANNELS_JSON_FILE_NAME))

        key = None
        channel_icon_url = None
        channel_name = ''
        channel_number = None

        db = IPTVProxyDatabase()

        # noinspection PyBroadException
        try:
            ijson_parser = ijson.parse(epg_json_stream)

            for (prefix, event, value) in ijson_parser:
                if prefix.isdigit() and (event, value) == ('start_map', None):
                    key = prefix
                    channel_icon_url = None
                    channel_name = ''
                    channel_number = None
                elif (prefix, event) == ('{0}.channum'.format(key), 'string'):
                    channel_number = int(value)
                elif (prefix, event) == ('{0}.channame'.format(key), 'string'):
                    channel_name = html.unescape(value).strip()
                elif (prefix, event) == ('{0}.icon'.format(key), 'string'):
                    channel_icon_url = value
                elif (prefix, event) == (key, 'end_map'):
                    channel = IPTVProxyEPGChannel('SmoothStreams',
                                                  channel_icon_url,
                                                  '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                          '{0} - (SmoothStreams)'.format(
                                                                              channel_number))),
                                                  channel_name,
                                                  channel_number)

                    cls._apply_optional_settings(channel)

                    SmoothStreamsSQL.insert_channel(db, channel)

            db.commit()

            logger.debug('Processed Fog JSON channels\n'
                         'File name => {0}'.format(SMOOTH_STREAMS_FOG_CHANNELS_JSON_FILE_NAME))
        except Exception:
            db.rollback()

            logger.debug('Failed to process Fog JSON channels\n'
                         'File name => {0}'.format(SMOOTH_STREAMS_FOG_CHANNELS_JSON_FILE_NAME))

            raise
        finally:
            db.close_connection()

    @classmethod
    def _parse_fog_epg_xml(cls):
        epg_xml_stream = cls._request_fog_epg_xml()

        logger.debug('Processing Fog XML EPG\n'
                     'File name => {0}'.format(SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME))

        source_channel_id_to_channel_number = {}
        tv_element = None
        tv_date = None

        db = IPTVProxyDatabase()

        # noinspection PyBroadException
        try:
            for event, element in etree.iterparse(epg_xml_stream,
                                                  events=('start', 'end'),
                                                  tag=('channel', 'programme', 'tv')):
                if event == 'end':
                    if element.tag == 'channel':
                        channel_id = element.get('id')

                        for sub_element in list(element):
                            if sub_element.tag == 'icon':
                                channel_number = int(re.search(r'.*/([0-9]+)\.png', sub_element.get('src')).group(1))

                                source_channel_id_to_channel_number[channel_id] = channel_number

                        element.clear()
                        tv_element.clear()
                    elif element.tag == 'programme':
                        channel_id = element.get('channel')

                        program = IPTVProxyEPGProgram()

                        program.end_date_time_in_utc = datetime.strptime(element.get('stop'), '%Y%m%d%H%M%S %z')
                        program.start_date_time_in_utc = datetime.strptime(element.get('start'), '%Y%m%d%H%M%S %z')

                        for sub_element in list(element):
                            if sub_element.tag == 'category' and sub_element.text and not program.category:
                                program.category = sub_element.text
                            elif sub_element.tag == 'desc' and sub_element.text:
                                program.description = sub_element.text
                            if sub_element.tag == 'sub-title' and sub_element.text:
                                program.sub_title = sub_element.text
                            elif sub_element.tag == 'title' and sub_element.text:
                                program.title = sub_element.text

                        SmoothStreamsSQL.insert_program(db,
                                                        '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                                '{0} - (SmoothStreams)'.format(
                                                                                    source_channel_id_to_channel_number[
                                                                                        channel_id]))),
                                                        program)

                        element.clear()
                        tv_element.clear()
                elif event == 'start':
                    if element.tag == 'tv':
                        tv_element = element

                        tv_date = datetime.strptime(element.get('date'), '%Y%m%d%H%M%S %z').replace(tzinfo=pytz.utc)

            db.commit()

            logger.debug('Processed Fog XML EPG\n'
                         'File name    => {0}\n'
                         'Generated on => {1}'.format(SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME,
                                                      tv_date))
        except Exception:
            db.rollback()

            logger.debug('Failed to process Fog XML EPG\n'
                         'File name    => {0}'.format(SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME))

            raise
        finally:
            db.close_connection()

    @classmethod
    def _parse_other_epg_xml(cls):
        epg_xml_stream = cls._request_other_epg_xml()

        logger.debug('Processing external XML EPG')

        source_channel_id_to_channel_number = {}
        tv_element = None
        channel_number = 0

        db = IPTVProxyDatabase()

        # noinspection PyBroadException
        try:
            for event, element in etree.iterparse(epg_xml_stream,
                                                  events=('start', 'end'),
                                                  tag=('channel', 'programme', 'tv')):
                if event == 'end':
                    if element.tag == 'channel':
                        channel_icon_url = None
                        channel_id = element.get('id')
                        channel_name = ''
                        channel_number += 1

                        source_channel_id_to_channel_number[channel_id] = channel_number

                        for sub_element in list(element):
                            if sub_element.tag == 'display-name':
                                channel_name = sub_element.text
                            elif sub_element.tag == 'icon':
                                channel_icon_url = sub_element.get('src')

                        channel = IPTVProxyEPGChannel('SmoothStreams',
                                                      channel_icon_url,
                                                      '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                              '{0} - (SmoothStreams)'.format(
                                                                                  channel_number))),
                                                      channel_name,
                                                      channel_number)

                        cls._apply_optional_settings(channel)

                        SmoothStreamsSQL.insert_channel(db, channel)

                        element.clear()
                        tv_element.clear()
                    elif element.tag == 'programme':
                        channel_id = element.get('channel')

                        program = IPTVProxyEPGProgram()

                        program.end_date_time_in_utc = datetime.strptime(element.get('stop'), '%Y%m%d%H%M%S %z')
                        program.start_date_time_in_utc = datetime.strptime(element.get('start'), '%Y%m%d%H%M%S %z')

                        for sub_element in list(element):
                            if sub_element.tag == 'category' and sub_element.text and not program.category:
                                program.category = sub_element.text
                            elif sub_element.tag == 'desc' and sub_element.text:
                                program.description = sub_element.text
                            if sub_element.tag == 'sub-title' and sub_element.text:
                                program.sub_title = sub_element.text
                            elif sub_element.tag == 'title' and sub_element.text:
                                program.title = sub_element.text

                        SmoothStreamsSQL.insert_program(db,
                                                        '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                                                '{0} - (SmoothStreams)'.format(
                                                                                    source_channel_id_to_channel_number[
                                                                                        channel_id]))),
                                                        program)

                        element.clear()
                        tv_element.clear()
                elif event == 'start':
                    if element.tag == 'tv':
                        tv_element = element

            db.commit()

            logger.debug('Processed external XML EPG')
        except Exception:
            db.rollback()

            logger.debug('Failed to process external XML EPG')

            raise
        finally:
            db.close_connection()

    @classmethod
    def _parse_smooth_streams_epg_json(cls):
        epg_json_stream = cls._request_smooth_streams_epg_json()

        logger.debug('Processing SmoothStreams JSON EPG\n'
                     'File name => {0}'.format(SMOOTH_STREAMS_EPG_FILE_NAME))

        data_id = None
        events_id = None

        generated_on = None

        channel_icon_url = None
        channel_name = ''
        channel_number = None

        programs = []

        program_description = ''
        program_runtime = None
        program_title = ''
        program_start_date_time_in_utc = None

        db = IPTVProxyDatabase()

        # noinspection PyBroadException
        try:
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

                    programs.append(IPTVProxyEPGProgram('',
                                                        program_description,
                                                        program_end_date_time_in_utc,
                                                        program_start_date_time_in_utc,
                                                        '',
                                                        program_title))
                    program_description = ''
                    program_runtime = None
                    program_title = ''
                    program_start_date_time_in_utc = None
                elif (prefix, event) == ('data.{0}.events.{1}.description'.format(data_id, events_id), 'string'):
                    program_description = html.unescape(value)
                elif (prefix, event) == ('data.{0}.events.{1}.name'.format(data_id, events_id), 'string'):
                    program_title = html.unescape(value)
                elif (prefix, event) == ('data.{0}.events.{1}.runtime'.format(data_id, events_id), 'number'):
                    program_runtime = value
                elif (prefix, event) == ('data.{0}.events.{1}.runtime'.format(data_id, events_id), 'string'):
                    program_runtime = int(value)
                elif (prefix, event) == ('data.{0}.events.{1}.time'.format(data_id, events_id), 'string'):
                    program_start_date_time_in_utc = datetime.fromtimestamp(int(value), pytz.utc)
                elif (prefix, event) == ('data.{0}.img'.format(data_id), 'string'):
                    channel_icon_url = value
                elif (prefix, event) == ('data.{0}'.format(data_id), 'end_map'):
                    channel_id = '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID,
                                                         '{0} - (SmoothStreams)'.format(channel_number)))

                    channel = IPTVProxyEPGChannel('SmoothStreams',
                                                  channel_icon_url,
                                                  channel_id,
                                                  channel_name,
                                                  channel_number)
                    channel.programs = programs

                    cls._apply_optional_settings(channel)

                    SmoothStreamsSQL.insert_channel(db, channel)
                    for program in programs:
                        SmoothStreamsSQL.insert_program(db, channel_id, program)

                    channel_icon_url = None
                    channel_name = None
                    channel_number = None

                    programs = []
                elif (prefix, event) == ('data.{0}.name'.format(data_id), 'string'):
                    channel_name = html.unescape(value).strip()
                elif (prefix, event) == ('data.{0}.number'.format(data_id), 'string'):
                    channel_number = int(value)

            db.commit()

            logger.debug('Processed SmoothStreams JSON EPG\n'
                         'File name    => {0}\n'
                         'Generated on => {1}'.format(SMOOTH_STREAMS_EPG_FILE_NAME,
                                                      generated_on))
        except Exception:
            db.rollback()

            logger.debug('Failed to process SmoothStreams JSON EPG\n'
                         'File name    => {0}'.format(SMOOTH_STREAMS_EPG_FILE_NAME))

            raise
        finally:
            db.close_connection()

    @classmethod
    def _refresh_epg(cls):
        logger.debug('SmoothStreams EPG refresh timer triggered')

        # noinspection PyBroadException
        try:
            cls._generate_epg()
        except Exception:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

    @classmethod
    def _request_fog_channels_json(cls):
        url = '{0}{1}'.format(SMOOTH_STREAMS_FOG_EPG_BASE_URL, SMOOTH_STREAMS_FOG_CHANNELS_JSON_FILE_NAME)

        logger.debug('Downloading {0}\n'
                     'URL => {1}'.format(SMOOTH_STREAMS_FOG_CHANNELS_JSON_FILE_NAME, url))

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
    def _request_fog_epg_xml(cls):
        url = '{0}{1}'.format(SMOOTH_STREAMS_FOG_EPG_BASE_URL, SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME)

        logger.debug('Downloading {0}\n'
                     'URL => {1}'.format(SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME, url))

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
    def _request_other_epg_xml(cls):
        url = '{0}'.format(IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_URL'))

        logger.debug('Downloading external XML EPG\n'
                     'URL => {1}'.format(SMOOTH_STREAMS_FOG_EPG_XML_FILE_NAME, url))

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
        db = IPTVProxyDatabase()
        channel_name_records = SmoothStreamsSQL.query_channel_by_channel_number(db, channel_number)
        db.close_connection()

        if channel_name_records:
            channel_name = channel_name_records[0]['name']
        else:
            channel_name = 'Channel {0:02}'.format(int(channel_number))

        return channel_name

    @classmethod
    def get_channel_numbers_range(cls):
        db = IPTVProxyDatabase()
        minimum_maximum_channel_number_records = SmoothStreamsSQL.query_minimum_maximum_channel_numbers(db)
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
        smooth_streams_do_use_icons_setting_records = SmoothStreamsSQL.query_setting(db, 'do_use_icons')
        smooth_streams_channel_name_map_md5_setting_records = SmoothStreamsSQL.query_setting(db, 'channel_name_map_md5')
        smooth_streams_epg_source_setting_records = SmoothStreamsSQL.query_setting(db, 'epg_source')
        smooth_streams_epg_url_setting_records = SmoothStreamsSQL.query_setting(db, 'epg_url')
        db.close_connection()

        if not smooth_streams_do_use_icons_setting_records or not \
                smooth_streams_channel_name_map_md5_setting_records or not \
                smooth_streams_epg_source_setting_records or \
                hashlib.md5(json.dumps(cls._channel_name_map, sort_keys=True).encode()).hexdigest() != \
                smooth_streams_channel_name_map_md5_setting_records[0]['value'] or \
                cls._do_use_smooth_streams_icons != \
                bool(int(smooth_streams_do_use_icons_setting_records[0]['value'])) or \
                IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') != \
                smooth_streams_epg_source_setting_records[0]['value'] or \
                (IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_SOURCE') == 'other' and
                 IPTVProxyConfiguration.get_configuration_parameter('SMOOTH_STREAMS_EPG_URL') !=
                 smooth_streams_epg_url_setting_records[0]['value']):
            logger.debug('Resetting EPG')

            cls._cancel_refresh_epg_timer()
            cls._generate_epg()
        else:
            cls._source = smooth_streams_epg_source_setting_records[0]['value']

    @classmethod
    def is_channel_number_in_epg(cls, channel_number):
        db = IPTVProxyDatabase()
        channel_name_records = SmoothStreamsSQL.query_channel_by_channel_number(db, channel_number)
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
    def set_do_use_smooth_streams_icons(cls, do_use_smooth_streams_icons):
        cls._do_use_smooth_streams_icons = do_use_smooth_streams_icons
