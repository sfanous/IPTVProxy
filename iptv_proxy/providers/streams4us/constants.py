class Streams4UsConstants(object):
    __slots__ = []

    BASE_URL = 'http://its.streamsforus.net:8000/'
    DB_FILE_NAME = 'streams4us.db'
    DEFAULT_EPG_SOURCE = 'streams4us'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'Streams4Us'
    TEMPORARY_DB_FILE_NAME = 'streams4u_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'streams4us']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
