class VitalTVConstants(object):
    __slots__ = []

    DB_FILE_NAME = 'vitaltv.db'
    DEFAULT_EPG_SOURCE = 'vitaltv'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'VitalTV'
    TEMPORARY_DB_FILE_NAME = 'vitaltv_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'vitaltv']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
