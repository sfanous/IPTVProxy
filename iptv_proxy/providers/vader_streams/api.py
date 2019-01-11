import base64
import json
import logging
import re
import sys
import traceback
import urllib.parse
from datetime import datetime

import m3u8
import pytz
import requests

from .constants import VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES
from .constants import VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES
from .db import VaderStreamsDB
from .epg import VaderStreamsEPG
from ..iptv_provider import IPTVProxyProvider
from ...configuration import IPTVProxyConfiguration
from ...proxy import IPTVProxy
from ...security import IPTVProxySecurityManager
from ...utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class VaderStreams(IPTVProxyProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True

    @classmethod
    def _calculate_token(cls):
        credentials = {
            'username': IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_USERNAME'),
            'password': IPTVProxySecurityManager.decrypt_password(
                IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_PASSWORD')).decode(),
        }

        return base64.b64encode(json.dumps(credentials, separators=(',', ':')).encode()).decode()

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

        http_session = requests.Session()

        target_url = 'http://{0}.vaders.tv{1}/{2}/tracks-v1a1/mono.m3u8'.format(server,
                                                                                port if port != ':80' else '',
                                                                                channel_name)

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_name    => {2}\n'
                     '    channel_number  => {3}\n'
                     '    client_uuid     => {4}\n'
                     '    port            => {5}\n'
                     '    server          => {6}\n'
                     'Target path    => {7}\n'
                     '  Parameters\n'
                     '    token           => {8}'.format(client_ip_address,
                                                         requested_path,
                                                         channel_name,
                                                         channel_number,
                                                         client_uuid,
                                                         port,
                                                         server,
                                                         target_url,
                                                         authorization_token))

        response = IPTVProxyUtility.make_http_request(http_session.get,
                                                      target_url,
                                                      params={
                                                          'token': authorization_token
                                                      },
                                                      headers=http_session.headers,
                                                      cookies=http_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            # noinspection PyUnresolvedReferences
            logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response,
                                                                             is_content_text=True,
                                                                             do_print_content=True))

            chunks_m3u8 = response.text

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

            match = re.search('http://(.*)\.vaders\.tv(:[0-9]+)?/(.*)/tracks-v1a1/.*', chunks_m3u8)
            if match is not None:
                server = match.group(1)
                port = match.group(2) if match.group(2) is not None and len(match.groups()) == 3 else ':80'
                channel_name = match.group(3) if len(match.groups()) == 3 else match.group(2)

            chunks_m3u8 = re.sub('.*/tracks-v1a1/', '', chunks_m3u8)

            return re.sub('.ts\?token=(.*)',
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
                                              urllib.parse.quote(http_token) if http_token else '',
                                              urllib.parse.quote(port),
                                              urllib.parse.quote(server)),
                          chunks_m3u8.replace('/', '_'))
        else:
            logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

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
            http_session = requests.Session()

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

            response = IPTVProxyUtility.make_http_request(http_session.get,
                                                          target_url,
                                                          params={
                                                              'token': authorization_token
                                                          },
                                                          headers=http_session.headers,
                                                          cookies=http_session.cookies.get_dict())

            if response.status_code == requests.codes.OK:
                # noinspection PyUnresolvedReferences
                logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response,
                                                                                 is_content_text=True,
                                                                                 do_print_content=True))

                match = re.search('http://(.*)\.vaders\.tv(:[0-9]+)?/(.*)/tracks-v1a1/.*', response.text)
                if match is None:
                    match = re.search('http://(.*)\.vaders\.tv(:[0-9]+)?/(.*)/index.m3u8.*', response.request.url)

                server = match.group(1)
                port = match.group(2) if match.group(2) is not None and len(match.groups()) == 3 else ':80'
                channel_name = match.group(3) if len(match.groups()) == 3 else match.group(2)

                return re.sub('tracks-v1a1/mono.m3u8\?token=(.*)',
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
                                                  urllib.parse.quote(http_token) if http_token else '',
                                                  urllib.parse.quote(port),
                                                  urllib.parse.quote(server)),
                              re.sub('.*/tracks-v1a1/', 'tracks-v1a1/', response.text))
            else:
                logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

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

        http_session = requests.Session()

        target_url = 'http://{0}.vaders.tv{1}/{2}{3}'.format(server,
                                                             port if port != ':80' else '',
                                                             channel_name,
                                                             re.sub(r'(/.*)?(/.*\.ts)',
                                                                    r'\2',
                                                                    requested_path).replace('_', '/'))

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_name    => {2}\n'
                     '    channel_number  => {3}\n'
                     '    client_uuid     => {4}\n'
                     '    port            => {5}\n'
                     '    server          => {6}\n'
                     'Target path    => {7}\n'
                     '  Parameters\n'
                     '    token           => {8}'.format(client_ip_address,
                                                         requested_path,
                                                         channel_name,
                                                         channel_number,
                                                         client_uuid,
                                                         port,
                                                         server,
                                                         target_url,
                                                         authorization_token))

        response = IPTVProxyUtility.make_http_request(http_session.get,
                                                      target_url,
                                                      params={
                                                          'token': authorization_token
                                                      },
                                                      headers=http_session.headers,
                                                      cookies=http_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            # noinspection PyUnresolvedReferences
            logger.trace(IPTVProxyUtility.assemble_response_from_log_message(response,
                                                                             is_content_binary=True))

            IPTVProxy.set_serviceable_client_parameter(client_uuid,
                                                       'last_requested_ts_file_path',
                                                       re.sub(r'(/.*)?(/.*\.ts)',
                                                              r'\2',
                                                              requested_path).replace('_', '/')[1:])

            return response.content
        else:
            logger.error(IPTVProxyUtility.assemble_response_from_log_message(response))

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
            client_ip_address_type = IPTVProxyUtility.determine_ip_address_type(client_ip_address)
            server_hostname = IPTVProxyConfiguration.get_configuration_parameter(
                'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
            server_port = IPTVProxyConfiguration.get_configuration_parameter(
                'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure else ''))

            playlist_m3u8 = ['#EXTM3U x-tvg-url="{0}://{1}:{2}/live/vadertreams/epg.xml"\n'.format(
                'https' if is_server_secure else 'http',
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
               'protocol={6}'.format('https' if is_server_secure else 'http',
                                     server_hostname,
                                     server_port,
                                     channel_number,
                                     client_uuid,
                                     urllib.parse.quote(http_token) if http_token else '',
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

        if playlist_protocol not in VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES:
            playlist_protocol = IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_PLAYLIST_PROTOCOL')

        if playlist_type not in VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES:
            playlist_type = IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_PLAYLIST_TYPE')

        tracks = {}

        db = VaderStreamsDB()
        epg = db.retrieve(['epg'])

        for channel in epg.values():
            track_information = []

            channel_icon = channel.icon_url.format(
                's' if is_server_secure else '',
                server_hostname,
                server_port,
                '?http_token={0}'.format(urllib.parse.quote(http_token)) if http_token else '').replace(
                ' ', '%20') if channel.icon_url else ''
            channel_group = channel.group
            channel_id = channel.id
            channel_name = channel.name
            channel_number = channel.number

            track_information.append(
                '#EXTINF:-1 group-title="{0}" '
                'tvg-id="{1}" '
                'tvg-name="{2}" '
                'tvg-logo="{3}" '
                'channel-id="{4}",{2}\n'.format(channel_group,
                                                channel_id,
                                                channel_name,
                                                channel_icon,
                                                channel_number))

            if playlist_type == 'dynamic':
                generate_playlist_m3u8_track_url_mapping = dict(channel_number=channel_number,
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
                        channel_number,
                        'm3u8' if playlist_protocol == 'hls' else 'ts',
                        cls._calculate_token()))

            tracks[channel_name] = ''.join(track_information)

        db.close()

        return [tracks[channel_name] for channel_name in sorted(tracks, key=lambda channel_name_: channel_name_.lower())]

    @classmethod
    def get_supported_protocols(cls):
        return VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES

    @classmethod
    def initialize(cls):
        password_in_configuration_file = IPTVProxyConfiguration.get_configuration_parameter('VADER_STREAMS_PASSWORD')
        encrypted_password = IPTVProxySecurityManager.scrub_password(cls.__name__, password_in_configuration_file)

        if password_in_configuration_file != encrypted_password:
            IPTVProxyConfiguration.update_configuration_file('VaderStreams', 'password', encrypted_password)
            IPTVProxyConfiguration.set_configuration_parameter('VADER_STREAMS_PASSWORD', encrypted_password)

    @classmethod
    def terminate(cls):
        pass

    @classmethod
    def set_do_reduce_hls_stream_delay(cls, do_reduce_hls_stream_delay):
        cls._do_reduce_hls_stream_delay = do_reduce_hls_stream_delay
