import logging
from datetime import datetime
from datetime import timedelta
from threading import Timer

import ZODB
import transaction
import tzlocal
from ZODB.FileStorage import FileStorage
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

from .constants import MAXIMUM_NUMBER_OF_CHANGED_OBJECTS

logger = logging.getLogger(__name__)


class IPTVProxyDB():
    __slots__ = ['_connection', '_number_of_changed_objects', '_root']

    _db = None
    _db_file_path = None
    _pack_timer = None

    @classmethod
    def _initialize_db(cls):
        do_commit_transaction = False

        cls._db = ZODB.DB(FileStorage(cls._db_file_path))
        connection = cls._db.open()
        root = connection.root()

        if 'IPTVProxy' not in root:
            do_commit_transaction = True

            root['IPTVProxy'] = PersistentMapping()
        if 'files' not in root['IPTVProxy']:
            do_commit_transaction = True

            root['IPTVProxy']['files'] = PersistentMapping()
        if 'http_server_active_sessions' not in root['IPTVProxy']:
            do_commit_transaction = True

            root['IPTVProxy']['http_server_active_sessions'] = PersistentMapping()
        if 'recordings' not in root['IPTVProxy']:
            do_commit_transaction = True

            root['IPTVProxy']['recordings'] = PersistentList()

        if do_commit_transaction:
            transaction.commit()

        connection.close()

    @classmethod
    def _initialize_pack_timer(cls):
        current_date_time_in_local = datetime.now(tzlocal.get_localzone())

        connection = cls._db.open()
        root = connection.root()

        try:
            last_db_pack_date_time_in_local = root['IPTVProxy']['last_db_pack_date_time_in_local']

            if current_date_time_in_local >= \
                    (last_db_pack_date_time_in_local + timedelta(days=1)).replace(hour=4,
                                                                                  minute=30,
                                                                                  second=0,
                                                                                  microsecond=0):
                pack_date_time_in_local = current_date_time_in_local
            else:
                pack_date_time_in_local = (current_date_time_in_local + timedelta(days=1)).replace(hour=4,
                                                                                                   minute=30,
                                                                                                   second=0,
                                                                                                   microsecond=0)
        except KeyError:
            pack_date_time_in_local = current_date_time_in_local

        connection.close()

        interval = (pack_date_time_in_local - current_date_time_in_local).total_seconds()

        cls._pack_timer = Timer(interval, cls._pack)
        cls._pack_timer.daemon = True
        cls._pack_timer.start()

        logger.debug('Started DB packing timer\n'
                     'Interval => {0} seconds'.format(interval))

    @classmethod
    def _pack(cls):
        cls._db.pack()

        logger.debug('Packed DB')

        connection = cls._db.open()
        root = connection.root()

        root['IPTVProxy']['last_db_pack_date_time_in_local'] = datetime.now(tzlocal.get_localzone())

        transaction.commit()
        connection.close()

        cls._initialize_pack_timer()

    @classmethod
    def initialize(cls):
        cls._initialize_db()
        cls._initialize_pack_timer()

    @classmethod
    def set_db_file_path(cls, db_file_path):
        cls._db_file_path = db_file_path

    @classmethod
    def terminate(cls):
        if cls._pack_timer:
            cls._pack_timer.cancel()

        cls._db.close()

    def __init__(self):
        self._connection = IPTVProxyDB._db.open()
        self._number_of_changed_objects = 0
        self._root = self._connection.root()

    def abort(self):
        transaction.abort()

        self._number_of_changed_objects = 0

    def commit(self):
        transaction.commit()

        self._number_of_changed_objects = 0

    def close(self, do_commit_transaction=False):
        if do_commit_transaction:
            self.commit()
        else:
            self.abort()

        self._connection.close()

    def has_keys(self, keys):
        key_to_check = self._root['IPTVProxy']

        for key in keys:
            if key not in key_to_check:
                return False
            key_to_check = key_to_check[key]

        return True

    def persist(self, keys, value):
        key_to_persist = self._root['IPTVProxy']

        for key in keys[:-1]:
            key_to_persist = key_to_persist[key]

        key_to_persist[keys[-1]] = value

    def retrieve(self, keys):
        key_to_retrieve = self._root['IPTVProxy']

        for key in keys:
            key_to_retrieve = key_to_retrieve[key]

        return key_to_retrieve

    def savepoint(self, number_of_newly_changed_objects):
        self._number_of_changed_objects += number_of_newly_changed_objects

        if self._number_of_changed_objects >= MAXIMUM_NUMBER_OF_CHANGED_OBJECTS:
            transaction.savepoint()

            self._number_of_changed_objects = 0
