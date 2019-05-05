import logging

from sqlalchemy import and_
from sqlalchemy.sql import func

from iptv_proxy.data_access import DatabaseAccess
from iptv_proxy.providers import ProvidersController

logger = logging.getLogger(__name__)


class ProviderDatabaseAccess():
    __slots__ = []

    _provider_name = None

    @classmethod
    def delete_channels(cls, db_session):
        db_session.query(ProvidersController.get_provider_map_class(cls._provider_name).channel_class()).delete()

    @classmethod
    def delete_programs(cls, db_session):
        program_class = ProvidersController.get_provider_map_class(cls._provider_name).program_class()

        db_session.query(program_class).delete()

    @classmethod
    def delete_setting(cls, db_session, setting_name):
        DatabaseAccess.delete_setting(db_session, setting_name)

    @classmethod
    def query_channel_name_by_channel_number(cls, db_session, channel_number):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class.name).filter(and_(channel_class.number == channel_number)).first()

    @classmethod
    def query_channels(cls, db_session):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class).order_by(channel_class.number).yield_per(1)

    @classmethod
    def query_channels_complete_xmltv(cls, db_session):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class.complete_xmltv.label('xmltv')).order_by(channel_class.number).yield_per(1)

    @classmethod
    def query_channels_pickle(cls, db_session):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class.pickle).order_by(channel_class.number).yield_per(1)

    @classmethod
    def query_channels_pickle_in_m3u8_group(cls, db_session, channel_m3u8_group):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class.pickle).filter(channel_class.m3u8_group == channel_m3u8_group).order_by(
            channel_class.number).all()

    @classmethod
    def query_channels_m3u8_groups(cls, db_session):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class.m3u8_group).distinct().yield_per(1)

    @classmethod
    def query_channels_minimal_xmltv(cls, db_session):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(channel_class.minimal_xmltv.label('xmltv')).order_by(channel_class.number).yield_per(1)

    @classmethod
    def query_minimum_maximum_channel_numbers(cls, db_session):
        channel_class = ProvidersController.get_provider_map_class(cls._provider_name).channel_class()

        return db_session.query(func.min(channel_class.number).label('minimum_channel_number'),
                                func.max(channel_class.number).label('maximum_channel_number')).first()

    @classmethod
    def query_programs_pickle_by_channel_xmltv_id_start_stop(cls,
                                                             db_session,
                                                             channel_xmltv_id,
                                                             program_start_cutoff,
                                                             program_stop_cutoff):
        program_class = ProvidersController.get_provider_map_class(cls._provider_name).program_class()

        return db_session.query(program_class.pickle).filter(and_(program_class.channel_xmltv_id == channel_xmltv_id,
                                                                  program_class.start < program_start_cutoff,
                                                                  program_class.stop > program_stop_cutoff)).order_by(
            program_class.start).all()

    @classmethod
    def query_programs_complete_xmltv(cls, db_session, program_start_cutoff):
        program_class = ProvidersController.get_provider_map_class(cls._provider_name).program_class()

        return db_session.query(program_class.complete_xmltv.label('xmltv')).filter(
            program_class.start < program_start_cutoff).order_by(program_class.channel_number,
                                                                 program_class.start).yield_per(1)

    @classmethod
    def query_programs_minimal_xmltv(cls, db_session, program_start_cutoff):
        program_class = ProvidersController.get_provider_map_class(cls._provider_name).program_class()

        return db_session.query(program_class.minimal_xmltv.label('xmltv')).filter(
            program_class.start < program_start_cutoff).order_by(program_class.channel_number,
                                                                 program_class.start).yield_per(1)

    @classmethod
    def query_setting(cls, db_session, setting_name):
        return DatabaseAccess.query_setting(db_session, setting_name)

    @classmethod
    def query_settings(cls, db_session):
        return DatabaseAccess.query_settings(db_session)
