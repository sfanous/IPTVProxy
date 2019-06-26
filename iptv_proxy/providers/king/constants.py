class KingConstants(object):
    __slots__ = []

    BASE_URL = 'http://king-tv.net:8080/'
    DB_FILE_NAME = 'king.db'
    DEFAULT_EPG_SOURCE = 'king'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'King'
    TEMPORARY_DB_FILE_NAME = 'king_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'king']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
