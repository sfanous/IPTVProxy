import hashlib
import logging
import os
from threading import RLock

from watchdog.events import FileSystemEventHandler as FileSystemEventHandler_

from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class FileSystemEventHandler(FileSystemEventHandler_):
    def __init__(self, file_path):
        FileSystemEventHandler_.__init__(self)

        self._file_path = file_path
        self._last_file_version_md5_checksum = None
        self._lock = RLock()

    def _do_process_on_modified_event(self, event):
        do_process_on_modified_event = False

        if os.path.normpath(event.src_path) == os.path.normpath(self._file_path):
            if not self._last_file_version_md5_checksum:
                do_process_on_modified_event = True

                self._last_file_version_md5_checksum = hashlib.md5(
                    Utility.read_file(self._file_path, in_binary=True)).hexdigest()
            else:
                configuration_md5_checksum = hashlib.md5(
                    Utility.read_file(self._file_path, in_binary=True)).hexdigest()
                if configuration_md5_checksum != self._last_file_version_md5_checksum:
                    do_process_on_modified_event = True

                    self._last_file_version_md5_checksum = configuration_md5_checksum

        return do_process_on_modified_event
