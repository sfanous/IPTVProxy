import base64
import json
import logging
import pickle
import re
import sys
import traceback
import urllib.parse
from datetime import datetime

import m3u8
import pytz
import requests
from rwlock import RWLock

from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.providers.iptv_provider.api import Provider
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants
from iptv_proxy.providers.vaderstreams.data_access import VaderStreamsDatabaseAccess
from iptv_proxy.providers.vaderstreams.db import VaderStreamsDatabase
from iptv_proxy.providers.vaderstreams.epg import VaderStreamsEPG
from iptv_proxy.proxy import IPTVProxy
from iptv_proxy.security import SecurityManager
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class VaderStreams(Provider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()

    @classmethod
    def _calculate_token(cls):
        credentials = {
            'username': Configuration.get_configuration_parameter('VADERSTREAMS_USERNAME'),
            'password': SecurityManager.decrypt_password(
                Configuration.get_configuration_parameter('VADERSTREAMS_PASSWORD')).decode(),
        }

        return base64.b64encode(json.dumps(credentials, separators=(',', ':')).encode()).decode()

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_do_reduce_hls_stream_delay(
                OptionalSettings.get_optional_settings_parameter('reduce_vaderstreams_delay'))
        except KeyError:
            pass

    @classmethod
    def download_chunks_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        authorization_token = requested_query_string_parameters.get('authorization_token')
        channel_name = requested_query_string_parameters.get('channel_name')
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        port = requested_query_string_parameters.get('port')
        server = requested_query_string_parameters.get('server')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc))

        requests_session = requests.Session()

        target_url = 'http://{0}{1}/{2}/tracks-v1a1/mono.m3u8'.format(
            server if re.match(r"\A\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\Z", server)
            else '{0}.vaders.tv'.format(server),
            port if port != ':80'
            else '',
            channel_name)

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_name   => {2}\n'
                     '    channel_number => {3}\n'
                     '    client_uuid    => {4}\n'
                     '    port           => {5}\n'
                     '    server         => {6}\n'
                     'Target path    => {7}\n'
                     '  Parameters\n'
                     '    token          => {8}'.format(client_ip_address,
                                                        requested_path,
                                                        channel_name,
                                                        channel_number,
                                                        client_uuid,
                                                        port,
                                                        server,
                                                        target_url,
                                                        authorization_token))

        response = Utility.make_http_request(requests_session.get,
                                             target_url,
                                             params={
                                                 'token': authorization_token
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response,
                                                                    is_content_text=True,
                                                                    do_print_content=True))

            chunks_m3u8 = response.text

            with cls._do_reduce_hls_stream_delay_lock.reader_lock:
                if cls._do_reduce_hls_stream_delay:
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

                            m3u8_object = m3u8.loads(response.text)

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
                        m3u8_object = m3u8.loads(response.text)

                        for i in range(len(m3u8_object.segments) - 3):
                            m3u8_object.segments.pop(0)

                            m3u8_object.media_sequence += 1

                        chunks_m3u8 = m3u8_object.dumps()

            IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_requested_channel_number', channel_number)

            match = re.search(r'http://(.*)\.vaders\.tv(:\d+)?/(.*)/tracks-v1a1/.*', chunks_m3u8)
            if match is None:
                match = re.search(r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?/(.*)/tracks-v1a1/.*',
                                  chunks_m3u8)
            if match is not None:
                server = match.group(1)
                port = match.group(2) if match.group(2) is not None and len(match.groups()) == 3 else ':80'
                channel_name = match.group(3) if len(match.groups()) == 3 else match.group(2)

            chunks_m3u8 = re.sub('.*/tracks-v1a1/', '', chunks_m3u8)

            return re.sub(r'.ts\?token=(.*)',
                          r'.ts?'
                          r'authorization_token=\1&'
                          'channel_name={0}&'
                          'channel_number={1}&'
                          'client_uuid={2}&'
                          'http_token={3}&'
                          'port={4}&'
                          'server={5}'.format(urllib.parse.quote(channel_name),
                                              channel_number,
                                              client_uuid,
                                              urllib.parse.quote(http_token) if http_token
                                              else '',
                                              urllib.parse.quote(port),
                                              urllib.parse.quote(server)),
                          chunks_m3u8.replace('/', '_'))
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def download_playlist_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        protocol = requested_query_string_parameters.get('protocol')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc))

        authorization_token = cls._calculate_token()

        if protocol == 'hls':
            requests_session = requests.Session()

            target_url = 'http://vapi.vaders.tv/play/{0}.m3u8'.format(channel_number)

            logger.debug('Proxying request\n'
                         'Source IP      => {0}\n'
                         'Requested path => {1}\n'
                         '  Parameters\n'
                         '    channel_number => {2}\n'
                         '    client_uuid    => {3}\n'
                         '    protocol       => {4}\n'
                         'Target path    => {5}\n'
                         '  Parameters\n'
                         '    token          => {6}'.format(client_ip_address,
                                                            requested_path,
                                                            channel_number,
                                                            client_uuid,
                                                            protocol,
                                                            target_url,
                                                            authorization_token))

            response = Utility.make_http_request(requests_session.get,
                                                 target_url,
                                                 params={
                                                     'token': authorization_token
                                                 },
                                                 headers=requests_session.headers,
                                                 cookies=requests_session.cookies.get_dict())

            if response.status_code == requests.codes.OK:
                logger.trace(Utility.assemble_response_from_log_message(response,
                                                                        is_content_text=True,
                                                                        do_print_content=True))

                match = re.search(r'http://(.*)\.vaders\.tv(:\d+)?/(.*)/tracks-v1a1/.*', response.text)
                if match is None:
                    match = re.search(r'http://(.*)\.vaders\.tv(:\d+)?/(.*)/index.m3u8.*', response.request.url)
                    if match is None:
                        match = re.search(r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?/(.*)/index.m3u8.*',
                                          response.request.url)

                server = match.group(1)
                port = match.group(2) if match.group(2) is not None and len(match.groups()) == 3 else ':80'
                channel_name = match.group(3) if len(match.groups()) == 3 else match.group(2)

                return re.sub(r'tracks-v1a1/mono.m3u8\?token=(.*)',
                              'chunks.m3u8?'
                              r'authorization_token=\1&'
                              'channel_name={0}&'
                              'channel_number={1}&'
                              'client_uuid={2}&'
                              'http_token={3}&'
                              'port={4}&'
                              'server={5}'.format(urllib.parse.quote(channel_name),
                                                  channel_number,
                                                  client_uuid,
                                                  urllib.parse.quote(http_token) if http_token
                                                  else '',
                                                  urllib.parse.quote(port),
                                                  urllib.parse.quote(server)),
                              re.sub('.*/tracks-v1a1/', 'tracks-v1a1/', response.text))
            else:
                logger.error(Utility.assemble_response_from_log_message(response))

                response.raise_for_status()
        elif protocol == 'mpegts':
            return '#EXTM3U\n' \
                   '#EXTINF:-1 ,{0}\n' \
                   'http://vapi.vaders.tv/play/{1}.ts?' \
                   'token={2}'.format(VaderStreamsEPG.get_channel_name(int(channel_number)),
                                      channel_number,
                                      authorization_token)

    @classmethod
    def download_ts_file(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        authorization_token = requested_query_string_parameters.get('authorization_token')
        channel_name = requested_query_string_parameters.get('channel_name')
        channel_number = requested_query_string_parameters.get('channel_number')
        port = requested_query_string_parameters.get('port')
        server = requested_query_string_parameters.get('server')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc))

        requests_session = requests.Session()

        target_url = 'http://{0}{1}/{2}{3}'.format(server
                                                   if re.match(r"\A\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\Z", server)
                                                   else '{0}.vaders.tv'.format(server),
                                                   port if port != ':80'
                                                   else '',
                                                   channel_name,
                                                   re.sub(r'(/.*)?(/.*\.ts)',
                                                          r'\2',
                                                          requested_path).replace('_', '/'))

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_name   => {2}\n'
                     '    channel_number => {3}\n'
                     '    client_uuid    => {4}\n'
                     '    port           => {5}\n'
                     '    server         => {6}\n'
                     'Target path    => {7}\n'
                     '  Parameters\n'
                     '    token          => {8}'.format(client_ip_address,
                                                        requested_path,
                                                        channel_name,
                                                        channel_number,
                                                        client_uuid,
                                                        port,
                                                        server,
                                                        target_url,
                                                        authorization_token))

        response = Utility.make_http_request(requests_session.get,
                                             target_url,
                                             params={
                                                 'token': authorization_token
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response,
                                                                    is_content_binary=True))

            IPTVProxy.set_serviceable_client_parameter(client_uuid,
                                                       'last_requested_ts_file_path',
                                                       re.sub(r'(/.*)?(/.*\.ts)',
                                                              r'\2',
                                                              requested_path).replace('_', '/')[1:])

            return response.content
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def generate_playlist_m3u8(cls,
                               is_server_secure,
                               client_ip_address,
                               client_uuid,
                               requested_query_string_parameters):
        http_token = requested_query_string_parameters.get('http_token')
        playlist_protocol = requested_query_string_parameters.get('playlist_protocol')
        playlist_type = requested_query_string_parameters.get('playlist_type')

        try:
            client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)
            server_hostname = Configuration.get_configuration_parameter(
                'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
            server_port = Configuration.get_configuration_parameter(
                'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                             else ''))

            playlist_m3u8 = ['#EXTM3U x-tvg-url="{0}://{1}:{2}/live/vadertreams/epg.xml"\n'.format(
                'https' if is_server_secure
                else 'http',
                server_hostname,
                server_port)]

            generate_playlist_m3u8_tracks_mapping = dict(client_uuid=client_uuid,
                                                         http_token=http_token,
                                                         is_server_secure=is_server_secure,
                                                         playlist_protocol=playlist_protocol,
                                                         playlist_type=playlist_type,
                                                         server_hostname=server_hostname,
                                                         server_port=server_port)

            playlist_m3u8.append(''.join(cls.generate_playlist_m3u8_tracks(generate_playlist_m3u8_tracks_mapping)))

            logger.debug('Generated live playlist.m3u8')

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

        return '{0}://{1}:{2}/live/vaderstreams/playlist.m3u8?' \
               'channel_number={3:02}&' \
               'client_uuid={4}&' \
               'http_token={5}&' \
               'protocol={6}'.format('https' if is_server_secure
                                     else 'http',
                                     server_hostname,
                                     server_port,
                                     int(channel_number),
                                     client_uuid,
                                     urllib.parse.quote(http_token) if http_token
                                     else '',
                                     playlist_protocol)

    @classmethod
    def generate_playlist_m3u8_tracks(cls, generate_playlist_m3u8_tracks_mapping):
        client_uuid = generate_playlist_m3u8_tracks_mapping['client_uuid']
        http_token = generate_playlist_m3u8_tracks_mapping['http_token']
        is_server_secure = generate_playlist_m3u8_tracks_mapping['is_server_secure']
        playlist_protocol = generate_playlist_m3u8_tracks_mapping['playlist_protocol']
        playlist_type = generate_playlist_m3u8_tracks_mapping['playlist_type']
        server_hostname = generate_playlist_m3u8_tracks_mapping['server_hostname']
        server_port = generate_playlist_m3u8_tracks_mapping['server_port']

        if playlist_protocol not in VaderStreamsConstants.VALID_PLAYLIST_PROTOCOL_VALUES:
            playlist_protocol = Configuration.get_configuration_parameter('VADERSTREAMS_PLAYLIST_PROTOCOL')

        if playlist_type not in VaderStreamsConstants.VALID_PLAYLIST_TYPE_VALUES:
            playlist_type = Configuration.get_configuration_parameter('VADERSTREAMS_PLAYLIST_TYPE')

        tracks = {}

        with VaderStreamsDatabase.get_access_lock().shared_lock:
            db_session = VaderStreamsDatabase.create_session()

            try:
                for channel_row in VaderStreamsDatabaseAccess.query_channels_pickle(db_session):
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
                        track_information.append(
                            'http://vapi.vaders.tv/play/{0:02}.{1}?token={2}\n'.format(
                                channel.number,
                                'm3u8' if playlist_protocol == 'hls'
                                else 'ts',
                                cls._calculate_token()))

                    tracks['{0} {1} {2}'.format(channel.m3u8_group,
                                                channel.display_names[0].text,
                                                channel.number)] = ''.join(track_information)
            finally:
                db_session.close()

        return [tracks[channel_name] for channel_name in sorted(tracks,
                                                                key=lambda channel_name_: channel_name_.lower())]

    @classmethod
    def get_supported_protocols(cls):
        return VaderStreamsConstants.VALID_PLAYLIST_PROTOCOL_VALUES

    @classmethod
    def initialize(cls, **kwargs):
        try:
            pass
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()

    @classmethod
    def terminate(cls, **kwargs):
        try:
            pass
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()

    @classmethod
    def set_do_reduce_hls_stream_delay(cls, do_reduce_hls_stream_delay):
        with cls._do_reduce_hls_stream_delay_lock.writer_lock:
            cls._do_reduce_hls_stream_delay = do_reduce_hls_stream_delay
