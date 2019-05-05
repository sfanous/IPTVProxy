import logging

from sqlalchemy import func

from iptv_proxy.data_model import HTTPSession
from iptv_proxy.data_model import Recording
from iptv_proxy.data_model import Segment
from iptv_proxy.data_model import Setting
from iptv_proxy.enums import RecordingStatus

logger = logging.getLogger(__name__)


class DatabaseAccess(object):
    __slots__ = []

    @classmethod
    def delete_http_session(cls, db_session, http_session_id):
        db_session.query(HTTPSession).filter(HTTPSession.id == http_session_id).delete()

    @classmethod
    def delete_http_sessions(cls, db_session):
        db_session.query(HTTPSession).delete()

    @classmethod
    def delete_recording(cls, db_session, recording_id):
        db_session.query(Recording).filter(Recording.id == recording_id).delete()

    @classmethod
    def delete_segments(cls, db_session, recording_id):
        db_session.query(Segment).filter(Segment.recording_id == recording_id).delete()

    @classmethod
    def delete_setting(cls, db_session, setting_name):
        db_session.query(Setting).filter(Setting.name == setting_name).delete()

    @classmethod
    def query_http_session(cls, db_session, http_session_id):
        return db_session.query(HTTPSession).filter(HTTPSession.id == http_session_id).first()

    @classmethod
    def query_http_sessions(cls, db_session):
        return db_session.query(HTTPSession).yield_per(1)

    @classmethod
    def query_live_recordings(cls, db_session):
        return db_session.query(Recording).filter(Recording.status == RecordingStatus.LIVE.value).yield_per(1)

    @classmethod
    def query_persisted_recordings(cls, db_session):
        return db_session.query(Recording).filter(Recording.status == RecordingStatus.PERSISTED.value).yield_per(1)

    @classmethod
    def query_recording(cls, db_session, recording_id):
        return db_session.query(Recording).filter(Recording.id == recording_id).first()

    @classmethod
    def query_recordings(cls, db_session):
        return db_session.query(Recording).yield_per(1)

    @classmethod
    def query_scheduled_recordings(cls, db_session):
        return db_session.query(Recording).filter(Recording.status == RecordingStatus.SCHEDULED.value).yield_per(1)

    @classmethod
    def query_segments_directory_path(cls, db_session, recording_id):
        return db_session.query(Segment.directory_path).filter(
            Segment.recording_id == recording_id).distinct().yield_per(1)

    @classmethod
    def query_segments_count(cls, db_session, recording_id):
        return db_session.query(func.count(Segment.id).label('count')).filter(
            Segment.recording_id == recording_id).first()

    @classmethod
    def query_segment_directory_path(cls, db_session, segment_name, recording_id):
        return db_session.query(Segment.directory_path).filter(
            Segment.name == segment_name,
            Segment.recording_id == recording_id).first()

    @classmethod
    def query_segment_pickle(cls, db_session, recording_id):
        return db_session.query(Segment.pickle).filter(
            Segment.recording_id == recording_id).order_by(Segment.id).yield_per(1)

    @classmethod
    def query_setting(cls, db_session, setting_name):
        return db_session.query(Setting).filter(Setting.name == setting_name).first()

    @classmethod
    def query_settings(cls, db_session):
        return db_session.query(Setting).yield_per(1)
