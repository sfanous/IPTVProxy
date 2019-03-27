import logging
import sqlite3
from datetime import datetime
from sqlite3 import Row

from .constants import DEFAULT_DB_CREATE_SCHEMA_FILE_PATH
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class IPTVProxyDatabase(object):
    __slots__ = ['_connection', '_cursor']

    _database_file_path = None

    @classmethod
    def initialize(cls):
        connection = sqlite3.connect(IPTVProxyDatabase._database_file_path)
        cursor = connection.cursor()
        cursor.executescript(IPTVProxyUtility.read_file(DEFAULT_DB_CREATE_SCHEMA_FILE_PATH))
        cursor.close()
        connection.close()

    @classmethod
    def set_database_file_path(cls, database_file_path):
        cls._database_file_path = database_file_path

    def __init__(self):
        self._connection = sqlite3.connect(IPTVProxyDatabase._database_file_path)
        self._connection.row_factory = Row
        self._cursor = self._connection.cursor()

    def close_connection(self):
        self._cursor.close()
        self._connection.close()

    def commit(self):
        self._connection.commit()

    def execute(self, sql_statement, parameters):
        self._cursor.execute(sql_statement, parameters)

        return self._cursor.fetchall()


class IPTVProxySQL(object):
    __slots__ = []

    @classmethod
    def delete_http_session_by_id(cls, db, http_session_id):
        sql_statement = 'DELETE ' \
                        'FROM http_session ' \
                        'WHERE id = :id'
        db.execute(sql_statement, {'id': http_session_id})

    @classmethod
    def delete_http_sessions(cls, db):
        sql_statement = 'DELETE ' \
                        'FROM http_session'
        db.execute(sql_statement, {})

    @classmethod
    def delete_recording_by_id(cls, db, recording_id):
        sql_statement = 'DELETE ' \
                        'FROM recording ' \
                        'WHERE id = :id'
        db.execute(sql_statement, {'id': recording_id})

    @classmethod
    def insert_http_session(cls, db, http_session):
        sql_statement = 'INSERT ' \
                        'INTO http_session (id, client_ip_address, user_agent, last_access_date_time_in_utc, ' \
                        'expiry_date_time_in_utc) ' \
                        'VALUES (:id, :client_ip_address, :user_agent, :last_access_date_time_in_utc, ' \
                        ':expiry_date_time_in_utc)'
        db.execute(sql_statement, {'id': http_session.id,
                                   'client_ip_address': http_session.client_ip_address,
                                   'user_agent': http_session.user_agent,
                                   'last_access_date_time_in_utc': datetime.strftime(
                                       http_session.last_access_date_time_in_utc, '%Y-%m-%d %H:%M:%S%z'),
                                   'expiry_date_time_in_utc': datetime.strftime(http_session.expiry_date_time_in_utc,
                                                                                '%Y-%m-%d %H:%M:%S%z')})

    @classmethod
    def insert_recording(cls, db, recording):
        sql_statement = 'INSERT ' \
                        'INTO recording (id, provider, channel_number, channel_name, program_title, ' \
                        'start_date_time_in_utc, end_date_time_in_utc, status) ' \
                        'VALUES (:id, :provider, :channel_number, :channel_name, :program_title, ' \
                        ':start_date_time_in_utc, :end_date_time_in_utc, :status)'
        db.execute(sql_statement, {'id': recording.id,
                                   'provider': recording.provider,
                                   'channel_number': recording.channel_number,
                                   'channel_name': recording.channel_name,
                                   'program_title': recording.program_title,
                                   'start_date_time_in_utc': datetime.strftime(recording.start_date_time_in_utc,
                                                                               '%Y-%m-%d %H:%M:%S%z'),
                                   'end_date_time_in_utc': datetime.strftime(recording.end_date_time_in_utc,
                                                                             '%Y-%m-%d %H:%M:%S%z'),
                                   'status': recording.status})

    @classmethod
    def insert_setting(cls, db, name, value):
        sql_statement = 'REPLACE ' \
                        'INTO settings (name, value) ' \
                        'VALUES (:name, :value)'
        db.execute(sql_statement, {'name': name,
                                   'value': value})

    @classmethod
    def query_http_session_by_id(cls, db, http_session_id):
        sql_statement = 'SELECT * ' \
                        'FROM http_session ' \
                        'WHERE id = :id'
        http_session_records = db.execute(sql_statement, {'id': http_session_id})

        return http_session_records

    @classmethod
    def query_http_sessions(cls, db):
        sql_statement = 'SELECT * ' \
                        'FROM http_session'
        http_session_records = db.execute(sql_statement, {})

        return http_session_records

    @classmethod
    def query_live_recordings(cls, db):
        sql_statement = 'SELECT * ' \
                        'FROM recording ' \
                        'WHERE status = \'live\''
        live_recording_records = db.execute(sql_statement, {})

        return live_recording_records

    @classmethod
    def query_recording_by_id(cls, db, recording_id):
        sql_statement = 'SELECT * ' \
                        'FROM recording ' \
                        'WHERE id = :id'
        recording_records = db.execute(sql_statement, {'id': recording_id})

        return recording_records

    @classmethod
    def query_recordings(cls, db):
        sql_statement = 'SELECT * ' \
                        'FROM recording'
        recording_records = db.execute(sql_statement, {})

        return recording_records

    @classmethod
    def query_scheduled_recordings(cls, db):
        sql_statement = 'SELECT * ' \
                        'FROM recording ' \
                        'WHERE status = \'scheduled\''
        scheduled_recording_records = db.execute(sql_statement, {})

        return scheduled_recording_records

    @classmethod
    def query_setting(cls, db, name):
        sql_statement = 'SELECT value ' \
                        'FROM settings ' \
                        'WHERE name = :name'
        setting_records = db.execute(sql_statement, {'name': name})

        return setting_records
