import logging
from datetime import datetime
from datetime import timedelta

import pytz
import tzlocal

from iptv_proxy.configuration import Configuration
from iptv_proxy.constants import VERSION
from iptv_proxy.enums import EPGStyle
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class EPG(object):
    __slots__ = []

    @classmethod
    def generate_xmltv(cls,
                       is_server_secure,
                       authorization_required,
                       client_ip_address,
                       providers_map_class,
                       number_of_days,
                       style):
        current_date_time_in_utc = datetime.now(pytz.utc)

        yield '<?xml version="1.0" encoding="utf-8"?>\n<tv date="{0}" generator-info-name="IPTVProxy {1}">\n'.format(
            current_date_time_in_utc.strftime('%Y%m%d%H%M%S %z'),
            VERSION)

        client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)
        server_password = Configuration.get_configuration_parameter('SERVER_PASSWORD')
        server_hostname = Configuration.get_configuration_parameter(
            'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
        server_port = Configuration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                         else ''))

        cutoff_date_time_in_local = datetime.now(tzlocal.get_localzone()).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0) + timedelta(days=int(number_of_days) + 1)
        cutoff_date_time_in_utc = cutoff_date_time_in_local.astimezone(pytz.utc)

        for provider_map_class in providers_map_class.values():
            with provider_map_class.database_class().get_access_lock().shared_lock:
                db_session = provider_map_class.database_class().create_session()

                try:
                    if style.capitalize() == EPGStyle.COMPLETE.value:
                        query_channels_xmltv = provider_map_class.database_access_class().query_channels_complete_xmltv
                        query_programs_xmltv = provider_map_class.database_access_class().query_programs_complete_xmltv
                    else:
                        query_channels_xmltv = provider_map_class.database_access_class().query_channels_minimal_xmltv
                        query_programs_xmltv = provider_map_class.database_access_class().query_programs_minimal_xmltv

                    for channel_row in query_channels_xmltv(db_session):
                        yield channel_row.xmltv.format(
                            's' if is_server_secure
                            else '',
                            server_hostname,
                            server_port,
                            '?http_token={0}'.format(server_password) if authorization_required
                            else '')

                    for program_row in query_programs_xmltv(db_session, cutoff_date_time_in_utc):
                        yield program_row.xmltv
                finally:
                    db_session.close()

        yield '</tv>\n'
