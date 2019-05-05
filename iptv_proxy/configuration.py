import copy
import hashlib
import json
import logging
import os
import sys
import traceback
from collections import OrderedDict
from json import JSONDecodeError

from configobj import ConfigObj
from rwlock import RWLock
from watchdog.observers import Observer

from iptv_proxy.constants import DEFAULT_HOSTNAME_LOOPBACK
from iptv_proxy.db import Database
from iptv_proxy.providers import ProvidersController
from iptv_proxy.utilities import Utility
from iptv_proxy.watchdog_events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class Configuration(object):
    __slots__ = []

    _configuration = {}
    _configuration_file_path = None
    _configuration_file_watchdog_observer = None
    _lock = RWLock()
    _previous_configuration = {}

    @classmethod
    def _backup_configuration(cls):
        with cls._lock.writer_lock:
            cls._previous_configuration = copy.deepcopy(cls._configuration)

    @classmethod
    def _set_configuration(cls, configuration):
        cls._configuration = configuration

    @classmethod
    def _update_configuration_file(cls, configuration_object):
        if cls._configuration_file_watchdog_observer is not None:
            cls.stop_configuration_file_watchdog_observer()

        try:
            configuration_object.write()

            logger.debug('Updated configuration file\n'
                         'Configuration file path => {0}'.format(cls._configuration_file_path))
        except OSError:
            logger.error('Could not open the specified configuration file for writing\n'
                         'Configuration file path => {0}'.format(cls._configuration_file_path))
        finally:
            if cls._configuration_file_watchdog_observer is not None:
                cls.start_configuration_file_watchdog_observer()

    @classmethod
    def get_configuration_copy(cls):
        with cls._lock.reader_lock:
            return copy.deepcopy(cls._configuration)

    @classmethod
    def get_configuration_file_path(cls):
        return cls._configuration_file_path

    @classmethod
    def get_configuration_parameter(cls, parameter_name):
        with cls._lock.reader_lock:
            return cls._configuration[parameter_name]

    @classmethod
    def join_configuration_file_watchdog_observer(cls):
        cls._configuration_file_watchdog_observer.join()

    @classmethod
    def process_configuration_file_updates(cls):
        with cls._lock.writer_lock:
            message_to_log = []

            purge_http_sessions = False
            restart_http_server = False
            restart_https_server = False

            # <editor-fold desc="Detect and handle SERVER_PASSWORD change">
            if cls._configuration['SERVER_PASSWORD'] != cls._previous_configuration['SERVER_PASSWORD']:
                purge_http_sessions = True

                message_to_log.append('Detected a change in the password option in the [Server] section\n'
                                      'Old value => {0}\n'
                                      'New value => {1}\n'.format(cls._previous_configuration['SERVER_PASSWORD'],
                                                                  cls._configuration['SERVER_PASSWORD']))
            # </editor-fold>

            # <editor-fold desc="Detect and handle SERVER_HOSTNAME_<LOOPBACK,PRIVATE,PUBLIC> change">
            loopback_hostname_updated = False
            private_hostname_updated = False
            public_hostname_updated = False

            if cls._configuration['SERVER_HOSTNAME_LOOPBACK'] != \
                    cls._previous_configuration['SERVER_HOSTNAME_LOOPBACK']:
                loopback_hostname_updated = True

                message_to_log.append(
                    'Detected a change in the loopback option in the [Hostnames] section\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(cls._previous_configuration['SERVER_HOSTNAME_LOOPBACK'],
                                                cls._configuration['SERVER_HOSTNAME_LOOPBACK']))

            if cls._configuration['SERVER_HOSTNAME_PRIVATE'] != cls._previous_configuration['SERVER_HOSTNAME_PRIVATE']:
                private_hostname_updated = True

                message_to_log.append(
                    'Detected a change in the private option in the [Hostnames] section\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(cls._previous_configuration['SERVER_HOSTNAME_PRIVATE'],
                                                cls._configuration['SERVER_HOSTNAME_PRIVATE']))

            if cls._configuration['SERVER_HOSTNAME_PUBLIC'] != cls._previous_configuration['SERVER_HOSTNAME_PUBLIC']:
                public_hostname_updated = True

                message_to_log.append(
                    'Detected a change in the public option in the [Hostnames] section\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(cls._previous_configuration['SERVER_HOSTNAME_PUBLIC'],
                                                cls._configuration['SERVER_HOSTNAME_PUBLIC']))

            if loopback_hostname_updated or private_hostname_updated or public_hostname_updated:
                restart_https_server = True
            # </editor-fold>

            # <editor-fold desc="Detect and handle SERVER_HTTP_PORT change">
            if cls._configuration['SERVER_HTTP_PORT'] != cls._previous_configuration['SERVER_HTTP_PORT']:
                restart_http_server = True

                message_to_log.append(
                    'Detected a change in the http option in the [Ports] section\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(cls._previous_configuration['SERVER_HTTP_PORT'],
                                                cls._configuration['SERVER_HTTP_PORT']))
            # </editor-fold>

            # <editor-fold desc="Detect and handle SERVER_HTTPS_PORT change">
            if cls._configuration['SERVER_HTTPS_PORT'] != cls._previous_configuration['SERVER_HTTPS_PORT']:
                restart_https_server = True

                message_to_log.append('Detected a change in the https option in the [Ports] section\n'
                                      'Old value => {0}\n'
                                      'New value => {1}\n'.format(cls._previous_configuration['SERVER_HTTPS_PORT'],
                                                                  cls._configuration['SERVER_HTTPS_PORT']))
            # </editor-fold>

            if purge_http_sessions:
                from iptv_proxy.http_server import HTTPRequestHandler

                message_to_log.append('Action => Purge all user HTTP/S sessions')

                with Database.get_write_lock():
                    db_session = Database.create_session()

                    try:
                        HTTPRequestHandler.purge_http_sessions(db_session)
                        db_session.commit()
                    except Exception:
                        (type_, value_, traceback_) = sys.exc_info()
                        logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                        db_session.rollback()
                    finally:
                        db_session.close()

            if restart_http_server:
                from iptv_proxy.controller import Controller

                message_to_log.append('Action => Restart HTTP server')

                Controller.shutdown_http_server()
                Controller.start_http_server()

            if restart_https_server:
                from iptv_proxy.security import SecurityManager

                message_to_log.append('Action => Restart HTTPS server')

                if SecurityManager.get_auto_generate_self_signed_certificate():
                    SecurityManager.generate_self_signed_certificate()

                    from iptv_proxy.controller import Controller

                    Controller.shutdown_https_server()
                    Controller.start_https_server()

            if message_to_log:
                logger.debug('\n'.join(message_to_log))

            for provider_name in sorted(ProvidersController.get_providers_map_class()):
                ProvidersController.get_provider_map_class(
                    provider_name).configuration_class().process_configuration_file_updates(cls._configuration,
                                                                                            cls._previous_configuration)

    @classmethod
    def read_configuration_file(cls, initial_read=True):
        with cls._lock.writer_lock:
            cls._backup_configuration()

            try:
                configuration_object = ConfigObj(cls._configuration_file_path,
                                                 file_error=True,
                                                 indent_type='',
                                                 interpolation=False,
                                                 raise_errors=True,
                                                 write_empty_values=True)

                configuration_object_md5 = hashlib.md5('{0}'.format(configuration_object).encode()).hexdigest()

                configuration = {}
                providers = []

                non_defaultable_error = False
                error_message_to_log = []
                message_to_log = []

                password = None
                hostname_loopback = DEFAULT_HOSTNAME_LOOPBACK
                hostname_private = None
                hostname_public = None
                http_port = None
                https_port = None

                # <editor-fold desc="Read Server section">
                try:
                    server_section = configuration_object['Server']

                    try:
                        password = server_section['password']
                    except KeyError:
                        non_defaultable_error = True

                        error_message_to_log.append('Could not find a password option in the [Server] section\n')

                    try:
                        server_hostnames_section = server_section['Hostnames']

                        # <editor-fold desc="Read loopback option">
                        try:
                            hostname_loopback = server_hostnames_section['loopback']

                            if not Utility.is_valid_loopback_hostname(hostname_loopback):
                                error_message_to_log.append(
                                    'The loopback option in the [Hostnames] section has an invalid loopback hostname\n'
                                    'Defaulting to {0}\n'.format(DEFAULT_HOSTNAME_LOOPBACK))
                        except KeyError:
                            hostname_loopback = DEFAULT_HOSTNAME_LOOPBACK

                            error_message_to_log.append(
                                'The loopback option in the [Hostnames] section is missing\n'
                                'Defaulting to {0}\n'.format(DEFAULT_HOSTNAME_LOOPBACK))
                        # </editor-fold>

                        # <editor-fold desc="Read private option">
                        do_determine_private_ip_address = False

                        try:
                            hostname_private = server_hostnames_section['private']

                            if not Utility.is_valid_private_hostname(hostname_private):
                                if Utility.is_valid_public_hostname(hostname_private):
                                    error_message_to_log.append(
                                        'The private option in the [Hostnames] section has a public IP address\n')
                                else:
                                    do_determine_private_ip_address = True
                        except KeyError:
                            do_determine_private_ip_address = True
                        # </editor-fold>

                        # <editor-fold desc="Read public option">
                        do_determine_public_ip_address = False

                        try:
                            hostname_public = server_hostnames_section['public']
                            if not Utility.is_valid_public_hostname(hostname_public):
                                do_determine_public_ip_address = True
                        except KeyError:
                            do_determine_public_ip_address = True
                        # </editor-fold>
                    except KeyError:
                        error_message_to_log.append(
                            'Could not find a [Hostnames] section in the [Server] section\n')

                        hostname_loopback = DEFAULT_HOSTNAME_LOOPBACK

                        do_determine_private_ip_address = True
                        do_determine_public_ip_address = True

                    if do_determine_private_ip_address:
                        hostname_private = Utility.determine_private_ip_address()

                        if hostname_private:
                            error_message_to_log.append(
                                'The private option in the [Hostnames] section has an invalid private IP address\n'
                                'Reverting to {0}\n'.format(hostname_private))

                    if do_determine_public_ip_address:
                        hostname_public = Utility.determine_public_ip_address()

                        if hostname_public:
                            error_message_to_log.append(
                                'The public option in the [Hostnames] section has an invalid public IP address\n'
                                'Reverting to {0}\n'.format(hostname_public))

                    try:
                        server_ports_section = server_section['Ports']

                        # <editor-fold desc="Read http option">
                        try:
                            http_port = server_ports_section['http']
                            if not Utility.is_valid_port_number(http_port):
                                non_defaultable_error = True

                                error_message_to_log.append(
                                    'The http option in the [Ports] section must be a number between 0 and 65535\n')
                        except KeyError:
                            non_defaultable_error = True

                            error_message_to_log.append(
                                'Could not find an http option in the [Ports] section\n'
                                'The http option in the [Ports] section must be a number between 0 and 65535\n')
                        # </editor-fold>

                        # <editor-fold desc="Read https option">
                        try:
                            https_port = server_ports_section['https']
                            if not Utility.is_valid_port_number(https_port):
                                non_defaultable_error = True

                                error_message_to_log.append(
                                    'The https option in the [Ports] section must be a number between 0 and 65535\n')
                        except KeyError:
                            non_defaultable_error = True

                            error_message_to_log.append(
                                'Could not find an https option in the [Ports] section\n'
                                'The https option in the [Ports] section must be a number between 0 and 65535\n')
                        # </editor-fold>
                    except KeyError:
                        non_defaultable_error = True

                        error_message_to_log.append('Could not find a [Ports] section in the [Server] section\n')
                except KeyError:
                    non_defaultable_error = True

                    error_message_to_log.append('Could not find a [Server] section\n')
                # </editor-fold>

                if not non_defaultable_error:
                    configuration = {
                        'SERVER_PASSWORD': password,
                        'SERVER_HOSTNAME_LOOPBACK': hostname_loopback,
                        'SERVER_HOSTNAME_PRIVATE': hostname_private,
                        'SERVER_HOSTNAME_PUBLIC': hostname_public,
                        'SERVER_HTTP_PORT': http_port,
                        'SERVER_HTTPS_PORT': https_port
                    }

                    message_to_log = ['{0}ead configuration file\n'
                                      'Configuration file path          => {1}\n\n'
                                      'SERVER_PASSWORD                  => {2}\n'
                                      'SERVER_HOSTNAME_LOOPBACK         => {3}\n'
                                      'SERVER_HOSTNAME_PRIVATE          => {4}\n'
                                      'SERVER_HOSTNAME_PUBLIC           => {5}\n'
                                      'SERVER_HTTP_PORT                 => {6}\n'
                                      'SERVER_HTTPS_PORT                => {7}'.format('R' if initial_read else 'Rer',
                                                                                       cls._configuration_file_path,
                                                                                       password,
                                                                                       hostname_loopback,
                                                                                       hostname_private,
                                                                                       hostname_public,
                                                                                       http_port,
                                                                                       https_port)]

                for provider_name in sorted(ProvidersController.get_providers_map_class()):
                    ProvidersController.get_provider_map_class(
                        provider_name).configuration_class().read_configuration_file(configuration_object,
                                                                                     configuration,
                                                                                     providers,
                                                                                     message_to_log,
                                                                                     error_message_to_log)

                if not non_defaultable_error:
                    logger.info('\n'.join(message_to_log))

                    cls._set_configuration(configuration)

                    if configuration_object_md5 != hashlib.md5('{0}'.format(configuration_object).encode()).hexdigest():
                        cls._update_configuration_file(configuration_object)

                    if initial_read:
                        ProvidersController.initialize_providers(providers)

                if error_message_to_log:
                    error_message_to_log.insert(0,
                                                '{0} configuration file values\n'
                                                'Configuration file path => {1}\n'.format(
                                                    'Invalid' if non_defaultable_error
                                                    else 'Warnings regarding',
                                                    cls._configuration_file_path))

                    if initial_read and non_defaultable_error:
                        error_message_to_log.append('Exiting...')
                    elif non_defaultable_error:
                        error_message_to_log.append('Configuration file skipped')
                    else:
                        error_message_to_log.append('Configuration file processed')

                    logger.error('\n'.join(error_message_to_log))

                    if initial_read and non_defaultable_error:
                        sys.exit()
            except OSError:
                logger.error('Could not open the specified configuration file for reading\n'
                             'Configuration file path => {0}'
                             '{1}'.format(cls._configuration_file_path,
                                          '\n\nExiting...' if initial_read
                                          else ''))

                if initial_read:
                    sys.exit()
            except SyntaxError as e:
                logger.error('Invalid configuration file syntax\n'
                             'Configuration file path => {0}\n'
                             '{1}'
                             '{2}'.format(cls._configuration_file_path,
                                          '{0}'.format(e),
                                          '\n\nExiting...' if initial_read
                                          else ''))

                if initial_read:
                    sys.exit()

    @classmethod
    def set_configuration_file_path(cls, configuration_file_path):
        cls._configuration_file_path = configuration_file_path

    @classmethod
    def set_configuration_parameter(cls, parameter_name, parameter_value):
        with cls._lock.writer_lock:
            cls._configuration[parameter_name] = parameter_value

    @classmethod
    def start_configuration_file_watchdog_observer(cls):
        iptv_proxy_configuration_event_handler = ConfigurationEventHandler(cls._configuration_file_path)

        cls._configuration_file_watchdog_observer = Observer()
        cls._configuration_file_watchdog_observer.schedule(iptv_proxy_configuration_event_handler,
                                                           os.path.dirname(cls._configuration_file_path),
                                                           recursive=False)
        cls._configuration_file_watchdog_observer.start()

    @classmethod
    def stop_configuration_file_watchdog_observer(cls):
        cls._configuration_file_watchdog_observer.stop()

    @classmethod
    def validate_update_configuration_request(cls, configuration):
        errors = {}

        # <editor-fold desc="Validate Server options">
        if not Utility.is_valid_server_password(configuration['SERVER_PASSWORD']):
            errors['serverPassword'] = 'Must not be an empty value'

        if not Utility.is_valid_loopback_hostname(configuration['SERVER_HOSTNAME_LOOPBACK']):
            errors['serverHostnameLoopback'] = 'Must be a valid loopback IP address or hostname\n' \
                                               'Recommended value => {0}'.format(DEFAULT_HOSTNAME_LOOPBACK)

        if not Utility.is_valid_private_hostname(configuration['SERVER_HOSTNAME_PRIVATE']):
            if not Utility.is_valid_public_hostname(configuration['SERVER_HOSTNAME_PRIVATE']):
                private_ip_address = Utility.determine_private_ip_address()

                errors['serverHostnamePrivate'] = 'Must be a valid private IP address, public IP address, or hostname'

                if private_ip_address:
                    errors['serverHostnamePrivate'] += '\nRecommended value => {0}'.format(private_ip_address)

        if not Utility.is_valid_public_hostname(configuration['SERVER_HOSTNAME_PUBLIC']):
            public_ip_address = Utility.determine_public_ip_address()

            errors['serverHostnamePublic'] = 'Must be a valid public IP address or hostname'

            if public_ip_address:
                errors['serverHostnamePublic'] += '\nRecommended value => {0}'.format(public_ip_address)

        if not Utility.is_valid_port_number(configuration['SERVER_HTTP_PORT']):
            errors['serverPort'] = 'Must be a number between 0 and 65535'
        # </editor-fold>

        for provider_name in sorted(ProvidersController.get_providers_map_class()):
            ProvidersController.get_provider_map_class(
                provider_name).configuration_class().validate_update_configuration_request(configuration,
                                                                                           errors)

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

            for provider_name in sorted(ProvidersController.get_providers_map_class()):
                provider_section = ProvidersController.get_provider_map_class(
                    provider_name).configuration_class().create_section(configuration)

                if provider_section:
                    configuration_object[ProvidersController.get_provider_map_class(
                        provider_name).api_class().__name__] = provider_section

            configuration_object.write()

            logger.debug('Updated configuration file\n'
                         'Configuration file path => {0}'.format(configuration_file_path))
        except OSError:
            logger.error('Could not open the specified configuration file for writing\n'
                         'Configuration file path => {0}'.format(configuration_file_path))

            raise


class ConfigurationEventHandler(FileSystemEventHandler):
    def __init__(self, configuration_file_path):
        FileSystemEventHandler.__init__(self, configuration_file_path)

    def on_modified(self, event):
        with self._lock:
            if self._do_process_on_modified_event(event):
                logger.debug('Detected changes in configuration file\n'
                             'Configuration file path => {0}'.format(self._file_path))

                Configuration.read_configuration_file(initial_read=False)
                Configuration.process_configuration_file_updates()


class OptionalSettings(object):
    __slots__ = []

    _lock = RWLock()
    _optional_settings = OrderedDict()
    _optional_settings_file_path = None
    _optional_settings_file_watchdog_observer = None
    _previous_optional_settings = OrderedDict()

    @classmethod
    def _backup_optional_settings(cls):
        with cls._lock.writer_lock:
            cls._previous_optional_settings = copy.deepcopy(cls._optional_settings)

    @classmethod
    def _set_optional_settings(cls, optional_settings):
        with cls._lock.writer_lock:
            cls._optional_settings = optional_settings

    @classmethod
    def get_optional_settings_file_path(cls):
        return cls._optional_settings_file_path

    @classmethod
    def get_optional_settings_parameter(cls, parameter_name):
        with cls._lock.reader_lock:
            return cls._optional_settings[parameter_name]

    @classmethod
    def join_optional_settings_file_watchdog_observer(cls):
        cls._optional_settings_file_watchdog_observer.join()

    @classmethod
    def process_optional_settings_file_updates(cls):
        with cls._lock.writer_lock:
            message_to_log = []

            # <editor-fold desc="Detect and handle cache_downloaded_segments change">
            if 'cache_downloaded_segments' not in cls._optional_settings:
                cls._optional_settings['cache_downloaded_segments'] = True

            if 'cache_downloaded_segments' not in cls._previous_optional_settings or \
                    cls._optional_settings['cache_downloaded_segments'] != \
                    cls._previous_optional_settings['cache_downloaded_segments']:
                from iptv_proxy.cache import CacheManager

                message_to_log.append(
                    'Detected a change in the cache_downloaded_segments setting\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(
                        json.dumps(cls._previous_optional_settings['cache_downloaded_segments']),
                        json.dumps(cls._optional_settings['cache_downloaded_segments'])))

                CacheManager.set_do_cache_downloaded_segments(
                    cls._optional_settings['cache_downloaded_segments'])
            # </editor-fold>

            # <editor-fold desc="Detect and handle allow_insecure_lan_connections change">
            if 'allow_insecure_lan_connections' not in cls._optional_settings:
                cls._optional_settings['allow_insecure_lan_connections'] = True

            if 'allow_insecure_lan_connections' not in cls._previous_optional_settings or \
                    cls._optional_settings['allow_insecure_lan_connections'] != \
                    cls._previous_optional_settings['allow_insecure_lan_connections']:
                from iptv_proxy.http_server import HTTPRequestHandler

                message_to_log.append(
                    'Detected a change in the allow_insecure_lan_connections setting\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(
                        json.dumps(cls._previous_optional_settings['allow_insecure_lan_connections']),
                        json.dumps(cls._optional_settings['allow_insecure_lan_connections'])))

                HTTPRequestHandler.set_allow_insecure_lan_connections(
                    cls._optional_settings['allow_insecure_lan_connections'])
            # </editor-fold>

            # <editor-fold desc="Detect and handle allow_insecure_wan_connections change">
            if 'allow_insecure_wan_connections' not in cls._optional_settings:
                cls._optional_settings['allow_insecure_wan_connections'] = False

            if 'allow_insecure_wan_connections' not in cls._previous_optional_settings or \
                    cls._optional_settings['allow_insecure_wan_connections'] != \
                    cls._previous_optional_settings['allow_insecure_wan_connections']:
                from iptv_proxy.http_server import HTTPRequestHandler

                message_to_log.append(
                    'Detected a change in the allow_insecure_wan_connections setting\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(
                        json.dumps(cls._previous_optional_settings['allow_insecure_wan_connections']),
                        json.dumps(cls._optional_settings['allow_insecure_wan_connections'])))

                HTTPRequestHandler.set_allow_insecure_wan_connections(
                    cls._optional_settings['allow_insecure_wan_connections'])
            # </editor-fold>

            # <editor-fold desc="Detect and handle lan_connections_require_credentials change">
            if 'lan_connections_require_credentials' not in cls._optional_settings:
                cls._optional_settings['lan_connections_require_credentials'] = False

            if 'lan_connections_require_credentials' not in cls._previous_optional_settings or \
                    cls._optional_settings['lan_connections_require_credentials'] != \
                    cls._previous_optional_settings['lan_connections_require_credentials']:
                from iptv_proxy.http_server import HTTPRequestHandler

                message_to_log.append(
                    'Detected a change in the lan_connections_require_credentials setting\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(
                        json.dumps(cls._previous_optional_settings['lan_connections_require_credentials']),
                        json.dumps(cls._optional_settings['lan_connections_require_credentials'])))

                HTTPRequestHandler.set_lan_connections_require_credentials(
                    cls._optional_settings['lan_connections_require_credentials'])
            # </editor-fold>

            # <editor-fold desc="Detect and handle wan_connections_require_credentials change">
            if 'wan_connections_require_credentials' not in cls._optional_settings:
                cls._optional_settings['wan_connections_require_credentials'] = True

            if 'wan_connections_require_credentials' not in cls._previous_optional_settings or \
                    cls._optional_settings['wan_connections_require_credentials'] != \
                    cls._previous_optional_settings['wan_connections_require_credentials']:
                from iptv_proxy.http_server import HTTPRequestHandler

                message_to_log.append(
                    'Detected a change in the wan_connections_require_credentials setting\n'
                    'Old value => {0}\n'
                    'New value => {1}\n'.format(
                        json.dumps(cls._previous_optional_settings['wan_connections_require_credentials']),
                        json.dumps(cls._optional_settings['wan_connections_require_credentials'])))

                HTTPRequestHandler.set_wan_connections_require_credentials(
                    cls._optional_settings['wan_connections_require_credentials'])
            # </editor-fold>

            if message_to_log:
                message_to_log.append('Action => N/A')

                logger.debug('\n'.join(message_to_log))

            for provider_name in sorted(ProvidersController.get_providers_map_class()):
                ProvidersController.get_provider_map_class(
                    provider_name).optional_settings_class().process_optional_settings_file_updates(
                    cls._optional_settings,
                    cls._previous_optional_settings)

    @classmethod
    def read_optional_settings_file(cls):
        with cls._lock.writer_lock:
            cls._backup_optional_settings()

            try:
                optional_settings_file_content = Utility.read_file(cls._optional_settings_file_path)
                cls._set_optional_settings(json.loads(optional_settings_file_content, object_pairs_hook=OrderedDict))
            except OSError:
                logger.error('Failed to read optional settings file\n'
                             'Optional settings file path => {0}'.format(cls._optional_settings_file_path))
            except JSONDecodeError:
                logger.error('Invalid optional settings file syntax\n'
                             'Optional settings file path => {0}'.format(cls._optional_settings_file_path))

    @classmethod
    def set_optional_settings_file_path(cls, optional_settings_file_path):
        cls._optional_settings_file_path = optional_settings_file_path

    @classmethod
    def set_optional_settings_parameter(cls, parameter_name, parameter_value):
        with cls._lock.writer_lock:
            cls._optional_settings[parameter_name] = parameter_value

    @classmethod
    def start_optional_settings_file_watchdog_observer(cls):
        iptv_proxy_optional_settings_event_handler = OptionalSettingsEventHandler(cls._optional_settings_file_path)

        cls._optional_settings_file_watchdog_observer = Observer()
        cls._optional_settings_file_watchdog_observer.schedule(iptv_proxy_optional_settings_event_handler,
                                                               os.path.dirname(cls._optional_settings_file_path),
                                                               recursive=False)
        cls._optional_settings_file_watchdog_observer.start()

    @classmethod
    def stop_optional_settings_file_watchdog_observer(cls):
        cls._optional_settings_file_watchdog_observer.stop()


class OptionalSettingsEventHandler(FileSystemEventHandler):
    def __init__(self, optional_settings_file_path):
        FileSystemEventHandler.__init__(self, optional_settings_file_path)

    def on_modified(self, event):
        with self._lock:
            if self._do_process_on_modified_event(event):
                logger.debug('Detected changes in optional settings file\n'
                             'Optional settings file path => {0}'.format(self._file_path))

                OptionalSettings.read_optional_settings_file()
                OptionalSettings.process_optional_settings_file_updates()
