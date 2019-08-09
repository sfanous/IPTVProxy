class HydrogenConstants(object):
    __slots__ = []

    BASE_URL = 'http://m3u.hydr0.io:25461/'
    DB_FILE_NAME = 'hydrogen.db'
    DEFAULT_EPG_SOURCE = 'hydrogen'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'Hydrogen'
    TEMPORARY_DB_FILE_NAME = 'hydrogen_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'hydrogen']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
