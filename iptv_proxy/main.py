import logging
import sys
import traceback

from .constants import VERSION
from .controller import IPTVProxyController
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


def main():
    # noinspection PyBroadException
    try:
        (configuration_file_path,
         db_file_path,
         log_file_path,
         recordings_directory_path,
         certificate_file_path,
         key_file_path) = IPTVProxyUtility.parse_command_line_arguments()

        IPTVProxyUtility.initialize_logging(log_file_path)

        logger.info('Starting IPTV Proxy {0}\n'
                    'Configuration file path   => {1}\n'
                    'Database file path        => {2}\n'
                    'Log file path             => {3}\n'
                    'Recordings directory path => {4}\n'
                    'SSL certificate file path => {5}\n'
                    'SSL key file path         => {6}'.format(VERSION,
                                                              configuration_file_path,
                                                              db_file_path,
                                                              log_file_path,
                                                              recordings_directory_path,
                                                              certificate_file_path,
                                                              key_file_path))

        IPTVProxyController.start_proxy(configuration_file_path,
                                        db_file_path,
                                        recordings_directory_path,
                                        certificate_file_path,
                                        key_file_path)

        logger.info('Shutting down IPTV Proxy {0}'.format(VERSION))
    except Exception:
        (type_, value_, traceback_) = sys.exc_info()
        logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))
