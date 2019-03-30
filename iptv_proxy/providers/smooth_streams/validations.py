import logging

import requests

from .constants import VALID_SMOOTH_STREAMS_EPG_SOURCE_VALUES
from .constants import VALID_SMOOTH_STREAMS_PLAYLIST_PROTOCOL_VALUES
from .constants import VALID_SMOOTH_STREAMS_PLAYLIST_TYPE_VALUES
from .constants import VALID_SMOOTH_STREAMS_SERVER_VALUES
from .constants import VALID_SMOOTH_STREAMS_SERVICE_VALUES

logger = logging.getLogger(__name__)


class SmoothStreamsValidations(object):
    __slots__ = []

    @classmethod
    def is_valid_epg_source(cls, epg_source):
        is_valid_smooth_streams_epg_source = True

        if epg_source not in VALID_SMOOTH_STREAMS_EPG_SOURCE_VALUES:
            is_valid_smooth_streams_epg_source = False

        return is_valid_smooth_streams_epg_source

    @classmethod
    def is_valid_epg_url(cls, epg_url):
        is_valid_smooth_streams_epg_url = True

        try:
            requests.head(epg_url)
        except requests.RequestException:
            is_valid_smooth_streams_epg_url = False

        return is_valid_smooth_streams_epg_url

    @classmethod
    def is_valid_password(cls, password):
        return len(password)

    @classmethod
    def is_valid_playlist_protocol(cls, playlist_protocol):
        is_valid_playlist_protocol = True

        if playlist_protocol not in VALID_SMOOTH_STREAMS_PLAYLIST_PROTOCOL_VALUES:
            is_valid_playlist_protocol = False

        return is_valid_playlist_protocol

    @classmethod
    def is_valid_playlist_type(cls, playlist_type):
        is_valid_playlist_type = True

        if playlist_type not in VALID_SMOOTH_STREAMS_PLAYLIST_TYPE_VALUES:
            is_valid_playlist_type = False

        return is_valid_playlist_type

    @classmethod
    def is_valid_server(cls, server):
        is_valid_smooth_streams_server = True

        if server not in VALID_SMOOTH_STREAMS_SERVER_VALUES:
            is_valid_smooth_streams_server = False

        return is_valid_smooth_streams_server

    @classmethod
    def is_valid_service(cls, service):
        is_valid_smooth_streams_service = True

        if service not in VALID_SMOOTH_STREAMS_SERVICE_VALUES:
            is_valid_smooth_streams_service = False

        return is_valid_smooth_streams_service

    @classmethod
    def is_valid_username(cls, username):
        return len(username)
