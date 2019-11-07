class CrystalClearConstants(object):
    __slots__ = []

    DB_FILE_NAME = 'crystalclear.db'
    DEFAULT_EPG_SOURCE = 'crystalclear'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'CrystalClear'
    TEMPORARY_DB_FILE_NAME = 'crystalclear_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'crystalclear']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
