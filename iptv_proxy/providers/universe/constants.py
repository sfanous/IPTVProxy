class UniverseConstants(object):
    __slots__ = []

    DB_FILE_NAME = 'universe.db'
    DEFAULT_EPG_SOURCE = 'universe'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'Universe'
    TEMPORARY_DB_FILE_NAME = 'universe_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'universe']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
