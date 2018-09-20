import os

CACHE_TIME_TO_LIVE = 60
CHANNEL_ICONS_DIRECTORY_PATH = os.path.join(os.path.abspath('resources'), 'icons', 'channels')
DEFAULT_CHANNEL_ICON_FILE_PATH = os.path.join(os.path.abspath('resources'), 'icons', 'channels', '0.png')
DEFAULT_CONFIGURATION_FILE_PATH = os.path.abspath('iptv_proxy.ini')
DEFAULT_DB_DIRECTORY_PATH = os.path.abspath('db')
DEFAULT_DB_FILE_PATH = os.path.join(DEFAULT_DB_DIRECTORY_PATH, 'iptv_proxy_db.fs')
DEFAULT_HOSTNAME_LOOPBACK = 'localhost'
DEFAULT_LOGGING_LEVEL = 'INFO'
DEFAULT_LOG_DIRECTORY_PATH = os.path.abspath('logs')
DEFAULT_LOG_FILE_PATH = os.path.join(DEFAULT_LOG_DIRECTORY_PATH, 'iptv_proxy.log')
DEFAULT_RECORDINGS_DIRECTORY_PATH = os.path.abspath('recordings')
DEFAULT_SSL_DIRECTORY_PATH = os.path.abspath('ssl')
DEFAULT_SSL_CERTIFICATE_FILE_PATH = os.path.join(DEFAULT_SSL_DIRECTORY_PATH, 'certificate', 'iptv_proxy.pem')
DEFAULT_SSL_KEY_FILE_PATH = os.path.join(DEFAULT_SSL_DIRECTORY_PATH, 'key', 'iptv_proxy.pem')
DEFAULT_STREAMING_PROTOCOL = 'hls'
ERROR_HTML_TEMPLATES = {
    'errors.html.st': None
}
ICONS_DIRECTORY_PATH = os.path.join(os.path.abspath('resources'), 'icons')
INDEX_HTML_TEMPLATES = {
    'iptv_proxy_script.js.st': None,
    'index.html.st': None,
    'guide_group_select_option.html.st': None,
    'guide_div.html.st': None,
    'channel_li.html.st': None,
    'channel_programs_li.html.st': None,
    'date_li.html.st': None,
    'date_programs_li.html.st': None,
    'program_li.html.st': None,
    'separator_li.html.st': None,
    'alert_li.html.st': None,
    'buttons_li.html.st': None,
    'date_separator_li.html.st': None,
    'recordings_table_row.html.st': None
}
LOGIN_HTML_TEMPLATES = {
    'login.html.st': None
}
MAXIMUM_NUMBER_OF_CHANGED_OBJECTS = 1024
OPTIONAL_SETTINGS_FILE_PATH = os.path.abspath('iptv_proxy_optional_settings.json')
RESOURCES_DIRECTORY_PATH = os.path.abspath('resources')
TEMPLATES_DIRECTORY_PATH = os.path.abspath('templates')
TRACE = 5
VALID_LOGGING_LEVEL_VALUES = ['ERROR', 'INFO', 'DEBUG', 'TRACE']
VERSION = '5.0.0'
XML_TV_TEMPLATES = {
    'tv_header.xml.st': None,
    'channel.xml.st': None,
    'programme.xml.st': None,
    'tv_footer.xml.st': None,
}
