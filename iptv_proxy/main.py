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

        (
            configuration_file_path,
            optional_settings_file_path,
            db_file_path,
            log_file_path,
            recordings_directory_path,
            certificate_file_path,
            key_file_path,
        ) = Utility.parse_command_line_arguments()

        Logging.initialize_logging(log_file_path)

        logger.info(
            'Starting IPTV Proxy %s\n'
            'Configuration file path     => %s\n'
            'Optional settings file path => %s\n'
            'Database file path          => %s\n'
            'Log file path               => %s\n'
            'Recordings directory path   => %s\n'
            'SSL certificate file path   => %s\n'
            'SSL key file path           => %s',
            VERSION,
            configuration_file_path,
            optional_settings_file_path,
            db_file_path,
            log_file_path,
            recordings_directory_path,
            certificate_file_path,
            key_file_path,
        )

        Controller.start_proxy(
            configuration_file_path,
            optional_settings_file_path,
            db_file_path,
            log_file_path,
            recordings_directory_path,
            certificate_file_path,
            key_file_path,
        )

        logger.info('Shutting down IPTV Proxy %s', VERSION)
    except Exception:
        (type_, value_, traceback_) = sys.exc_info()
        logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))
