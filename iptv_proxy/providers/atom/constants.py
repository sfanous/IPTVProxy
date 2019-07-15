class AtomConstants(object):
    __slots__ = []

    BASE_URL = 'http://atom.geekgalaxy.com:83/'
    DB_FILE_NAME = 'atom.db'
    DEFAULT_EPG_SOURCE = 'atom'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    PROVIDER_NAME = 'Atom'
    TEMPORARY_DB_FILE_NAME = 'atom_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'atom']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']

    _provider_name = PROVIDER_NAME.lower()
