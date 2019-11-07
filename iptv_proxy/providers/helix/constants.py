class HelixConstants(object):
    __slots__ = []

    DB_FILE_NAME = 'helix.db'
    DEFAULT_EPG_SOURCE = 'helix'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'Helix'
    TEMPORARY_DB_FILE_NAME = 'helix_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'helix']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
