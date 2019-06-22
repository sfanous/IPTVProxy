import logging
import pickle
import re
import sys
import traceback
import urllib.parse
from abc import ABC
from abc import abstractmethod
from datetime import datetime

import m3u8
import pytz
import requests

from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.enums import M388PlaylistSortOrder
from iptv_proxy.providers import ProvidersController
from iptv_proxy.proxy import IPTVProxy
from iptv_proxy.security import SecurityManager
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class Provider(ABC):
    _do_reduce_hls_stream_delay = None
    _do_reduce_hls_stream_delay_lock = None
    _provider_name = None

    @classmethod
    @abstractmethod
    def _generate_playlist_m3u8_static_track_url(cls, track_information, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def _initialize(cls, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def _initialize_class_variables(cls):
        pass

    @classmethod
    def _reduce_hls_stream_delay(cls, chunks_m3u8, client_uuid, channel_number, number_of_segments_to_keep=3):
        do_reduce_hls_stream_delay = False

        try:
            last_requested_channel_number = IPTVProxy.get_serviceable_client_parameter(
                client_uuid,
                'last_requested_channel_number')

            if channel_number != last_requested_channel_number:
                do_reduce_hls_stream_delay = True
            else:
                last_requested_ts_file_path = IPTVProxy.get_serviceable_client_parameter(
                    client_uuid,
                    'last_requested_ts_file_path')

                m3u8_object = m3u8.loads(chunks_m3u8)

                delete_segments_up_to_index = None

                for (segment_index, segment) in enumerate(m3u8_object.segments):
                    if last_requested_ts_file_path in segment.uri:
                        delete_segments_up_to_index = segment_index

                        break

                if delete_segments_up_to_index:
                    for i in range(delete_segments_up_to_index + 1):
                        m3u8_object.segments.pop(0)

                        m3u8_object.media_sequence += 1

                    chunks_m3u8 = m3u8_object.dumps()
        except KeyError:
            do_reduce_hls_stream_delay = True

        if do_reduce_hls_stream_delay:
            m3u8_object = m3u8.loads(chunks_m3u8)

            for i in range(len(m3u8_object.segments) - number_of_segments_to_keep):
                m3u8_object.segments.pop(0)

                m3u8_object.media_sequence += 1

            chunks_m3u8 = m3u8_object.dumps()

        return chunks_m3u8

    @classmethod
    @abstractmethod
    def _retrieve_fresh_authorization_token(cls):
        pass

    @classmethod
    @abstractmethod
    def _terminate(cls, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def download_chunks_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        pass

    @classmethod
    @abstractmethod
    def download_playlist_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        pass

    @classmethod
    @abstractmethod
    def download_ts_file(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        pass

    @classmethod
    def generate_playlist_m3u8(cls,
                               is_server_secure,
                               client_ip_address,
                               client_uuid,
                               requested_query_string_parameters):
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

            playlist_m3u8 = ['#EXTM3U x-tvg-url="{0}://{1}:{2}/live/{3}/epg.xml"\n'.format(
                'https' if is_server_secure
                else 'http',
                server_hostname,
                server_port,
                cls._provider_name)]

            generate_playlist_m3u8_tracks_mapping = dict(client_uuid=client_uuid,
                                                         http_token=http_token,
                                                         is_server_secure=is_server_secure,
                                                         playlist_protocol=playlist_protocol,
                                                         playlist_type=playlist_type,
                                                         server_hostname=server_hostname,
                                                         server_port=server_port)

            playlist_m3u8.append(''.join(cls.generate_playlist_m3u8_tracks(generate_playlist_m3u8_tracks_mapping)))

            logger.debug('Generated live {0} playlist.m3u8'.format(cls.__name__))

            return ''.join(playlist_m3u8)
        except (KeyError, ValueError):
            (status, value_, traceback_) = sys.exc_info()

            logger.error('\n'.join(traceback.format_exception(status, value_, traceback_)))

    @classmethod
    def generate_playlist_m3u8_track_url(cls, generate_playlist_m3u8_track_url_mapping):
        channel_number = generate_playlist_m3u8_track_url_mapping['channel_number']
        client_uuid = generate_playlist_m3u8_track_url_mapping['client_uuid']
        http_token = generate_playlist_m3u8_track_url_mapping['http_token']
        is_server_secure = generate_playlist_m3u8_track_url_mapping['is_server_secure']
        playlist_protocol = generate_playlist_m3u8_track_url_mapping['playlist_protocol']
        server_hostname = generate_playlist_m3u8_track_url_mapping['server_hostname']
        server_port = generate_playlist_m3u8_track_url_mapping['server_port']

        return '{0}://{1}:{2}/live/{3}/playlist.m3u8?' \
               'channel_number={4:02}&' \
               'client_uuid={5}&' \
               'http_token={6}&' \
               'protocol={7}'.format('https' if is_server_secure
                                     else 'http',
                                     server_hostname,
                                     server_port,
                                     cls._provider_name,
                                     int(channel_number),
                                     client_uuid,
                                     urllib.parse.quote(http_token) if http_token
                                     else '',
                                     playlist_protocol)

    @classmethod
    def generate_playlist_m3u8_tracks(cls,
                                      generate_playlist_m3u8_tracks_mapping,
                                      sort_by=M388PlaylistSortOrder.CHANNEL_NAME.value):
        client_uuid = generate_playlist_m3u8_tracks_mapping['client_uuid']
        http_token = generate_playlist_m3u8_tracks_mapping['http_token']
        is_server_secure = generate_playlist_m3u8_tracks_mapping['is_server_secure']
        playlist_protocol = generate_playlist_m3u8_tracks_mapping['playlist_protocol']
        playlist_type = generate_playlist_m3u8_tracks_mapping['playlist_type']
        server_hostname = generate_playlist_m3u8_tracks_mapping['server_hostname']
        server_port = generate_playlist_m3u8_tracks_mapping['server_port']

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        if playlist_protocol not in provider_map_class.constants_class().VALID_PLAYLIST_PROTOCOL_VALUES:
            playlist_protocol = Configuration.get_configuration_parameter(
                '{0}_PLAYLIST_PROTOCOL'.format(cls.__name__.upper()))

        if playlist_type not in provider_map_class.constants_class().VALID_PLAYLIST_TYPE_VALUES:
            playlist_type = Configuration.get_configuration_parameter('{0}_PLAYLIST_TYPE'.format(cls.__name__.upper()))

        authorization_token = None

        tracks = {}

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                for channel_row in provider_map_class.database_access_class().query_channels_pickle(db_session):
                    channel = pickle.loads(channel_row.pickle)

                    track_information = [
                        '#EXTINF:-1 group-title="{0}" '
                        'tvg-id="{1}" '
                        'tvg-name="{2}" '
                        'tvg-logo="{3}" '
                        'channel-id="{4}",{2}\n'.format(
                            channel.m3u8_group,
                            channel.xmltv_id,
                            channel.display_names[0].text,
                            channel.icons[0].source.format('s' if is_server_secure
                                                           else '',
                                                           server_hostname,
                                                           server_port,
                                                           '?http_token={0}'.format(
                                                               urllib.parse.quote(http_token)) if http_token
                                                           else '').replace(' ', '%20'),
                            channel.number)]

                    if playlist_type == 'dynamic':
                        generate_playlist_m3u8_track_url_mapping = dict(channel_number=channel.number,
                                                                        client_uuid=client_uuid,
                                                                        http_token=http_token,
                                                                        is_server_secure=is_server_secure,
                                                                        playlist_protocol=playlist_protocol,
                                                                        server_hostname=server_hostname,
                                                                        server_port=server_port)

                        track_information.append('{0}\n'.format(
                            cls.generate_playlist_m3u8_track_url(generate_playlist_m3u8_track_url_mapping)))
                    elif playlist_type == 'static':
                        if authorization_token is None:
                            authorization_token = cls._retrieve_fresh_authorization_token()

                        cls._generate_playlist_m3u8_static_track_url(track_information,
                                                                     channel_number=channel.number,
                                                                     playlist_protocol=playlist_protocol,
                                                                     authorization_token=authorization_token)

                    if sort_by == M388PlaylistSortOrder.CHANNEL_NAME.value:
                        tracks['{0} {1} {2}'.format(channel.m3u8_group,
                                                    channel.display_names[0].text,
                                                    channel.number)] = ''.join(track_information)
                    elif sort_by == M388PlaylistSortOrder.CHANNEL_NUMBER.value:
                        tracks[channel.number] = ''.join(track_information)
            finally:
                db_session.close()

        if not sort_by:
            return [tracks[channel_name] for channel_name in sorted(tracks,
                                                                    key=lambda channel_name_: channel_name_.lower())]
        else:
            return [tracks[channel_number] for channel_number in sorted(tracks)]

    @classmethod
    def get_supported_protocols(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        return provider_map_class.constants_class().VALID_PLAYLIST_PROTOCOL_VALUES

    @classmethod
    def initialize(cls, **kwargs):
        try:
            cls._initialize_class_variables()

            cls._initialize(**kwargs)
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()

    @classmethod
    def is_attribute_supported(cls, attribute_name):
        if getattr(cls, '{0}_lock'.format(attribute_name)) is not None:
            return True

        return False

    @classmethod
    def set_do_reduce_hls_stream_delay(cls, do_reduce_hls_stream_delay):
        with cls._do_reduce_hls_stream_delay_lock.writer_lock:
            cls._do_reduce_hls_stream_delay = do_reduce_hls_stream_delay

    @classmethod
    def terminate(cls, **kwargs):
        try:
            cls._terminate(**kwargs)
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()


class XtreamCodesProvider(Provider):
    @classmethod
    def _generate_playlist_m3u8_static_track_url(cls, track_information, **kwargs):
        channel_number = kwargs['channel_number']
        playlist_protocol = kwargs['playlist_protocol']

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('{0}_PASSWORD'.format(cls._provider_name.upper()))).decode()

        track_information.append(
            '{0}{1}{2}/{3}/{4}{5}\n'.format(
                ProvidersController.get_provider_map_class(cls._provider_name).constants_class().BASE_URL,
                'live/' if playlist_protocol == 'hls'
                else '',
                username,
                password,
                channel_number,
                '.m3u8' if playlist_protocol == 'hls'
                else '.ts'))

    @classmethod
    def _initialize(cls, **kwargs):
        pass

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_do_reduce_hls_stream_delay(
                OptionalSettings.get_optional_settings_parameter('reduce_{0}_delay'.format(cls._provider_name)))
        except KeyError:
            pass

    @classmethod
    def _retrieve_fresh_authorization_token(cls):
        return None

    @classmethod
    def _terminate(cls, **kwargs):
        pass

    @classmethod
    def download_chunks_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        protocol = requested_query_string_parameters.get('protocol')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc))

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('{0}_PASSWORD'.format(cls._provider_name.upper()))).decode()

        if protocol == 'hls':
            requests_session = requests.Session()

            target_url = '{0}live/{1}/{2}/{3}.m3u8'.format(
                ProvidersController.get_provider_map_class(cls._provider_name).constants_class().BASE_URL,
                username,
                password,
                channel_number)

            logger.debug('Proxying request\n'
                         'Source IP      => {0}\n'
                         'Requested path => {1}\n'
                         '  Parameters\n'
                         '    channel_number => {2}\n'
                         '    client_uuid    => {3}\n'
                         '    protocol       => {4}\n'
                         'Target path    => {5}'.format(client_ip_address,
                                                        requested_path,
                                                        channel_number,
                                                        client_uuid,
                                                        protocol,
                                                        target_url))

            response = Utility.make_http_request(requests_session.get,
                                                 target_url,
                                                 headers=requests_session.headers,
                                                 cookies=requests_session.cookies.get_dict())

            if response.status_code == requests.codes.OK:
                logger.trace(Utility.assemble_response_from_log_message(response,
                                                                        is_content_text=True,
                                                                        do_print_content=True))

                with cls._do_reduce_hls_stream_delay_lock.reader_lock:
                    if cls._do_reduce_hls_stream_delay:
                        chunks_m3u8 = cls._reduce_hls_stream_delay(response.text,
                                                                   client_uuid,
                                                                   channel_number,
                                                                   number_of_segments_to_keep=2)
                    else:
                        chunks_m3u8 = response.text

                IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_requested_channel_number', channel_number)

                match = re.search(r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?',
                                  response.request.url)

                server = match.group(1)
                port = match.group(2) if len(match.groups()) == 2 else ':80'

                return re.sub(r'/hlsr/(.*)/(.*)/(.*)/(.*)/(.*)/(.*).ts',
                              r'\6.ts?'
                              r'authorization_token=\1&'
                              'channel_number={0}&'
                              'client_uuid={1}&'
                              'http_token={2}&'
                              r'leaf_directory=\5&'
                              'port={3}&'
                              'server={4}'.format(channel_number,
                                                  client_uuid,
                                                  urllib.parse.quote(http_token) if http_token
                                                  else '',
                                                  urllib.parse.quote(port),
                                                  urllib.parse.quote(server)),
                              chunks_m3u8)
            else:
                logger.error(Utility.assemble_response_from_log_message(response))

                response.raise_for_status()
        elif protocol == 'mpegts':
            provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

            return '#EXTM3U\n' \
                   '#EXTINF:-1 ,{0}\n' \
                   '{1}live/{2}/{3}/{4}.ts' \
                   ''.format(provider_map_class.epg_class().get_channel_name(int(channel_number)),
                             provider_map_class.constants_class().BASE_URL,
                             username,
                             password,
                             channel_number)

    @classmethod
    def download_playlist_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        return cls.download_chunks_m3u8(client_ip_address,
                                        client_uuid,
                                        requested_path,
                                        requested_query_string_parameters)

    @classmethod
    def download_ts_file(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        authorization_token = requested_query_string_parameters.get('authorization_token')
        channel_number = requested_query_string_parameters.get('channel_number')
        leaf_directory = requested_query_string_parameters.get('leaf_directory')
        port = requested_query_string_parameters.get('port')
        server = requested_query_string_parameters.get('server')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc))

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('{0}_PASSWORD'.format(cls._provider_name.upper()))).decode()

        requests_session = requests.Session()

        target_url = 'http://{0}{1}/hlsr/{2}/{3}/{4}/{5}/{6}/{7}'.format(server,
                                                                         port if port != ':80'
                                                                         else '',
                                                                         authorization_token,
                                                                         username,
                                                                         password,
                                                                         channel_number,
                                                                         leaf_directory,
                                                                         re.sub(r'(/.*)?(/.*\.ts)',
                                                                                r'\2',
                                                                                requested_path))

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_number => {2}\n'
                     '    client_uuid    => {3}\n'
                     '    port           => {4}\n'
                     '    server         => {5}\n'
                     'Target path    => {6}'.format(client_ip_address,
                                                    requested_path,
                                                    channel_number,
                                                    client_uuid,
                                                    port,
                                                    server,
                                                    target_url))

        response = Utility.make_http_request(requests_session.get,
                                             target_url,
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response,
                                                                    is_content_binary=True))

            IPTVProxy.set_serviceable_client_parameter(client_uuid,
                                                       'last_requested_ts_file_path',
                                                       re.sub(r'(/.*)?(/.*\.ts)',
                                                              r'\2',
                                                              requested_path)[1:])

            return response.content
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()
