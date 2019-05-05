import logging
from threading import RLock

from pysqlite3 import dbapi2 as sqlite3
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
Base = declarative_base()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()

    cursor.execute('PRAGMA cache_size = "-8192"')
    cursor.execute('PRAGMA foreign_keys = "0"')
    cursor.execute('PRAGMA journal_mode = "WAL"')
    cursor.execute('PRAGMA secure_delete = "0"')
    cursor.execute('PRAGMA synchronous = "0"')

    cursor.close()


class Database(object):
    __slots__ = []

    _database_file_path = None
    _engine = None
    _session_factory = None
    _write_lock = RLock()

    @classmethod
    def create_session(cls):
        return cls._session_factory()

    @classmethod
    def get_database_file_path(cls):
        return cls._database_file_path

    @classmethod
    def get_write_lock(cls):
        return cls._write_lock

    @classmethod
    def initialize(cls):
        cls._engine = create_engine('sqlite:///{0}'.format(cls._database_file_path), echo=False, module=sqlite3)
        cls._session_factory = sessionmaker(cls._engine, autoflush=False, expire_on_commit=False)

        Base.metadata.create_all(cls._engine)

    @classmethod
    def set_database_file_path(cls, database_file_path):
        cls._database_file_path = database_file_path
