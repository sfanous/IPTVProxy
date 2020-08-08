import base64
import json
import logging
import re
import urllib.parse
from datetime import datetime

import pytz
import requests
from rwlock import RWLock

from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.providers.iptv_provider.api import Provider
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants
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
            'username': Configuration.get_configuration_parameter(
                'VADERSTREAMS_USERNAME'
            ),
            'password': SecurityManager.decrypt_password(
                Configuration.get_configuration_parameter('VADERSTREAMS_PASSWORD')
            ).decode(),
        }

        return base64.b64encode(
            json.dumps(credentials, separators=(',', ':')).encode()
        ).decode()

    @classmethod
    def _generate_playlist_m3u8_static_track_url(cls, track_information, **kwargs):
        channel_number = kwargs['channel_number']
        playlist_protocol = kwargs['playlist_protocol']
        authorization_token = kwargs['authorization_token']

        track_information.append(
            'http://vapi.vaders.tv/play/{0:02}.{1}?token={2}\n'.format(
                channel_number,
                'm3u8' if playlist_protocol == 'hls' else 'ts',
                authorization_token,
            )
        )

    @classmethod
    def _initialize(cls, **kwargs):
        pass

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_do_reduce_hls_stream_delay(
                OptionalSettings.get_optional_settings_parameter(
                    'reduce_vaderstreams_delay'
                )
            )
        except KeyError:
            pass

    @classmethod
    def _retrieve_fresh_authorization_token(cls):
        return cls._calculate_token()

    @classmethod
    def _terminate(cls, **kwargs):
        pass

    @classmethod
    def download_chunks_m3u8(
        cls,
        client_ip_address,
        client_uuid,
        requested_path,
        requested_query_string_parameters,
    ):
        authorization_token = requested_query_string_parameters.get(
            'authorization_token'
        )
        channel_name = requested_query_string_parameters.get('channel_name')
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        port = requested_query_string_parameters.get('port')
        server = requested_query_string_parameters.get('server')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(
            client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc)
        )

        requests_session = requests.Session()

        target_url = 'http://{0}{1}/{2}/tracks-v1a1/mono.m3u8'.format(
            server
            if re.match(r"\A\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\Z", server)
            else '{0}.vaders.tv'.format(server),
            port if port != ':80' else '',
            channel_name,
        )

        logger.debug(
            'Proxying request\n'
            'Source IP      => %s\n'
            'Requested path => %s\n'
            '  Parameters\n'
            '    channel_name   => %s\n'
            '    channel_number => %s\n'
            '    client_uuid    => %s\n'
            '    port           => %s\n'
            '    server         => %s\n'
            'Target path    => %s\n'
            '  Parameters\n'
            '    token          => %s',
            client_ip_address,
            requested_path,
            channel_name,
            channel_number,
            client_uuid,
            port,
            server,
            target_url,
            authorization_token,
        )

        response = Utility.make_http_request(
            requests_session.get,
            target_url,
            params={'token': authorization_token},
            headers=requests_session.headers,
            cookies=requests_session.cookies.get_dict(),
        )

        if response.status_code == requests.codes.OK:
            logger.trace(
                Utility.assemble_response_from_log_message(
                    response, is_content_text=True, do_print_content=True
                )
            )

            with cls._do_reduce_hls_stream_delay_lock.reader_lock:
                if cls._do_reduce_hls_stream_delay:
                    chunks_m3u8 = cls._reduce_hls_stream_delay(
                        response.text,
                        client_uuid,
                        channel_number,
                        number_of_segments_to_keep=3,
                    )
                else:
                    chunks_m3u8 = response.text

            IPTVProxy.set_serviceable_client_parameter(
                client_uuid, 'last_requested_channel_number', channel_number
            )

            match = re.search(
                r'http://(.*)\.vaders\.tv(:\d+)?/(.*)/tracks-v1a1/.*', chunks_m3u8
            )
            if match is None:
                match = re.search(
                    r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?/(.*)/tracks-v1a1/.*',
                    chunks_m3u8,
                )
            if match is not None:
                server = match.group(1)
                port = (
                    match.group(2)
                    if match.group(2) is not None and len(match.groups()) == 3
                    else ':80'
                )
                channel_name = (
                    match.group(3) if len(match.groups()) == 3 else match.group(2)
                )

            chunks_m3u8 = re.sub('.*/tracks-v1a1/', '', chunks_m3u8)

            return re.sub(
                r'.ts\?token=(.*)',
                r'.ts?'
                r'authorization_token=\1&'
                'channel_name={0}&'
                'channel_number={1}&'
                'client_uuid={2}&'
                'http_token={3}&'
                'port={4}&'
                'server={5}'.format(
                    urllib.parse.quote(channel_name),
                    channel_number,
                    client_uuid,
                    urllib.parse.quote(http_token) if http_token else '',
                    urllib.parse.quote(port),
                    urllib.parse.quote(server),
                ),
                chunks_m3u8.replace('/', '_'),
            )

        logger.error(Utility.assemble_response_from_log_message(response))

        response.raise_for_status()

    @classmethod
    def download_playlist_m3u8(
        cls,
        client_ip_address,
        client_uuid,
        requested_path,
        requested_query_string_parameters,
    ):
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        protocol = requested_query_string_parameters.get('protocol')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(
            client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc)
        )

        authorization_token = cls._calculate_token()

        if protocol == 'hls':
            requests_session = requests.Session()

            target_url = 'http://vapi.vaders.tv/play/{0}.m3u8'.format(channel_number)

            logger.debug(
                'Proxying request\n'
                'Source IP      => %s\n'
                'Requested path => %s\n'
                '  Parameters\n'
                '    channel_number => %s\n'
                '    client_uuid    => %s\n'
                '    protocol       => %s\n'
                'Target path    => %s\n'
                '  Parameters\n'
                '    token          => %s',
                client_ip_address,
                requested_path,
                channel_number,
                client_uuid,
                protocol,
                target_url,
                authorization_token,
            )

            response = Utility.make_http_request(
                requests_session.get,
                target_url,
                params={'token': authorization_token},
                headers=requests_session.headers,
                cookies=requests_session.cookies.get_dict(),
            )

            if response.status_code == requests.codes.OK:
                logger.trace(
                    Utility.assemble_response_from_log_message(
                        response, is_content_text=True, do_print_content=True
                    )
                )

                match = re.search(
                    r'http://(.*)\.vaders\.tv(:\d+)?/(.*)/tracks-v1a1/.*', response.text
                )
                if match is None:
                    match = re.search(
                        r'http://(.*)\.vaders\.tv(:\d+)?/(.*)/index.m3u8.*',
                        response.request.url,
                    )
                    if match is None:
                        match = re.search(
                            r'http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?/(.*)/index.m3u8.*',
                            response.request.url,
                        )

                server = match.group(1)
                port = (
                    match.group(2)
                    if match.group(2) is not None and len(match.groups()) == 3
                    else ':80'
                )
                channel_name = (
                    match.group(3) if len(match.groups()) == 3 else match.group(2)
                )

                return re.sub(
                    r'tracks-v1a1/mono.m3u8\?token=(.*)',
                    'chunks.m3u8?'
                    r'authorization_token=\1&'
                    'channel_name={0}&'
                    'channel_number={1}&'
                    'client_uuid={2}&'
                    'http_token={3}&'
                    'port={4}&'
                    'server={5}'.format(
                        urllib.parse.quote(channel_name),
                        channel_number,
                        client_uuid,
                        urllib.parse.quote(http_token) if http_token else '',
                        urllib.parse.quote(port),
                        urllib.parse.quote(server),
                    ),
                    re.sub('.*/tracks-v1a1/', 'tracks-v1a1/', response.text),
                )

            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()
        elif protocol == 'mpegts':
            return (
                '#EXTM3U\n'
                '#EXTINF:-1 ,{0}\n'
                'http://vapi.vaders.tv/play/{1}.ts?'
                'token={2}'.format(
                    VaderStreamsEPG.get_channel_name(int(channel_number)),
                    channel_number,
                    authorization_token,
                )
            )

    @classmethod
    def download_ts_file(
        cls,
        client_ip_address,
        client_uuid,
        requested_path,
        requested_query_string_parameters,
    ):
        authorization_token = requested_query_string_parameters.get(
            'authorization_token'
        )
        channel_name = requested_query_string_parameters.get('channel_name')
        channel_number = requested_query_string_parameters.get('channel_number')
        port = requested_query_string_parameters.get('port')
        server = requested_query_string_parameters.get('server')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        IPTVProxy.set_serviceable_client_parameter(
            client_uuid, 'last_request_date_time_in_utc', datetime.now(pytz.utc)
        )

        requests_session = requests.Session()

        target_url = 'http://{0}{1}/{2}{3}'.format(
            server
            if re.match(r"\A\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\Z", server)
            else '{0}.vaders.tv'.format(server),
            port if port != ':80' else '',
            channel_name,
            re.sub(r'(/.*)?(/.*\.ts)', r'\2', requested_path).replace('_', '/'),
        )

        logger.debug(
            'Proxying request\n'
            'Source IP      => %s\n'
            'Requested path => %s\n'
            '  Parameters\n'
            '    channel_name   => %s\n'
            '    channel_number => %s\n'
            '    client_uuid    => %s\n'
            '    port           => %s\n'
            '    server         => %s\n'
            'Target path    => %s\n'
            '  Parameters\n'
            '    token          => %s',
            client_ip_address,
            requested_path,
            channel_name,
            channel_number,
            client_uuid,
            port,
            server,
            target_url,
            authorization_token,
        )

        response = Utility.make_http_request(
            requests_session.get,
            target_url,
            params={'token': authorization_token},
            headers=requests_session.headers,
            cookies=requests_session.cookies.get_dict(),
        )

        if response.status_code == requests.codes.OK:
            logger.trace(
                Utility.assemble_response_from_log_message(
                    response, is_content_binary=True
                )
            )

            IPTVProxy.set_serviceable_client_parameter(
                client_uuid,
                'last_requested_ts_file_path',
                re.sub(r'(/.*)?(/.*\.ts)', r'\2', requested_path).replace('_', '/')[1:],
            )

            return response.content

        logger.error(Utility.assemble_response_from_log_message(response))

        response.raise_for_status()

    @classmethod
    def set_do_reduce_hls_stream_delay(cls, do_reduce_hls_stream_delay):
        with cls._do_reduce_hls_stream_delay_lock.writer_lock:
            cls._do_reduce_hls_stream_delay = do_reduce_hls_stream_delay
