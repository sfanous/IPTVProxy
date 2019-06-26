class VaderStreamsConstants(object):
    __slots__ = []

    BASE_URL = 'http://vapi.vaders.tv/'
    CATEGORIES_JSON_FILE_NAME = 'categories.json'
    CATEGORIES_PATH = 'epg/categories'
    CHANNELS_JSON_FILE_NAME = 'channels.json'
    CHANNELS_PATH = 'epg/channels'
    DB_FILE_NAME = 'vaderstreams.db'
    DEFAULT_EPG_SOURCE = 'vaderstreams'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    EPG_BASE_URL = 'http://vaders.tv/'
    JSON_EPG_TIME_DELTA_HOURS = 1
    MATCHCENTER_SCHEDULE_JSON_FILE_NAME = 'schedule.json'
    MATCHCENTER_SCHEDULE_PATH = 'mc/schedule'
    PROVIDER_NAME = 'VaderStreams'
    TEMPORARY_DB_FILE_NAME = 'vaderstreams_temp.db'
    VALID_EPG_SOURCE_VALUES = ['other', 'vaderstreams']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']
    VALID_SERVER_VALUES = ['auto']
    XML_EPG_FILE_NAME = 'p2.xml.gz'

    _provider_name = PROVIDER_NAME.lower()
