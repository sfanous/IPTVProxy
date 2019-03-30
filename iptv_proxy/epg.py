import copy
import functools
import logging
import xml.sax.saxutils
from datetime import datetime
from datetime import timedelta
from threading import RLock

import pytz
import tzlocal

from .configuration import IPTVProxyConfiguration
from .constants import VERSION
from .constants import XML_TV_TEMPLATES
from .db import IPTVProxyDatabase
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class IPTVProxyEPG(object):
    __slots__ = []

    _lock = RLock()

    @classmethod
    def _convert_epg_to_xml_tv(cls,
                               is_server_secure,
                               authorization_required,
                               client_ip_address,
                               providers,
                               number_of_days):
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
            'tv_source_data_url': ''
        }

        yield '{0}\n'.format(xml_tv_templates['tv_header.xml.st'].substitute(tv_xml_template_fields))

        cutoff_date_time_in_local = datetime.now(tzlocal.get_localzone()).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0) + timedelta(days=int(number_of_days) + 1)
        cutoff_date_time_in_utc = cutoff_date_time_in_local.astimezone(pytz.utc)

        for provider in providers.values():
            db = IPTVProxyDatabase()
            channel_records = provider['sql'].query_channels(db)
            db.close_connection()

            for channel_record in channel_records:
                xmltv_elements = []

                channel_xml_template_fields = {
                    'channel_id': channel_record['id'],
                    'channel_name': xml.sax.saxutils.escape(channel_record['name']),
                    'channel_icon': '        <icon src="{0}" />\n'.format(
                        xml.sax.saxutils.escape(
                            channel_record['icon_url'].format(
                                's'
                                if is_server_secure
                                else '',
                                server_hostname,
                                server_port,
                                '?http_token={0}'.format(
                                    IPTVProxyConfiguration.get_configuration_parameter('SERVER_PASSWORD'))
                                if authorization_required
                                else '')))
                    if channel_record['icon_url']
                    else ''
                }

                xmltv_elements.append(
                    '{0}\n'.format(xml_tv_templates['channel.xml.st'].substitute(channel_xml_template_fields)))

                db = IPTVProxyDatabase()
                program_records = provider['sql'].query_programs_by_channel_id(db, channel_record['id'])
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

                        xmltv_elements.append('{0}\n'.format(
                            xml_tv_templates['programme.xml.st'].substitute(programme_xml_template_fields)))

                yield ''.join(xmltv_elements)

        yield '{0}\n'.format(xml_tv_templates['tv_footer.xml.st'].substitute())

    @classmethod
    def generate_epg_xml_file(cls,
                              is_server_secure,
                              authorization_required,
                              client_ip_address,
                              providers,
                              number_of_days):
        return functools.partial(cls._convert_epg_to_xml_tv,
                                 is_server_secure,
                                 authorization_required,
                                 client_ip_address,
                                 providers,
                                 number_of_days)


class IPTVProxyEPGChannel(object):
    __slots__ = ['_group', '_icon_data_uri', '_icon_url', '_id', '_name', '_number', '_programs']

    def __init__(self, group, icon_url, id_, name, number):
        self._group = group
        self._icon_data_uri = None
        self._icon_url = icon_url
        self._id = id_
        self._name = name
        self._number = number
        self._programs = []

    def add_program(self, program):
        self._programs.append(program)

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, group):
        self._group = group

    @property
    def icon_data_uri(self):
        return self._icon_data_uri

    @icon_data_uri.setter
    def icon_data_uri(self, icon_data_uri):
        self._icon_data_uri = icon_data_uri

    @property
    def icon_url(self):
        return self._icon_url

    @icon_url.setter
    def icon_url(self, icon_url):
        self._icon_url = icon_url

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, number):
        self._number = number

    @property
    def programs(self):
        return tuple(self._programs)

    @programs.setter
    def programs(self, programs):
        self._programs = programs


class IPTVProxyEPGProgram(object):
    __slots__ = ['_category', '_description', '_end_date_time_in_utc', '_start_date_time_in_utc', '_sub_title',
                 '_title']

    def __init__(self,
                 category='',
                 description='',
                 end_date_time_in_utc=None,
                 start_date_time_in_utc=None,
                 sub_title='',
                 title=''):
        self._category = category
        self._description = description
        self._end_date_time_in_utc = end_date_time_in_utc
        self._start_date_time_in_utc = start_date_time_in_utc
        self._sub_title = sub_title
        self._title = title

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, category):
        self._category = category

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self._description = description

    @property
    def end_date_time_in_utc(self):
        return self._end_date_time_in_utc

    @end_date_time_in_utc.setter
    def end_date_time_in_utc(self, end_date_time_in_utc):
        self._end_date_time_in_utc = end_date_time_in_utc

    @property
    def start_date_time_in_utc(self):
        return self._start_date_time_in_utc

    @start_date_time_in_utc.setter
    def start_date_time_in_utc(self, start_date_time_in_utc):
        self._start_date_time_in_utc = start_date_time_in_utc

    @property
    def sub_title(self):
        return self._sub_title

    @sub_title.setter
    def sub_title(self, sub_title):
        self._sub_title = sub_title

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title
