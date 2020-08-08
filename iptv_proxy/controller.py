import logging
import os
import sys
import traceback
from ssl import SSLError
from threading import Event

from iptv_proxy.cache import CacheManager
from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.db import Database
from iptv_proxy.html_template_engine import HTMLTemplateEngine
from iptv_proxy.http_server import HTTPRequestHandler
from iptv_proxy.http_server import HTTPServerThread
from iptv_proxy.logging import Logging
from iptv_proxy.privilege import Privilege
from iptv_proxy.providers import ProvidersController
from iptv_proxy.recorder import PVR
from iptv_proxy.security import SecurityManager

logger = logging.getLogger(__name__)


class Controller(object):
    __slots__ = []

    _http_server_thread = None
    _https_server_thread = None
    _shutdown_proxy_event = Event()

    @classmethod
    def _shutdown_server(cls, server_thread):
        if server_thread:
            server_thread.stop()
            server_thread.join()

    @classmethod
    def _start_server(cls, is_secure):
        server_port = Configuration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_secure else '')
        )

        server_address = ('', int(server_port))

        server_thread = HTTPServerThread(server_address, is_secure=is_secure)
        server_thread.start()

        return server_thread

    @classmethod
    def shutdown_http_server(cls):
        cls._shutdown_server(cls._http_server_thread)

    @classmethod
    def shutdown_https_server(cls):
        cls._shutdown_server(cls._https_server_thread)

    @classmethod
    def shutdown_proxy(cls):
        cls._shutdown_proxy_event.set()

        ProvidersController.terminate()
        CacheManager.cancel_cleanup_cache_timer()
        PVR.cancel_start_recording_timer()
        PVR.stop()

        if cls._http_server_thread:
            cls._http_server_thread.stop()

        if cls._https_server_thread:
            cls._https_server_thread.stop()

        Configuration.stop_configuration_file_watchdog_observer()
        OptionalSettings.stop_optional_settings_file_watchdog_observer()
        Logging.stop_logging_configuration_file_watchdog_observer()

    @classmethod
    def start_http_server(cls):
        Privilege.become_privileged_user()
        cls._http_server_thread = cls._start_server(is_secure=False)
        Privilege.become_unprivileged_user()

    @classmethod
    def start_https_server(cls):
        try:
            Privilege.become_privileged_user()
            SecurityManager.determine_certificate_validity()
            cls._https_server_thread = cls._start_server(is_secure=True)
        except SSLError:
            logger.error(
                'Failed to start HTTPS Server\n'
                'Make sure the certificate and key files specified match\n'
                'Certificate file path => %s\n'
                'Key file path         => %s',
                SecurityManager.get_certificate_file_path(),
                SecurityManager.get_key_file_path(),
            )
        except OSError:
            error_message = ['Failed to start HTTPS Server']

            certificate_or_key_file_not_found = False

            if not os.path.exists(SecurityManager.get_certificate_file_path()):
                certificate_or_key_file_not_found = True

                error_message.append(
                    'SSL file not found\n'
                    'Certificate file path => {0}'.format(
                        SecurityManager.get_certificate_file_path()
                    )
                )

            if not os.path.exists(SecurityManager.get_key_file_path()):
                if certificate_or_key_file_not_found:
                    error_message[1] = error_message[1].replace('SSL file', 'SSL files')
                    error_message.append(
                        'Key file path         => {0}'.format(
                            SecurityManager.get_key_file_path()
                        )
                    )
                else:
                    certificate_or_key_file_not_found = True

                    error_message.append(
                        'SSL file not found\n'
                        'Key file path => {0}'.format(
                            SecurityManager.get_key_file_path()
                        )
                    )

            if not certificate_or_key_file_not_found:
                (status, value_, traceback_) = sys.exc_info()

                error_message.append(
                    '\n'.join(traceback.format_exception(status, value_, traceback_))
                )

            logger.error('\n'.join(error_message))
        finally:
            Privilege.become_unprivileged_user()

    @classmethod
    def start_proxy(
        cls,
        configuration_file_path,
        optional_settings_file_path,
        db_file_path,
        log_file_path,
        recordings_directory_path,
        certificate_file_path,
        key_file_path,
    ):
        Configuration.set_configuration_file_path(configuration_file_path)
        OptionalSettings.set_optional_settings_file_path(optional_settings_file_path)
        Database.set_database_file_path(db_file_path)
        Logging.set_log_file_path(log_file_path)
        PVR.set_recordings_directory_path(recordings_directory_path)
        SecurityManager.set_certificate_file_path(certificate_file_path)
        SecurityManager.set_key_file_path(key_file_path)

        ProvidersController.initialize()

        OptionalSettings.read_optional_settings_file()
        Database.initialize()
        SecurityManager.initialize()

        Configuration.read_configuration_file()

        CacheManager.initialize()
        HTMLTemplateEngine.initialize()
        HTTPRequestHandler.initialize()
        PVR.initialize()

        Configuration.start_configuration_file_watchdog_observer()
        OptionalSettings.start_optional_settings_file_watchdog_observer()
        Logging.start_logging_configuration_file_watchdog_observer()

        cls.start_http_server()
        cls.start_https_server()

        PVR.start()

        while not cls._shutdown_proxy_event.is_set():
            if cls._http_server_thread:
                cls._http_server_thread.join()

            if cls._https_server_thread:
                cls._https_server_thread.join()

            cls._shutdown_proxy_event.wait(0.5)

        Configuration.join_configuration_file_watchdog_observer()
        OptionalSettings.join_optional_settings_file_watchdog_observer()
        Logging.join_logging_configuration_file_watchdog_observer()
