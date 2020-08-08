import copy
import hashlib
import json
import logging
import logging.config
import os
import sys
import traceback

from watchdog.observers import Observer

from iptv_proxy.constants import DEFAULT_LOGGING_CONFIGURATION
from iptv_proxy.constants import LOGGING_CONFIGURATION_FILE_PATH
from iptv_proxy.constants import TRACE
from iptv_proxy.utilities import Utility
from iptv_proxy.watchdog_events import FileSystemEventHandler

logger = logging.getLogger(__name__)


def trace(self, msg, *args, **kwargs):
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)


class Logging(object):
    __slots__ = []

    _logging_configuration_file_watchdog_observer = None
    _log_file_path = None

    @classmethod
    def get_log_file_path(cls):
        return cls._log_file_path

    @classmethod
    def initialize_logging(cls, log_file_path):
        logging.addLevelName(TRACE, 'TRACE')
        logging.TRACE = TRACE
        logging.trace = trace
        logging.Logger.trace = trace

        try:
            cls.set_logging_configuration()
        except Exception:
            logging_configuration = copy.copy(DEFAULT_LOGGING_CONFIGURATION)
            logging_configuration['handlers']['rotating_file'][
                'filename'
            ] = log_file_path

            cls.set_logging_configuration(logging_configuration)

    @classmethod
    def join_logging_configuration_file_watchdog_observer(cls):
        cls._logging_configuration_file_watchdog_observer.join()

    @classmethod
    def set_logging_configuration(cls, configuration=None):
        if configuration is None:
            try:
                with open(
                    LOGGING_CONFIGURATION_FILE_PATH, 'r'
                ) as logging_configuration_file:
                    logging.config.dictConfig(json.load(logging_configuration_file))
            except FileNotFoundError:
                raise
            except Exception:
                (type_, value_, traceback_) = sys.exc_info()
                logger.error(
                    '\n'.join(traceback.format_exception(type_, value_, traceback_))
                )

                raise
        else:
            logging.config.dictConfig(configuration)

    @classmethod
    def set_log_file_path(cls, log_file_path):
        cls._log_file_path = log_file_path

    @classmethod
    def set_logging_level(cls, log_level):
        iptv_proxy_logger = logging.getLogger('iptv_proxy')

        iptv_proxy_logger.setLevel(log_level)

        for handler in iptv_proxy_logger.handlers:
            handler.setLevel(log_level)

    @classmethod
    def start_logging_configuration_file_watchdog_observer(cls):
        logging_configuration_event_handler = LoggingConfigurationEventHandler(
            LOGGING_CONFIGURATION_FILE_PATH
        )

        cls._logging_configuration_file_watchdog_observer = Observer()
        cls._logging_configuration_file_watchdog_observer.schedule(
            logging_configuration_event_handler,
            os.path.dirname(LOGGING_CONFIGURATION_FILE_PATH),
            recursive=False,
        )
        cls._logging_configuration_file_watchdog_observer.start()

    @classmethod
    def stop_logging_configuration_file_watchdog_observer(cls):
        cls._logging_configuration_file_watchdog_observer.stop()


class LoggingConfigurationEventHandler(FileSystemEventHandler):
    def __init__(self, logging_configuration_file_path):
        FileSystemEventHandler.__init__(self, logging_configuration_file_path)

    def on_created(self, event):
        with self._lock:
            if os.path.normpath(event.src_path) == os.path.normpath(self._file_path):
                self._last_file_version_md5_checksum = hashlib.md5(
                    Utility.read_file(self._file_path, in_binary=True)
                ).hexdigest()

                logger.debug(
                    'Detected creation of logging configuration file\n'
                    'Logging configuration file path => %s',
                    self._file_path,
                )

                Logging.set_logging_configuration()

    def on_deleted(self, event):
        with self._lock:
            if os.path.normpath(event.src_path) == os.path.normpath(self._file_path):
                self._last_file_version_md5_checksum = None

                logger.debug(
                    'Detected deletion of logging configuration file\n'
                    'Logging configuration file path => %s',
                    self._file_path,
                )

                logging_configuration = copy.copy(DEFAULT_LOGGING_CONFIGURATION)
                logging_configuration['handlers']['rotating_file'][
                    'filename'
                ] = Logging.get_log_file_path()

                Logging.set_logging_configuration(logging_configuration)

    def on_modified(self, event):
        with self._lock:
            if self._do_process_on_modified_event(event):
                logger.debug(
                    'Detected changes in logging configuration file\n'
                    'Logging configuration file path => %s',
                    self._file_path,
                )

                Logging.set_logging_configuration()
