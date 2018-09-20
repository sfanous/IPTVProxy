import logging

from .constants import VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES
from .constants import VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES
from .constants import VALID_VADER_STREAMS_SERVER_VALUES

logger = logging.getLogger(__name__)


class VaderStreamsValidations():
    __slots__ = []

    @classmethod
    def is_valid_password(cls, password):
        return len(password)

    @classmethod
    def is_valid_server(cls, server):
        is_valid_smooth_streams_server = True

        if server not in VALID_VADER_STREAMS_SERVER_VALUES:
            is_valid_smooth_streams_server = False

        return is_valid_smooth_streams_server

    @classmethod
    def is_valid_playlist_protocol(cls, playlist_protocol):
        is_valid_playlist_protocol = True

        if playlist_protocol not in VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES:
            is_valid_playlist_protocol = False

        return is_valid_playlist_protocol

    @classmethod
    def is_valid_playlist_type(cls, playlist_type):
        is_valid_playlist_type = True

        if playlist_type not in VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES:
            is_valid_playlist_type = False

        return is_valid_playlist_type

    @classmethod
    def is_valid_username(cls, username):
        return len(username)
