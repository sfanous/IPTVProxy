import json
import logging
import os
import sys
import traceback
from ssl import SSLError
from threading import Event

from .cache import IPTVProxyCacheManager
from .configuration import IPTVProxyConfiguration
from .constants import OPTIONAL_SETTINGS_FILE_PATH
from .db import IPTVProxyDB
from .http_server import IPTVProxyHTTPRequestHandler
from .http_server import IPTVProxyHTTPServerThread
from .privilege import IPTVProxyPrivilege
from .providers.smooth_streams.epg import SmoothStreamsEPG
from .providers.vader_streams.api import VaderStreams
from .providers.vader_streams.epg import VaderStreamsEPG
from .recorder import IPTVProxyPVR
from .security import IPTVProxySecurityManager
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class IPTVProxyController(object):
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
        server_port = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_secure else ''))

        server_address = ('', int(server_port))

        server_thread = IPTVProxyHTTPServerThread(server_address, is_secure=is_secure)
        server_thread.start()

        return server_thread

    @classmethod
    def read_optional_settings(cls):
        optional_settings_file_content = IPTVProxyUtility.read_file(OPTIONAL_SETTINGS_FILE_PATH)

        try:
            optional_settings = json.loads(optional_settings_file_content)

            try:
                IPTVProxyHTTPRequestHandler.set_allow_insecure_lan_connections(
                    optional_settings['allow_insecure_lan_connections'])
            except KeyError:
                pass

            try:
                IPTVProxyHTTPRequestHandler.set_allow_insecure_wan_connections(
                    optional_settings['allow_insecure_wan_connections'])
            except KeyError:
                pass

            try:
                IPTVProxySecurityManager.set_auto_generate_self_signed_certificate(
                    optional_settings['auto_generate_self_signed_certificate'])
            except KeyError:
                pass

            try:
                IPTVProxyCacheManager.set_do_cache_downloaded_segments(optional_settings['cache_downloaded_segments'])
            except KeyError:
                pass

            try:
                IPTVProxyHTTPRequestHandler.set_lan_connections_require_credentials(
                    optional_settings['lan_connections_require_credentials'])
            except KeyError:
                pass

            try:
                VaderStreams.set_do_reduce_hls_stream_delay(optional_settings['reduce_vader_streams_delay'])
            except KeyError:
                pass

            try:
                SmoothStreamsEPG.set_channel_name_map(optional_settings['smooth_streams_channel_name_map'])
            except KeyError:
                pass

            try:
                SmoothStreamsEPG.set_do_use_smooth_streams_icons(optional_settings['use_smooth_streams_icons'])
            except KeyError:
                pass

            try:
                VaderStreamsEPG.set_do_use_vader_streams_icons(optional_settings['use_vader_streams_icons'])
            except KeyError:
                pass

            try:
                VaderStreamsEPG.set_channel_name_map(optional_settings['vader_streams_channel_name_map'])
            except KeyError:
                pass

            try:
                IPTVProxyHTTPRequestHandler.set_wan_connections_require_credentials(
                    optional_settings['wan_connections_require_credentials'])
            except KeyError:
                pass
        except json.JSONDecodeError:
            logger.error('Failed to read optional settings\n'
                         'File path => {0}'.format(OPTIONAL_SETTINGS_FILE_PATH))

    @classmethod
    def shutdown_http_server(cls):
        cls._shutdown_server(cls._http_server_thread)

    @classmethod
    def shutdown_https_server(cls):
        cls._shutdown_server(cls._https_server_thread)

    @classmethod
    def shutdown_proxy(cls):
        cls._shutdown_proxy_event.set()

        for provider in IPTVProxyConfiguration.get_providers().values():
            provider['api'].terminate()

        IPTVProxyCacheManager.cancel_cleanup_cache_timer()
        IPTVProxyPVR.cancel_start_recording_timer()

        if cls._http_server_thread:
            cls._http_server_thread.stop()

        if cls._https_server_thread:
            cls._https_server_thread.stop()

        IPTVProxyConfiguration.stop_configuration_file_watchdog_observer()
        IPTVProxyDB.terminate()

    @classmethod
    def start_http_server(cls):
        IPTVProxyPrivilege.become_privileged_user()
        cls._http_server_thread = cls._start_server(is_secure=False)
        IPTVProxyPrivilege.become_unprivileged_user()

    @classmethod
    def start_https_server(cls):
        try:
            IPTVProxyPrivilege.become_privileged_user()
            IPTVProxySecurityManager.determine_certificate_validity()
            cls._https_server_thread = cls._start_server(is_secure=True)
        except SSLError:
            logger.error(
                'Failed to start HTTPS Server\n'
                'Make sure the certificate and key files specified match\n'
                'Certificate file path => {0}\n'
                'Key file path         => {1}'.format(IPTVProxySecurityManager.get_certificate_file_path(),
                                                      IPTVProxySecurityManager.get_key_file_path()))
        except OSError:
            error_message = ['Failed to start HTTPS Server']

            certificate_or_key_file_not_found = False

            if not os.path.exists(IPTVProxySecurityManager.get_certificate_file_path()):
                certificate_or_key_file_not_found = True

                error_message.append(
                    'SSL file not found\n'
                    'Certificate file path => {0}'.format(
                        IPTVProxySecurityManager.get_certificate_file_path()))

            if not os.path.exists(IPTVProxySecurityManager.get_key_file_path()):
                if certificate_or_key_file_not_found:
                    error_message[1] = error_message[1].replace('SSL file', 'SSL files')
                    error_message.append('Key file path         => {0}'.format(
                        IPTVProxySecurityManager.get_key_file_path()))
                else:
                    certificate_or_key_file_not_found = True

                    error_message.append('SSL file not found\n'
                                         'Key file path => {0}'.format(IPTVProxySecurityManager.get_key_file_path()))

            if not certificate_or_key_file_not_found:
                (status, value_, traceback_) = sys.exc_info()

                error_message.append('\n'.join(traceback.format_exception(status, value_, traceback_)))

            logger.error('\n'.join(error_message))
        finally:
            IPTVProxyPrivilege.become_unprivileged_user()

    @classmethod
    def start_proxy(cls,
                    configuration_file_path,
                    db_file_path,
                    recordings_directory_path,
                    certificate_file_path,
                    key_file_path):
        IPTVProxyConfiguration.set_configuration_file_path(configuration_file_path)
        IPTVProxyDB.set_db_file_path(db_file_path)
        IPTVProxyPVR.set_recordings_directory_path(recordings_directory_path)
        IPTVProxySecurityManager.set_certificate_file_path(certificate_file_path)
        IPTVProxySecurityManager.set_key_file_path(key_file_path)

        IPTVProxyConfiguration.read_configuration_file()
        try:
            IPTVProxyUtility.set_logging_level(
                getattr(logging, IPTVProxyConfiguration.get_configuration_parameter('LOGGING_LEVEL').upper()))
        except AttributeError:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

        cls.read_optional_settings()

        IPTVProxyDB.initialize()
        IPTVProxyHTTPRequestHandler.initialize()
        IPTVProxyPVR.initialize()
        IPTVProxySecurityManager.initialize()

        for provider in IPTVProxyConfiguration.get_providers().values():
            provider['api'].initialize()

            provider['epg'].initialize()

        IPTVProxyConfiguration.start_configuration_file_watchdog_observer()

        cls.start_http_server()
        cls.start_https_server()

        IPTVProxyPVR.start()

        while not cls._shutdown_proxy_event.is_set():
            if cls._http_server_thread:
                cls._http_server_thread.join()

            if cls._https_server_thread:
                cls._https_server_thread.join()

            cls._shutdown_proxy_event.wait(0.5)

        IPTVProxyConfiguration.join_configuration_file_watchdog_observer()
