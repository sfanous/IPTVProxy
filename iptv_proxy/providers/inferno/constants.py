class InfernoConstants(object):
    __slots__ = []

    DB_FILE_NAME = 'inferno.db'
    DEFAULT_EPG_SOURCE = 'inferno'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'Inferno'
    TEMPORARY_DB_FILE_NAME = 'inferno_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'inferno']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
