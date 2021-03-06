import logging
import os
from threading import RLock

from rwlock import RWLock
from sqlalchemy.ext.declarative import declarative_base

from iptv_proxy.db import Database
from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.db import ProviderDatabase

logger = logging.getLogger(__name__)
Base = declarative_base()


class BeastDatabase(ProviderDatabase):
    __slots__ = []

    _access_lock = RWLock()
    _database_file_path = None
    _engine = None
    _provider_name = BeastConstants.PROVIDER_NAME.lower()
    _session_factory = None
    _temporary_database_file_path = None
    _temporary_engine = None
    _temporary_session_factory = None
    _write_lock = RLock()

    @classmethod
    def _migrate(cls, old_db_session, new_db_session):
        pass

    @classmethod
    def create_session(cls):
        return cls._session_factory()

    @classmethod
    def initialize(cls):
        cls._database_file_path = os.path.join(
            os.path.dirname(Database.get_database_file_path()),
            BeastConstants.DB_FILE_NAME,
        )

        super().initialize()

        Base.metadata.create_all(cls._engine)

    @classmethod
    def initialize_temporary(cls):
        cls._temporary_database_file_path = os.path.join(
            os.path.dirname(Database.get_database_file_path()),
            BeastConstants.TEMPORARY_DB_FILE_NAME,
        )

        super().initialize_temporary()

        Base.metadata.create_all(cls._temporary_engine)
