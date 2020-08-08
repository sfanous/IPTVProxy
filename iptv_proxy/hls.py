import logging
import time
import urllib.parse

import math
import requests

from iptv_proxy.exceptions import HLSPlaylistDownloadError
from iptv_proxy.providers import ProvidersController

logger = logging.getLogger(__name__)


class HLSClient(object):
    __slots__ = ['_channel_number', '_id', '_provider_map_class', '_provider_name']

    def __init__(self, id_, provider_name, channel_number):
        self._id = id_
        self._provider_name = provider_name
        self._provider_map_class = ProvidersController.get_active_provider_map_class(
            provider_name
        )
        self._channel_number = channel_number

    def download_chunks_m3u8(self, chunks_url):
        for number_of_download_attempts in range(1, 11):
            try:
                chunks_url_components = urllib.parse.urlparse(chunks_url)
                chunks_query_string_parameters = dict(
                    urllib.parse.parse_qsl(chunks_url_components.query)
                )

                return self._provider_map_class.api_class().download_chunks_m3u8(
                    '127.0.0.1',
                    self._id,
                    chunks_url_components.path,
                    chunks_query_string_parameters,
                )
            except requests.exceptions.HTTPError:
                time_to_sleep_before_next_attempt = (
                    math.ceil(number_of_download_attempts / 2) * 2
                )

                logger.error(
                    'Attempt #{%s\n'
                    'Failed to download chunks.m3u8\n'
                    'Will try again in %s seconds',
                    number_of_download_attempts,
                    time_to_sleep_before_next_attempt,
                )

                time.sleep(time_to_sleep_before_next_attempt)
        else:
            logger.error('Exhausted attempts to download chunks.m3u8')

            raise HLSPlaylistDownloadError

    def download_playlist_m3u8(self):
        for number_of_download_attempts in range(1, 11):
            try:
                return self._provider_map_class.api_class().download_playlist_m3u8(
                    '127.0.0.1',
                    self._id,
                    '/live/{0}/playlist.m3u8'.format(self._provider_name),
                    dict(channel_number=self._channel_number, protocol='hls'),
                )
            except requests.exceptions.HTTPError:
                time_to_sleep_before_next_attempt = (
                    math.ceil(number_of_download_attempts / 5) * 5
                )

                logger.error(
                    'Attempt #%s\n'
                    'Failed to download playlist.m3u8\n'
                    'Will try again in %s seconds',
                    number_of_download_attempts,
                    time_to_sleep_before_next_attempt,
                )

                time.sleep(time_to_sleep_before_next_attempt)
        else:
            logger.error('Exhausted attempts to download playlist.m3u8')

            raise HLSPlaylistDownloadError

    def download_ts_file(self, segment_url):
        segment_url_components = urllib.parse.urlparse(segment_url)
        segment_query_string_parameters = dict(
            urllib.parse.parse_qsl(segment_url_components.query)
        )

        return self._provider_map_class.api_class().download_ts_file(
            '127.0.0.1',
            self._id,
            segment_url_components.path,
            segment_query_string_parameters,
        )
