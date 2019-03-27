import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


class IPTVProxyProviderSQL():
    @classmethod
    def delete_channels(cls, db, provider):
        sql_statement = 'DELETE ' \
                        'FROM channel ' \
                        'WHERE provider = :provider'
        db.execute(sql_statement, {'provider': provider})

    @classmethod
    def delete_channels_temp(cls, db, provider):
        sql_statement = 'DELETE ' \
                        'FROM channel_temp ' \
                        'WHERE provider = :provider'
        db.execute(sql_statement, {'provider': provider})

    @classmethod
    def delete_programs(cls, db, provider):
        sql_statement = 'DELETE ' \
                        'FROM program ' \
                        'WHERE provider = :provider'
        db.execute(sql_statement, {'provider': provider})

    @classmethod
    def delete_programs_temp(cls, db, provider):
        sql_statement = 'DELETE ' \
                        'FROM program_temp ' \
                        'WHERE provider = :provider'
        db.execute(sql_statement, {'provider': provider})

    @classmethod
    def insert_channel(cls, db, channel, provider):
        try:
            sql_statement = 'INSERT ' \
                            'INTO channel_temp (id, provider, number, name, icon_data_uri, icon_url, "group") ' \
                            'VALUES (:id, :provider, :number, :name, :icon_data_uri, :icon_url, :group)'
            db.execute(sql_statement, {'id': channel.id,
                                       'provider': provider,
                                       'number': channel.number,
                                       'name': channel.name,
                                       'icon_data_uri': channel.icon_data_uri,
                                       'icon_url': channel.icon_url,
                                       'group': channel.group})
        except sqlite3.IntegrityError:
            pass

    @classmethod
    def insert_program(cls, db, channel_id, program, provider):
        try:
            sql_statement = 'INSERT ' \
                            'INTO program_temp (channel_id, provider, start_date_time_in_utc, ' \
                            'end_date_time_in_utc, title, sub_title, description) ' \
                            'VALUES (:channel_id, :provider, :start_date_time_in_utc, :end_date_time_in_utc, :title, ' \
                            ':sub_title, :description)'
            db.execute(sql_statement, {'channel_id': channel_id,
                                       'provider': provider,
                                       'start_date_time_in_utc': datetime.strftime(program.start_date_time_in_utc,
                                                                                   '%Y-%m-%d %H:%M:%S%z'),
                                       'end_date_time_in_utc': datetime.strftime(program.end_date_time_in_utc,
                                                                                 '%Y-%m-%d %H:%M:%S%z'),
                                       'title': program.title,
                                       'sub_title': program.sub_title,
                                       'description': program.description})
        except sqlite3.IntegrityError:
            pass

    @classmethod
    def insert_select_channels(cls, db, provider):
        sql_statement = 'INSERT ' \
                        'INTO channel ' \
                        '  SELECT *' \
                        '  FROM channel_temp ' \
                        '  WHERE provider = :provider'
        db.execute(sql_statement, {'provider': provider})

    @classmethod
    def insert_select_programs(cls, db, provider):
        sql_statement = 'INSERT ' \
                        'INTO program ' \
                        '  SELECT *' \
                        '  FROM program_temp ' \
                        '  WHERE provider = :provider'
        db.execute(sql_statement, {'provider': provider})

    @classmethod
    def query_channel_by_channel_number(cls, db, channel_number, provider):
        sql_statement = 'SELECT * ' \
                        'FROM channel ' \
                        'WHERE provider = :provider ' \
                        '  AND number = :channel_number'
        channel_records = db.execute(sql_statement, {'provider': provider,
                                                     'channel_number': channel_number})

        return channel_records

    @classmethod
    def query_channels(cls, db, provider):
        sql_statement = 'SELECT * ' \
                        'FROM channel ' \
                        'WHERE provider = :provider'
        channel_records = db.execute(sql_statement, {'provider': provider})

        return channel_records

    @classmethod
    def query_minimum_maximum_channel_numbers(cls, db, provider):
        sql_statement = 'SELECT MIN(CAST(number as INTEGER)), MAX(CAST(number as INTEGER)) ' \
                        'FROM channel ' \
                        'WHERE provider = :provider'
        minimum_maximum_channel_number_records = db.execute(sql_statement, {'provider': provider})

        return minimum_maximum_channel_number_records

    @classmethod
    def query_programs_by_channel_id(cls, db, channel_id, provider):
        sql_statement = 'SELECT * ' \
                        'FROM program ' \
                        'WHERE provider = :provider ' \
                        '  AND channel_id = :channel_id'
        program_records = db.execute(sql_statement, {'provider': provider,
                                                     'channel_id': channel_id})

        return program_records
