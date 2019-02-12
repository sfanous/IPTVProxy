import copy
import logging
import os
import sys
import traceback
from datetime import datetime
from threading import RLock

import pytz
from configobj import ConfigObj
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .constants import DEFAULT_HOSTNAME_LOOPBACK
from .constants import DEFAULT_LOGGING_LEVEL
from .constants import VALID_LOGGING_LEVEL_VALUES
from .providers.smooth_streams.configuration import SmoothStreamsConfiguration
from .providers.vader_streams.configuration import VaderStreamsConfiguration
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class IPTVProxyConfiguration(object):
    __slots__ = []

    _configuration = {}
    _configuration_file_path = None
    _configuration_file_watchdog_observer = None
    _lock = RLock()
    _previous_configuration = {}
    _providers = {}

    @classmethod
    def _backup_configuration(cls):
        with cls._lock:
            cls._previous_configuration = copy.deepcopy(cls._configuration)

    @classmethod
    def _set_configuration(cls, configuration):
        with cls._lock:
            cls._configuration = configuration

    @classmethod
    def get_configuration_copy(cls):
        with cls._lock:
            return copy.deepcopy(cls._configuration)

    @classmethod
    def get_configuration_file_path(cls):
        return cls._configuration_file_path

    @classmethod
    def get_configuration_parameter(cls, parameter_name):
        with cls._lock:
            return cls._configuration[parameter_name]

    @classmethod
    def get_provider(cls, provider_name):
        with cls._lock:
            return cls._providers[provider_name]

    @classmethod
    def get_providers(cls):
        with cls._lock:
            return copy.copy(cls._providers)

    @classmethod
    def get_providers_name(cls):
        with cls._lock:
            return tuple(cls._providers.keys())

    @classmethod
    def is_provider_in_providers(cls, provider):
        with cls._lock:
            if provider in cls._providers:
                return True

            return False

    @classmethod
    def join_configuration_file_watchdog_observer(cls):
        cls._configuration_file_watchdog_observer.join()

    @classmethod
    def process_configuration_file_updates(cls):
        # <editor-fold desc="Detect and handle SERVER_PASSWORD change">
        if cls.get_configuration_parameter('SERVER_PASSWORD') != cls._previous_configuration['SERVER_PASSWORD']:
            from .http_server import IPTVProxyHTTPRequestHandler

            IPTVProxyHTTPRequestHandler.reset_active_sessions()

            logger.debug('Detected a change in the password option within the [Server] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Purged all user HTTP/S sessions'.format(cls._previous_configuration['SERVER_PASSWORD'],
                                                                  cls.get_configuration_parameter('SERVER_PASSWORD')))
        # </editor-fold>

        # <editor-fold desc="Detect and handle SERVER_HOSTNAME_<LOOPBACK,PRIVATE,PUBLIC> change">
        hostname_updated = False
        https_server_restarted = False
        message_to_log = []

        if (cls.get_configuration_parameter('SERVER_HOSTNAME_LOOPBACK') !=
                cls._previous_configuration['SERVER_HOSTNAME_LOOPBACK']):
            hostname_updated = True

            message_to_log.append('Detected a change in the loopback option within the [Hostnames] section\n'
                                  'Old value => {0}\n'
                                  'New value => {1}'.format(cls._previous_configuration['SERVER_HOSTNAME_LOOPBACK'],
                                                            cls.get_configuration_parameter(
                                                                'SERVER_HOSTNAME_LOOPBACK')))
        if (cls.get_configuration_parameter('SERVER_HOSTNAME_PRIVATE') !=
                cls._previous_configuration['SERVER_HOSTNAME_PRIVATE']):
            if hostname_updated:
                message_to_log.append('\n\n')
            else:
                hostname_updated = True

            message_to_log.append('Detected a change in the private option within the [Hostnames] section\n'
                                  'Old value => {0}\n'
                                  'New value => {1}'.format(cls._previous_configuration['SERVER_HOSTNAME_PRIVATE'],
                                                            cls.get_configuration_parameter('SERVER_HOSTNAME_PRIVATE')))
        if (cls.get_configuration_parameter('SERVER_HOSTNAME_PUBLIC') !=
                cls._previous_configuration['SERVER_HOSTNAME_PUBLIC']):
            if hostname_updated:
                message_to_log.append('\n\n')
            else:
                hostname_updated = True

            message_to_log.append('Detected a change in the public option within the [Hostnames] section\n'
                                  'Old value => {0}\n'
                                  'New value => {1}'.format(cls._previous_configuration['SERVER_HOSTNAME_PUBLIC'],
                                                            cls.get_configuration_parameter('SERVER_HOSTNAME_PUBLIC')))
        if hostname_updated:
            from .security import IPTVProxySecurityManager

            if IPTVProxySecurityManager.get_auto_generate_self_signed_certificate():
                IPTVProxySecurityManager.generate_self_signed_certificate()

                from .controller import IPTVProxyController

                IPTVProxyController.shutdown_https_server()
                IPTVProxyController.start_https_server()

                message_to_log.append('\n\nRestarted HTTPS server')
                logger.debug(''.join(message_to_log))
            else:
                logger.debug(''.join(message_to_log))
        # </editor-fold>

        # <editor-fold desc="Detect and handle SERVER_HTTP_PORT change">
        if cls.get_configuration_parameter('SERVER_HTTP_PORT') != cls._previous_configuration['SERVER_HTTP_PORT']:
            from .controller import IPTVProxyController

            IPTVProxyController.shutdown_http_server()
            IPTVProxyController.start_http_server()

            logger.debug('Detected a change in the http option within the [Ports] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Restarted HTTP server'.format(cls._previous_configuration['SERVER_HTTP_PORT'],
                                                        cls.get_configuration_parameter('SERVER_HTTP_PORT')))
        # </editor-fold>

        # <editor-fold desc="Detect and handle SERVER_HTTPS_PORT change">
        if cls.get_configuration_parameter('SERVER_HTTPS_PORT') != cls._previous_configuration['SERVER_HTTPS_PORT']:
            if not https_server_restarted:
                from .controller import IPTVProxyController

                IPTVProxyController.shutdown_https_server()
                IPTVProxyController.start_https_server()

                logger.debug('Detected a change in the https option within the [Ports] section\n'
                             'Old value => {0}\n'
                             'New value => {1}\n\n'
                             'Restarted HTTPS server'.format(cls._previous_configuration['SERVER_HTTPS_PORT'],
                                                             cls.get_configuration_parameter('SERVER_HTTPS_PORT')))
            else:
                logger.debug('Detected a change in the https option within the [Ports] section\n'
                             'Old value => {0}\n'
                             'New value => {1}'.format(cls._previous_configuration['SERVER_HTTPS_PORT'],
                                                       cls.get_configuration_parameter('SERVER_HTTPS_PORT')))
        # </editor-fold>

        SmoothStreamsConfiguration.process_configuration_file_updates(cls._configuration, cls._previous_configuration)
        VaderStreamsConfiguration.process_configuration_file_updates(cls._configuration, cls._previous_configuration)

        # <editor-fold desc="Detect and change LOGGING_LEVEL change">
        if cls.get_configuration_parameter('LOGGING_LEVEL') != cls._previous_configuration['LOGGING_LEVEL']:
            try:
                IPTVProxyUtility.set_logging_level(
                    getattr(logging, cls.get_configuration_parameter('LOGGING_LEVEL').upper()))
            except AttributeError:
                (type_, value_, traceback_) = sys.exc_info()
                logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

            logger.debug('Detected a change in the level option within the [Logging] section\n'
                         'Old value => {0}\n'
                         'New value => {1}'.format(cls._previous_configuration['LOGGING_LEVEL'],
                                                   cls.get_configuration_parameter('LOGGING_LEVEL')))
        # </editor-fold>

    @classmethod
    def read_configuration_file(cls, initial_read=True):
        cls._backup_configuration()

        try:
            configuration_object = ConfigObj(cls._configuration_file_path,
                                             file_error=True,
                                             indent_type='',
                                             interpolation=False,
                                             raise_errors=True,
                                             write_empty_values=True)

            non_defaultable_error = False
            error_messages = []

            password = None
            hostname_loopback = DEFAULT_HOSTNAME_LOOPBACK
            hostname_private = None
            hostname_public = None
            http_port = None
            https_port = None
            logging_level = DEFAULT_LOGGING_LEVEL

            # <editor-fold desc="Read Server section">
            try:
                server_section = configuration_object['Server']

                try:
                    password = server_section['password']
                except KeyError:
                    non_defaultable_error = True

                    error_messages.append('Could not find a password option within the [Server] section\n')

                try:
                    server_hostnames_section = server_section['Hostnames']

                    # <editor-fold desc="Read loopback option">
                    try:
                        hostname_loopback = server_hostnames_section['loopback']

                        if not IPTVProxyUtility.is_valid_loopback_hostname(hostname_loopback):
                            error_messages.append('The loopback option within the [Hostnames] section specifies an '
                                                  'invalid loopback hostname\n'
                                                  'Defaulting to {0}\n'.format(DEFAULT_HOSTNAME_LOOPBACK))
                    except KeyError:
                        hostname_loopback = DEFAULT_HOSTNAME_LOOPBACK

                        error_messages.append('The loopback option within the [Hostnames] section is missing\n'
                                              'Defaulting to {0}\n'.format(DEFAULT_HOSTNAME_LOOPBACK))
                    # </editor-fold>

                    # <editor-fold desc="Read private option">
                    do_determine_private_ip_address = False

                    try:
                        hostname_private = server_hostnames_section['private']

                        if not IPTVProxyUtility.is_valid_private_hostname(hostname_private):
                            if IPTVProxyUtility.is_valid_public_hostname(hostname_private):
                                error_messages.append('The private option within the [Hostnames] section specifies a '
                                                      'public IP address\n')
                            else:
                                do_determine_private_ip_address = True
                    except KeyError:
                        do_determine_private_ip_address = True
                    # </editor-fold>

                    # <editor-fold desc="Read public option">
                    do_determine_public_ip_address = False

                    try:
                        hostname_public = server_hostnames_section['public']
                        if not IPTVProxyUtility.is_valid_public_hostname(hostname_public):
                            do_determine_public_ip_address = True
                    except KeyError:
                        do_determine_public_ip_address = True
                    # </editor-fold>
                except KeyError:
                    error_messages.append('Could not find a [Hostnames] section within the [Server] section\n')

                    hostname_loopback = DEFAULT_HOSTNAME_LOOPBACK

                    do_determine_private_ip_address = True
                    do_determine_public_ip_address = True

                if do_determine_private_ip_address:
                    hostname_private = IPTVProxyUtility.determine_private_ip_address()

                    if hostname_private:
                        error_messages.append('The private option within the [Hostnames] section specifies an invalid '
                                              'private IP address\n'
                                              'Reverting to {0}\n'.format(hostname_private))

                if do_determine_public_ip_address:
                    hostname_public = IPTVProxyUtility.determine_public_ip_address()

                    if hostname_public:
                        error_messages.append('The public option within the [Hostnames] section specifies an invalid '
                                              'public IP address\n'
                                              'Reverting to {0}\n'.format(hostname_public))

                try:
                    server_ports_section = server_section['Ports']

                    # <editor-fold desc="Read http option">
                    try:
                        http_port = server_ports_section['http']
                        if not IPTVProxyUtility.is_valid_port_number(http_port):
                            non_defaultable_error = True

                            error_messages.append('The http option within the [Ports] section must be a number between '
                                                  '0 and 65535\n')
                    except KeyError:
                        non_defaultable_error = True

                        error_messages.append('Could not find an http option within the [Ports] section\n'
                                              'The http option within the [Ports] section must be a number between 0 '
                                              'and 65535\n')
                    # </editor-fold>

                    # <editor-fold desc="Read https option">
                    try:
                        https_port = server_ports_section['https']
                        if not IPTVProxyUtility.is_valid_port_number(https_port):
                            non_defaultable_error = True

                            error_messages.append('The https option within the [Ports] section must be a number '
                                                  'between 0 and 65535\n')
                    except KeyError:
                        non_defaultable_error = True

                        error_messages.append('Could not find an https option within the [Ports] section\n'
                                              'The https option within the [Ports] section must be a number between 0 '
                                              'and 65535\n')
                    # </editor-fold>
                except KeyError:
                    non_defaultable_error = True

                    error_messages.append('Could not find a [Ports] section within the [Server] section\n')
            except KeyError:
                non_defaultable_error = True

                error_messages.append('Could not find a [Server] section\n')
            # </editor-fold>

            # <editor-fold desc="Read SmoothStreams section">
            (is_valid_smooth_streams_section,
             smooth_streams_service,
             smooth_streams_server,
             smooth_streams_username,
             smooth_streams_password,
             smooth_streams_playlist_protocol,
             smooth_streams_playlist_type,
             smooth_streams_epg_source) = SmoothStreamsConfiguration.read_configuration_file(configuration_object,
                                                                                             error_messages)

            if is_valid_smooth_streams_section:
                from .providers.smooth_streams.api import SmoothStreams
                from .providers.smooth_streams.db import SmoothStreamsDB
                from .providers.smooth_streams.epg import SmoothStreamsEPG

                cls._providers[SmoothStreams.__name__.lower()] = {}
                cls._providers[SmoothStreams.__name__.lower()]['api'] = SmoothStreams()
                cls._providers[SmoothStreams.__name__.lower()]['db'] = SmoothStreamsDB
                cls._providers[SmoothStreams.__name__.lower()]['epg'] = SmoothStreamsEPG()
            else:
                from .providers.smooth_streams.api import SmoothStreams

                if SmoothStreams.__name__.lower() in cls._providers:
                    cls._providers[SmoothStreams.__name__.lower()]['api'].terminate()

                    del cls._providers[SmoothStreams.__name__.lower()]
            # </editor-fold>

            # <editor-fold desc="Read VaderStreams section">
            (is_valid_vader_streams_section,
             vader_streams_server,
             vader_streams_username,
             vader_streams_password,
             vader_streams_playlist_protocol,
             vader_streams_playlist_type) = VaderStreamsConfiguration.read_configuration_file(
                configuration_object,
                error_messages)

            if is_valid_vader_streams_section:
                from .providers.vader_streams.api import VaderStreams
                from .providers.vader_streams.db import VaderStreamsDB
                from .providers.vader_streams.epg import VaderStreamsEPG

                cls._providers[VaderStreams.__name__.lower()] = {}
                cls._providers[VaderStreams.__name__.lower()]['api'] = VaderStreams()
                cls._providers[VaderStreams.__name__.lower()]['db'] = VaderStreamsDB
                cls._providers[VaderStreams.__name__.lower()]['epg'] = VaderStreamsEPG()
            else:
                from .providers.vader_streams.api import VaderStreams

                if VaderStreams.__name__.lower() in cls._providers:
                    cls._providers[VaderStreams.__name__.lower()]['api'].terminate()

                    del cls._providers[VaderStreams.__name__.lower()]
            # </editor-fold>

            # <editor-fold desc="Read Logging section">
            try:
                logging_section = configuration_object['Logging']

                try:
                    logging_level = logging_section['level'].upper()
                    if not IPTVProxyUtility.is_valid_logging_level(logging_level):
                        logging_level = DEFAULT_LOGGING_LEVEL

                        error_messages.append('The level option within the [Logging] section must be one of\n'
                                              '{0}\n'
                                              'Defaulting to {1}\n'.format('\n'.join(['\u2022 {0}'.format(service)
                                                                                      for service in
                                                                                      VALID_LOGGING_LEVEL_VALUES]),
                                                                           logging_level))
                except KeyError:
                    error_messages.append('Could not find a level option within the [Logging] section\n'
                                          'The level option within the [Logging] section must be one of\n'
                                          '{0}\n'
                                          'Defaulting to {1}\n'.format('\n'.join(['\u2022 {0}'.format(service)
                                                                                  for service in
                                                                                  VALID_LOGGING_LEVEL_VALUES]),
                                                                       logging_level))
            except KeyError:
                error_messages.append('Could not find an [Logging] section\n'
                                      'Defaulting the level option to {0}\n'.format(logging_level))
            # </editor-fold>

            if error_messages:
                error_messages.insert(0,
                                      '{0} configuration file values\n'
                                      'Configuration file path => {1}\n'.format(
                                          'Invalid' if non_defaultable_error else 'Warnings regarding',
                                          cls._configuration_file_path))

                if initial_read and non_defaultable_error:
                    error_messages.append('Exiting...')
                elif non_defaultable_error:
                    error_messages.append('Skipping...')
                else:
                    error_messages.append('Processing with default values...')

                logger.error('\n'.join(error_messages))

                if initial_read and non_defaultable_error:
                    sys.exit()

            if not non_defaultable_error:
                configuration = {
                    'SERVER_PASSWORD': password,
                    'SERVER_HOSTNAME_LOOPBACK': hostname_loopback,
                    'SERVER_HOSTNAME_PRIVATE': hostname_private,
                    'SERVER_HOSTNAME_PUBLIC': hostname_public,
                    'SERVER_HTTP_PORT': http_port,
                    'SERVER_HTTPS_PORT': https_port,
                    'SMOOTH_STREAMS_SERVICE': smooth_streams_service,
                    'SMOOTH_STREAMS_SERVER': smooth_streams_server,
                    'SMOOTH_STREAMS_USERNAME': smooth_streams_username,
                    'SMOOTH_STREAMS_PASSWORD': smooth_streams_password,
                    'SMOOTH_STREAMS_PLAYLIST_PROTOCOL': smooth_streams_playlist_protocol,
                    'SMOOTH_STREAMS_PLAYLIST_TYPE': smooth_streams_playlist_type,
                    'SMOOTH_STREAMS_EPG_SOURCE': smooth_streams_epg_source,
                    'VADER_STREAMS_SERVER': vader_streams_server,
                    'VADER_STREAMS_USERNAME': vader_streams_username,
                    'VADER_STREAMS_PASSWORD': vader_streams_password,
                    'VADER_STREAMS_PLAYLIST_PROTOCOL': vader_streams_playlist_protocol,
                    'VADER_STREAMS_PLAYLIST_TYPE': vader_streams_playlist_type,
                    'LOGGING_LEVEL': logging_level
                }
                cls._set_configuration(configuration)

                logger.info('{0}ead configuration file\n'
                            'Configuration file path          => {1}\n\n'
                            'SERVER_PASSWORD                  => {2}\n'
                            'SERVER_HOSTNAME_LOOPBACK         => {3}\n'
                            'SERVER_HOSTNAME_PRIVATE          => {4}\n'
                            'SERVER_HOSTNAME_PUBLIC           => {5}\n'
                            'SERVER_HTTP_PORT                 => {6}\n'
                            'SERVER_HTTPS_PORT                => {7}\n\n'
                            'SMOOTH_STREAMS_SERVICE           => {8}\n'
                            'SMOOTH_STREAMS_SERVER            => {9}\n'
                            'SMOOTH_STREAMS_USERNAME          => {10}\n'
                            'SMOOTH_STREAMS_PASSWORD          => {11}\n'
                            'SMOOTH_STREAMS_PLAYLIST_PROTOCOL => {12}\n'
                            'SMOOTH_STREAMS_PLAYLIST_TYPE     => {13}\n'
                            'SMOOTH_STREAMS_EPG_SOURCE        => {14}\n\n'
                            'VADER_STREAMS_SERVER             => {15}\n'
                            'VADER_STREAMS_USERNAME           => {16}\n'
                            'VADER_STREAMS_PASSWORD           => {17}\n'
                            'VADER_STREAMS_PLAYLIST_PROTOCOL  => {18}\n'
                            'VADER_STREAMS_PLAYLIST_TYPE      => {19}\n\n'
                            'LOGGING_LEVEL                    => {20}'.format('R' if initial_read else 'Rer',
                                                                              cls._configuration_file_path,
                                                                              password,
                                                                              hostname_loopback,
                                                                              hostname_private,
                                                                              hostname_public,
                                                                              http_port,
                                                                              https_port,
                                                                              smooth_streams_service,
                                                                              smooth_streams_server,
                                                                              smooth_streams_username,
                                                                              smooth_streams_password,
                                                                              smooth_streams_playlist_protocol,
                                                                              smooth_streams_playlist_type,
                                                                              smooth_streams_epg_source,
                                                                              vader_streams_server,
                                                                              vader_streams_username,
                                                                              vader_streams_password,
                                                                              vader_streams_playlist_protocol,
                                                                              vader_streams_playlist_type,
                                                                              logging_level))
        except OSError:
            logger.error('Could not open the specified configuration file for reading\n'
                         'Configuration file path => {0}'
                         '{1}'.format(cls._configuration_file_path,
                                      '\n\nExiting...' if initial_read else ''))

            if initial_read:
                sys.exit()
        except SyntaxError as e:
            logger.error('Invalid configuration file syntax\n'
                         'Configuration file path => {0}\n'
                         '{1}'
                         '{2}'.format(cls._configuration_file_path,
                                      '{0}'.format(e),
                                      '\n\nExiting...' if initial_read else ''))

            if initial_read:
                sys.exit()

    @classmethod
    def set_configuration_file_path(cls, configuration_file_path):
        cls._configuration_file_path = configuration_file_path

    @classmethod
    def set_configuration_parameter(cls, parameter_name, parameter_value):
        with cls._lock:
            cls._configuration[parameter_name] = parameter_value

    @classmethod
    def start_configuration_file_watchdog_observer(cls):
        iptv_proxy_configuration_event_handler = IPTVProxyConfigurationEventHandler(cls._configuration_file_path)

        cls._configuration_file_watchdog_observer = Observer()
        cls._configuration_file_watchdog_observer.schedule(iptv_proxy_configuration_event_handler,
                                                           os.path.dirname(cls._configuration_file_path),
                                                           recursive=False)
        cls._configuration_file_watchdog_observer.start()

    @classmethod
    def stop_configuration_file_watchdog_observer(cls):
        cls._configuration_file_watchdog_observer.stop()

    @classmethod
    def update_configuration_file(cls, section, option, value):
        configuration_file_path = cls._configuration_file_path

        configuration_object = ConfigObj(configuration_file_path,
                                         file_error=True,
                                         interpolation=False,
                                         write_empty_values=True)
        configuration_object[section][option] = value

        try:
            configuration_object.write()

            logger.debug('Updated configuration file\n'
                         'Configuration file path => {0}\n\n'
                         'Section => {1}\n'
                         'Option  => {2}\n'
                         'Value   => {3}'.format(configuration_file_path, section, option, value))
        except OSError:
            logger.error('Could not open the specified configuration file for writing\n'
                         'Configuration file path => {0}'.format(configuration_file_path))

    @classmethod
    def validate_update_configuration_request(cls, configuration):
        errors = {}

        # <editor-fold desc="Validate Server options">
        if not IPTVProxyUtility.is_valid_server_password(configuration['SERVER_PASSWORD']):
            errors['serverPassword'] = 'Must not be an empty value'

        if not IPTVProxyUtility.is_valid_loopback_hostname(configuration['SERVER_HOSTNAME_LOOPBACK']):
            errors['serverHostnameLoopback'] = 'Must be a valid loopback IP address or hostname\n' \
                                               'Recommended value => {0}'.format(DEFAULT_HOSTNAME_LOOPBACK)

        if not IPTVProxyUtility.is_valid_private_hostname(configuration['SERVER_HOSTNAME_PRIVATE']):
            if not IPTVProxyUtility.is_valid_public_hostname(configuration['SERVER_HOSTNAME_PRIVATE']):
                private_ip_address = IPTVProxyUtility.determine_private_ip_address()

                errors['serverHostnamePrivate'] = 'Must be a valid private IP address, public IP address, or hostname'

                if private_ip_address:
                    errors['serverHostnamePrivate'] += '\nRecommended value => {0}'.format(private_ip_address)

        if not IPTVProxyUtility.is_valid_public_hostname(configuration['SERVER_HOSTNAME_PUBLIC']):
            public_ip_address = IPTVProxyUtility.determine_public_ip_address()

            errors['serverHostnamePublic'] = 'Must be a valid public IP address or hostname'

            if public_ip_address:
                errors['serverHostnamePublic'] += '\nRecommended value => {0}'.format(public_ip_address)

        if not IPTVProxyUtility.is_valid_port_number(configuration['SERVER_HTTP_PORT']):
            errors['serverPort'] = 'Must be a number between 0 and 65535'
        # </editor-fold>

        # <editor-fold desc="Validate SmoothStreams options">
        SmoothStreamsConfiguration.validate_update_configuration_request(configuration, errors)
        # </editor-fold>

        # <editor-fold desc="Validate VaderStreams options">
        VaderStreamsConfiguration.validate_update_configuration_request(configuration, errors)
        # </editor-fold>

        # <editor-fold desc="Validate Logging options">
        if not IPTVProxyUtility.is_valid_logging_level(configuration['LOGGING_LEVEL']):
            errors['loggingLevel'] = 'Must be one of [{0}]'.format(
                ', '.join(['\'{0}\''.format(logging_level) for logging_level in VALID_LOGGING_LEVEL_VALUES]))
        # </editor-fold>

        return errors

    @classmethod
    def write_configuration_file(cls, configuration):
        configuration_file_path = cls._configuration_file_path

        try:
            configuration_object = ConfigObj(configuration_file_path,
                                             file_error=True,
                                             interpolation=False,
                                             write_empty_values=True)

            # <editor-fold desc="Create Server section">
            server_section = {
                'password': configuration['SERVER_PASSWORD'],
                'Ports': {
                    'http': configuration['SERVER_HTTP_PORT'],
                    'https': configuration['SERVER_HTTPS_PORT']
                },
                'Hostnames': {
                    'loopback': configuration['SERVER_HOSTNAME_LOOPBACK'],
                    'private': configuration['SERVER_HOSTNAME_PRIVATE'],
                    'public': configuration['SERVER_HOSTNAME_PUBLIC']
                }
            }

            configuration_object['Server'] = server_section
            # </editor-fold>

            # <editor-fold desc="Create SmoothStreams section">
            smooth_streams_section = SmoothStreamsConfiguration.create_section(configuration)

            if smooth_streams_section:
                configuration_object['SmoothStreams'] = smooth_streams_section
            # </editor-fold>

            # <editor-fold desc="Create VaderStreams section">
            vader_streams_section = VaderStreamsConfiguration.create_section(configuration)

            if vader_streams_section:
                configuration_object['VaderStreams'] = vader_streams_section
            # </editor-fold>

            # <editor-fold desc="Create Logging section">
            logging_section = {
                'level': configuration['LOGGING_LEVEL']
            }

            configuration_object['Logging'] = logging_section
            # </editor-fold>

            configuration_object.write()

            logger.debug('Updated configuration file\n'
                         'Configuration file path => {0}'.format(configuration_file_path))
        except OSError:
            logger.error('Could not open the specified configuration file for writing\n'
                         'Configuration file path => {0}'.format(configuration_file_path))

            raise


class IPTVProxyConfigurationEventHandler(FileSystemEventHandler):
    def __init__(self, configuration_file_path):
        FileSystemEventHandler.__init__(self)

        self._configuration_file_path = configuration_file_path
        self._last_modification_date_time = None
        self._event_handler_lock = RLock()

    def on_modified(self, event):
        modification_event_date_time_in_utc = datetime.now(pytz.utc)
        do_read_configuration_file = False

        with self._event_handler_lock:
            if os.path.normpath(event.src_path) == os.path.normpath(self._configuration_file_path):
                # Read the configuration file if this is the first modification since the proxy started or if the
                # modification events are at least 1s apart (A hack to deal with watchdog generating duplicate events)
                if not self._last_modification_date_time:
                    do_read_configuration_file = True

                    self._last_modification_date_time = modification_event_date_time_in_utc
                else:
                    total_time_between_modifications = \
                        (modification_event_date_time_in_utc - self._last_modification_date_time).total_seconds()

                    if total_time_between_modifications >= 1.0:
                        do_read_configuration_file = True

                        self._last_modification_date_time = modification_event_date_time_in_utc

                if do_read_configuration_file:
                    logger.debug('Detected changes in configuration file\n'
                                 'Configuration file path => {0}'.format(self._configuration_file_path))

                    IPTVProxyConfiguration.read_configuration_file(initial_read=False)
                    IPTVProxyConfiguration.process_configuration_file_updates()
