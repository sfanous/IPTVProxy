import logging

from .constants import PROVIDER_NAME
from ..iptv_provider.db import IPTVProxyProviderSQL
from ...db import IPTVProxySQL

logger = logging.getLogger(__name__)


class VaderStreamsSQL(IPTVProxyProviderSQL):
    @classmethod
    def delete_channels(cls, db, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.delete_channels(db, provider)

    @classmethod
    def delete_channels_temp(cls, db, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.delete_channels_temp(db, provider)

    @classmethod
    def delete_programs(cls, db, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.delete_programs(db, provider)

    @classmethod
    def delete_programs_temp(cls, db, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.delete_programs_temp(db, provider)

    @classmethod
    def delete_setting(cls, db, name):
        IPTVProxySQL.delete_setting(db, 'vader_streams_{0}'.format(name))

    @classmethod
    def insert_channel(cls, db, channel, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.insert_channel(db, channel, provider)

    @classmethod
    def insert_program(cls, db, channel_id, program, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.insert_program(db, channel_id, program, provider)

    @classmethod
    def insert_select_channels(cls, db, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.insert_select_channels(db, provider)

    @classmethod
    def insert_select_programs(cls, db, provider=PROVIDER_NAME):
        IPTVProxyProviderSQL.insert_select_programs(db, provider)

    @classmethod
    def insert_setting(cls, db, name, value):
        IPTVProxySQL.insert_setting(db, 'vader_streams_{0}'.format(name), value)

    @classmethod
    def query_channel_by_channel_number(cls, db, channel_number, provider=PROVIDER_NAME):
        return IPTVProxyProviderSQL.query_channel_by_channel_number(db, channel_number, provider)

    @classmethod
    def query_channels(cls, db, provider=PROVIDER_NAME):
        return IPTVProxyProviderSQL.query_channels(db, provider)

    @classmethod
    def query_groups(cls, db, provider=PROVIDER_NAME):
        sql_statement = 'SELECT DISTINCT("group") ' \
                        'FROM channel ' \
                        'WHERE provider = :provider'
        group_records = db.execute(sql_statement, {'provider': provider})

        return group_records

    @classmethod
    def query_minimum_maximum_channel_numbers(cls, db, provider=PROVIDER_NAME):
        return IPTVProxyProviderSQL.query_minimum_maximum_channel_numbers(db, provider)

    @classmethod
    def query_programs_by_channel_id(cls, db, channel_id, provider=PROVIDER_NAME):
        return IPTVProxyProviderSQL.query_programs_by_channel_id(db, channel_id, provider)

    @classmethod
    def query_setting(cls, db, name):
        return IPTVProxySQL.query_setting(db, 'vader_streams_{0}'.format(name))
