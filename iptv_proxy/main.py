import logging
import sys
import traceback

from iptv_proxy.constants import VERSION
from iptv_proxy.controller import Controller
from iptv_proxy.logging import Logging
from iptv_proxy.privilege import Privilege
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


def main():
    try:
        Privilege.initialize()
        Privilege.become_unprivileged_user()

        (configuration_file_path,
         optional_settings_file_path,
         db_file_path,
         log_file_path,
         recordings_directory_path,
         certificate_file_path,
         key_file_path) = Utility.parse_command_line_arguments()

        Logging.initialize_logging(log_file_path)

        logger.info('Starting IPTV Proxy {0}\n'
                    'Configuration file path     => {1}\n'
                    'Optional settings file path => {2}\n'
                    'Database file path          => {3}\n'
                    'Log file path               => {4}\n'
                    'Recordings directory path   => {5}\n'
                    'SSL certificate file path   => {6}\n'
                    'SSL key file path           => {7}'.format(VERSION,
                                                                configuration_file_path,
                                                                optional_settings_file_path,
                                                                db_file_path,
                                                                log_file_path,
                                                                recordings_directory_path,
                                                                certificate_file_path,
                                                                key_file_path))

        Controller.start_proxy(configuration_file_path,
                               optional_settings_file_path,
                               db_file_path,
                               log_file_path,
                               recordings_directory_path,
                               certificate_file_path,
                               key_file_path)

        logger.info('Shutting down IPTV Proxy {0}'.format(VERSION))
    except Exception:
        (type_, value_, traceback_) = sys.exc_info()
        logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))
