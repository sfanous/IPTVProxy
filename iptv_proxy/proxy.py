import logging
import sys
import traceback
from threading import RLock

from iptv_proxy.configuration import Configuration
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class IPTVProxy(object):
    __slots__ = []

    _serviceable_clients = {}
    _serviceable_clients_lock = RLock()

    @classmethod
    def _add_client_to_serviceable_clients(cls, client_uuid, client_ip_address):
        with cls._serviceable_clients_lock:
            cls._serviceable_clients[client_uuid] = {}
            cls._serviceable_clients[client_uuid]['ip_address'] = client_ip_address

    @classmethod
    def generate_playlist_m3u8(cls,
                               is_server_secure,
                               client_ip_address,
                               client_uuid,
                               requested_query_string_parameters,
                               providers):
        http_token = requested_query_string_parameters.get('http_token')
        playlist_protocol = requested_query_string_parameters.get('protocol')
        playlist_type = requested_query_string_parameters.get('type')

        try:
            client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)
            server_hostname = Configuration.get_configuration_parameter(
                'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
            server_port = Configuration.get_configuration_parameter(
                'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                             else ''))

            playlist_m3u8 = ['#EXTM3U x-tvg-url="{0}://{1}:{2}/live/epg.xml"\n'.format(
                'https' if is_server_secure
                else 'http',
                server_hostname,
                server_port)]

            for (provider_name, provider) in sorted(list(providers.items())):
                provider_protocol = playlist_protocol
                provider_type = playlist_type

                try:
                    provider_protocol = requested_query_string_parameters['{0}_protocol'.format(provider_name)]
                except KeyError:
                    pass

                try:
                    provider_type = requested_query_string_parameters['{0}_type'.format(provider_name)]
                except KeyError:
                    pass

                generate_playlist_m3u8_tracks_mapping = dict(client_uuid=client_uuid,
                                                             http_token=http_token,
                                                             is_server_secure=is_server_secure,
                                                             playlist_protocol=provider_protocol,
                                                             playlist_type=provider_type,
                                                             server_hostname=server_hostname,
                                                             server_port=server_port)

                playlist_m3u8.append(
                    ''.join(provider.api_class().generate_playlist_m3u8_tracks(generate_playlist_m3u8_tracks_mapping)))

            logger.debug('Generated live IPTVProxy playlist.m3u8')

            return ''.join(playlist_m3u8)
        except (KeyError, ValueError):
            (status, value_, traceback_) = sys.exc_info()

            logger.error('\n'.join(traceback.format_exception(status, value_, traceback_)))

    @classmethod
    def get_serviceable_client_parameter(cls, client_uuid, parameter_name):
        with cls._serviceable_clients_lock:
            return cls._serviceable_clients[client_uuid][parameter_name]

    @classmethod
    def refresh_serviceable_clients(cls, client_uuid, client_ip_address):
        with cls._serviceable_clients_lock:
            if client_uuid not in cls._serviceable_clients:
                logger.debug('Adding client to serviceable clients\n'
                             'Client IP address => {0}\n'
                             'Client ID         => {1}'.format(client_ip_address, client_uuid))

                cls._add_client_to_serviceable_clients(client_uuid, client_ip_address)

    @classmethod
    def set_serviceable_client_parameter(cls, client_uuid, parameter_name, parameter_value):
        with cls._serviceable_clients_lock:
            cls._serviceable_clients[client_uuid][parameter_name] = parameter_value
