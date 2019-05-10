import logging
import os
import shutil
import sys
import traceback
from abc import ABC
from abc import abstractmethod

from pysqlite3 import dbapi2 as sqlite3
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
Base = declarative_base()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()

    cursor.execute('PRAGMA cache_size = "-8192"')
    cursor.execute('PRAGMA foreign_keys = "0"')
    cursor.execute('PRAGMA journal_mode = "WAL"')
    cursor.execute('PRAGMA secure_delete = "0"')
    cursor.execute('PRAGMA synchronous = "0"')

    cursor.close()


class ProviderDatabase(ABC):
    __slots__ = []

    _access_lock = None
    _database_file_path = None
    _engine = None
    _session_factory = None
    _temporary_database_file_path = None
    _temporary_engine = None
    _temporary_session_factory = None
    _write_lock = None

    @classmethod
    @abstractmethod
    def _migrate(cls, old_db_session, new_db_session):
        pass

    @classmethod
    def create_session(cls):
        return cls._session_factory()

    @classmethod
    def create_temporary_session(cls):
        return cls._temporary_session_factory()

    @classmethod
    def get_access_lock(cls):
        return cls._access_lock

    @classmethod
    def get_write_lock(cls):
        return cls._write_lock

    @classmethod
    def initialize(cls):
        cls._engine = create_engine('sqlite:///{0}'.format(cls._database_file_path), echo=False, module=sqlite3)
        cls._session_factory = sessionmaker(cls._engine, autoflush=False, expire_on_commit=False)

        cls._access_lock.exclusive_lock = cls._access_lock.writer_lock
        cls._access_lock.shared_lock = cls._access_lock.reader_lock

    @classmethod
    def initialize_temporary(cls):
        try:
            os.remove(cls._temporary_database_file_path)
        except Exception:
            pass

        cls._temporary_engine = create_engine('sqlite:///{0}'.format(cls._temporary_database_file_path),
                                              echo=False,
                                              module=sqlite3)
        cls._temporary_session_factory = sessionmaker(cls._temporary_engine, autoflush=False, expire_on_commit=False)

    @classmethod
    def migrate(cls):
        with cls._access_lock.exclusive_lock:
            old_db_session = cls._session_factory()
            new_db_session = cls._temporary_session_factory()

            try:
                cls._migrate(old_db_session, new_db_session)

                new_db_session.commit()

                shutil.move(cls._temporary_database_file_path, cls._database_file_path)
            except Exception:
                new_db_session.rollback()

                shutil.rmtree(cls._temporary_database_file_path)

                (type_, value_, traceback_) = sys.exc_info()
                logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                raise
            finally:
                old_db_session.close()
                new_db_session.close()

                cls._temporary_database_file_path = None
                cls._temporary_engine = None
                cls._temporary_session_factory = None
