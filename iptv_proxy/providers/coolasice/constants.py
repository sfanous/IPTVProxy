class CoolAsIceConstants(object):
    BASE_URL = 'http://bangobongobingo.com/'
    DB_FILE_NAME = 'coolasice.db'
    DEFAULT_EPG_SOURCE = 'coolasice'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    EPG_PATH = 'xmltv.php'
    M3U8_PLAYLIST_FILE_NAME = 'tv_channels_{0}.m3u'
    M3U8_PLAYLIST_PATH = 'get.php'
    PROVIDER_NAME = 'CoolAsIce'
    TEMPORARY_DB_FILE_NAME = 'coolasice_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'coolasice']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']
    XML_EPG_FILE_NAME = 'xmltv.xml'

    _provider_name = PROVIDER_NAME.lower()
