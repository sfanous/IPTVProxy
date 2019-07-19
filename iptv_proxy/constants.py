import os
import sys

if getattr(sys, 'frozen', False):
    directory_containing_script = os.path.dirname(sys.executable)
else:
    directory_containing_script = sys.path[0]

CACHE_TIME_TO_LIVE = 60
CACHE_WAIT_TIME = 3
CHANNEL_ICONS_DIRECTORY_PATH = os.path.join(directory_containing_script, 'resources', 'icons', 'channels')
DEFAULT_CHANNEL_ICON_FILE_PATH = os.path.join(CHANNEL_ICONS_DIRECTORY_PATH, '0.png')
DEFAULT_CONFIGURATION_FILE_PATH = os.path.join(directory_containing_script, 'iptv_proxy.ini')
DEFAULT_DB_DIRECTORY_PATH = os.path.join(directory_containing_script, 'db')
DEFAULT_DB_FILE_PATH = os.path.join(DEFAULT_DB_DIRECTORY_PATH, 'iptv_proxy.db')
DEFAULT_HOSTNAME_LOOPBACK = 'localhost'
DEFAULT_LOGGING_CONFIGURATION = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'MultiLine': {
            'format': '%(asctime)s %(name)-50s %(funcName)-40s %(levelname)-8s %(message)s',
            '()': 'iptv_proxy.formatters.MultiLineFormatter',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'MultiLine',
            'class': 'logging.StreamHandler'
        },
        'rotating_file': {
            'level': 'INFO',
            'formatter': 'MultiLine',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.join(directory_containing_script, 'logs'), 'iptv_proxy.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10
        }
    },
    'loggers': {
        'iptv_proxy': {
            'handlers': ['console', 'rotating_file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
DEFAULT_LOG_DIRECTORY_PATH = os.path.join(directory_containing_script, 'logs')
DEFAULT_LOG_FILE_PATH = os.path.join(DEFAULT_LOG_DIRECTORY_PATH, 'iptv_proxy.log')
DEFAULT_OPTIONAL_SETTINGS_FILE_PATH = os.path.join(directory_containing_script, 'iptv_proxy_optional_settings.json')
DEFAULT_RECORDINGS_DIRECTORY_PATH = os.path.join(directory_containing_script, 'recordings')
DEFAULT_SSL_DIRECTORY_PATH = os.path.join(directory_containing_script, 'ssl')
DEFAULT_SSL_CERTIFICATE_FILE_PATH = os.path.join(DEFAULT_SSL_DIRECTORY_PATH, 'certificate', 'iptv_proxy.pem')
DEFAULT_SSL_KEY_FILE_PATH = os.path.join(DEFAULT_SSL_DIRECTORY_PATH, 'key', 'iptv_proxy.pem')
DEFAULT_STREAMING_PROTOCOL = 'hls'
HTTP_CHUNK_SIZE = 8192
ICONS_DIRECTORY_PATH = os.path.join(directory_containing_script, 'resources', 'icons')
LOGGING_CONFIGURATION_FILE_PATH = os.path.join(directory_containing_script, 'iptv_proxy_logging_configuration.json')
RESOURCES_DIRECTORY_PATH = os.path.join(directory_containing_script, 'resources')
TEMPLATES_BYTECODE_CACHE_DIRECTORY_PATH = os.path.join(directory_containing_script, 'templates', 'byte_code_cache')
TEMPLATES_DIRECTORY_PATH = os.path.join(directory_containing_script, 'templates')
TRACE = 5
VERSION = '7.6.8'
