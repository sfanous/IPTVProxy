class SmoothStreamsConstants(object):
    DB_FILE_NAME = 'smoothstreams.db'
    DEFAULT_EPG_SOURCE = 'fog'
    DEFAULT_PLAYLIST_PROTOCOL = 'hls'
    DEFAULT_PLAYLIST_TYPE = 'dynamic'
    EPG_BASE_URL = 'https://guide.smoothstreams.tv/'
    EPG_FILE_NAME = 'feed-new-full.json'
    EPG_TIME_DELTA_HOURS = 1
    FOG_CHANNELS_JSON_FILE_NAME = 'channels.json'
    FOG_EPG_BASE_URL = 'https://guide.smoothstreams.tv/altepg/'
    FOG_EPG_TIME_DELTA_HOURS = 6
    FOG_EPG_XML_FILE_NAME = 'xmltv5.xml'
    PROVIDER_NAME = 'SmoothStreams'
    TEMPORARY_DB_FILE_NAME = 'smoothstreams_temp.db'
    VALID_EPG_SOURCE_VALUES = ['fog', 'other', 'smoothstreams']
    VALID_PLAYLIST_PROTOCOL_VALUES = ['hls', 'mpegts', 'rtmp']
    VALID_PLAYLIST_TYPE_VALUES = ['dynamic', 'static']
    VALID_SERVER_VALUES = ['dap', 'deu', 'deu-de', 'deu-nl', 'deu-nl1', 'deu-nl2', 'deu-nl3', 'deu-nl4',
                           'deu-nl5', 'deu-uk', 'deu-uk1', 'deu-uk2', 'dna', 'dnae', 'dnae1', 'dnae2',
                           'dnae3', 'dnae4', 'dnae6', 'dnaw', 'dnaw1', 'dnaw2', 'dnaw3', 'dnaw4'
                           ]
    VALID_SERVICE_VALUES = ['view247', 'viewmmasr', 'viewss', 'viewstvn']

    _provider_name = PROVIDER_NAME.lower()
