import logging
import os
from threading import RLock

from rwlock import RWLock
from sqlalchemy.ext.declarative import declarative_base

from iptv_proxy.db import Database
from iptv_proxy.providers.iptv_provider.db import ProviderDatabase
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants
from iptv_proxy.providers.smoothstreams.data_access import SmoothStreamsDatabaseAccess

logger = logging.getLogger(__name__)
Base = declarative_base()


class SmoothStreamsDatabase(ProviderDatabase):
    __slots__ = []

    _access_lock = RWLock()
    _database_file_path = None
    _engine = None
    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
    _session_factory = None
    _temporary_database_file_path = None
    _temporary_engine = None
    _temporary_session_factory = None
    _write_lock = RLock()

    @classmethod
    def _migrate(cls, old_db_session, new_db_session):
        setting_row = SmoothStreamsDatabaseAccess.query_setting(
            old_db_session, 'session'
        )

        if setting_row is not None:
            new_db_session.merge(setting_row)

    @classmethod
    def initialize(cls):
        cls._database_file_path = os.path.join(
            os.path.dirname(Database.get_database_file_path()),
            SmoothStreamsConstants.DB_FILE_NAME,
        )

        super().initialize()

        Base.metadata.create_all(cls._engine)

    @classmethod
    def initialize_temporary(cls):
        cls._temporary_database_file_path = os.path.join(
            os.path.dirname(Database.get_database_file_path()),
            SmoothStreamsConstants.TEMPORARY_DB_FILE_NAME,
        )

        super().initialize_temporary()

        Base.metadata.create_all(cls._temporary_engine)
