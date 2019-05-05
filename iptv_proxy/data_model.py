import logging
import uuid
from datetime import datetime
from datetime import timedelta

import pytz
from sqlalchemy import Column
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import TypeDecorator
from sqlalchemy import UniqueConstraint
from sqlalchemy import types
from sqlalchemy.ext.hybrid import hybrid_property

from iptv_proxy.db import Base

logger = logging.getLogger(__name__)


class DateTimeUTC(TypeDecorator):
    impl = types.DateTime

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=pytz.utc)


class HTTPSession(Base):
    __tablename__ = 'http_session'

    _id = Column('id', String, primary_key=True, autoincrement=False)
    _client_ip_address = Column('client_ip_address', String, nullable=False)
    _user_agent = Column('_user_agent', String, nullable=False)
    _expiry_date_time_in_utc = Column('expiry_date_time_in_utc', DateTimeUTC(timezone=True), nullable=False)
    _last_access_date_time_in_utc = Column('last_access_date_time_in_utc', DateTimeUTC(timezone=True), nullable=False)

    __table_args__ = (Index('http_session_ix_id', _id.asc()),)

    def __init__(self, client_ip_address, user_agent):
        current_date_time_in_utc = datetime.now(pytz.utc)

        self._id = '{0}'.format(uuid.uuid4())
        self._client_ip_address = client_ip_address
        self._user_agent = user_agent
        self._last_access_date_time_in_utc = current_date_time_in_utc
        self._expiry_date_time_in_utc = current_date_time_in_utc + timedelta(days=7)

    @hybrid_property
    def client_ip_address(self):
        return self._client_ip_address

    @client_ip_address.setter
    def client_ip_address(self, client_ip_address):
        self._client_ip_address = client_ip_address

    @hybrid_property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @hybrid_property
    def expiry_date_time_in_utc(self):
        return self._expiry_date_time_in_utc

    @expiry_date_time_in_utc.setter
    def expiry_date_time_in_utc(self, expiry_date_time_in_utc):
        self._expiry_date_time_in_utc = expiry_date_time_in_utc

    @hybrid_property
    def last_access_date_time_in_utc(self):
        return self._last_access_date_time_in_utc

    @last_access_date_time_in_utc.setter
    def last_access_date_time_in_utc(self, last_access_date_time_in_utc):
        self._last_access_date_time_in_utc = last_access_date_time_in_utc

    @hybrid_property
    def user_agent(self):
        return self._user_agent

    @user_agent.setter
    def user_agent(self, user_agent):
        self._user_agent = user_agent


class Recording(Base):
    __tablename__ = 'recording'

    _id = Column('id', String, primary_key=True, autoincrement=False)
    _provider = Column('provider', String, nullable=False)
    _channel_number = Column('channel_number', Integer, nullable=False)
    _channel_name = Column('channel_name', String, nullable=False)
    _program_title = Column('program_title', String, nullable=False)
    _start_date_time_in_utc = Column('start', DateTimeUTC(timezone=True), nullable=False)
    _end_date_time_in_utc = Column('stop', DateTimeUTC(timezone=True), nullable=False)
    _status = Column('status', String, nullable=False)

    __table_args__ = (Index('recording_ix_id', _id.asc()),
                      Index('recording_ix_status', _status.asc()),
                      UniqueConstraint('provider', 'channel_number', 'start', 'stop'))

    def __init__(self,
                 id_,
                 provider,
                 channel_number,
                 channel_name,
                 program_title,
                 start_date_time_in_utc,
                 end_date_time_in_utc,
                 status):
        self._id = id_
        self._provider = provider
        self._channel_number = channel_number
        self._channel_name = channel_name
        self._program_title = program_title
        self._start_date_time_in_utc = start_date_time_in_utc
        self._end_date_time_in_utc = end_date_time_in_utc
        self._status = status

    @hybrid_property
    def channel_name(self):
        return self._channel_name

    @channel_name.setter
    def channel_name(self, channel_name):
        self._channel_name = channel_name

    @hybrid_property
    def channel_number(self):
        return self._channel_number

    @channel_number.setter
    def channel_number(self, channel_number):
        self._channel_number = channel_number

    @hybrid_property
    def end_date_time_in_utc(self):
        return self._end_date_time_in_utc

    @end_date_time_in_utc.setter
    def end_date_time_in_utc(self, end_date_time_in_utc):
        self._end_date_time_in_utc = end_date_time_in_utc

    @hybrid_property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @hybrid_property
    def program_title(self):
        return self._program_title

    @program_title.setter
    def program_title(self, program_title):
        self._program_title = program_title

    @hybrid_property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, provider):
        self._provider = provider

    @hybrid_property
    def start_date_time_in_utc(self):
        return self._start_date_time_in_utc

    @start_date_time_in_utc.setter
    def start_date_time_in_utc(self, start_date_time_in_utc):
        self._start_date_time_in_utc = start_date_time_in_utc

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status


class Segment(Base):
    __tablename__ = 'segment'

    _id = Column('id', Integer, primary_key=True, autoincrement=True)
    _name = Column('name', String, nullable=False)
    _recording_id = Column('recording_id', String, nullable=False)
    _pickle = Column('pickle', LargeBinary, nullable=False)
    _directory_path = Column('directory_path', String, nullable=False)

    __table_args__ = (Index('segment_ix_id', _id.asc()),
                      Index('segment_ix_id_name', _id.asc(), _name.asc()),
                      Index('segment_ix_name_recording_id', _recording_id.asc(), _name.asc()),
                      Index('segment_ix_recording_id', _recording_id.asc()),
                      Index('segment_ix_recording_id_directory_path', _recording_id.asc(), _directory_path.asc()),
                      Index('segment_ix_recording_id_id', _recording_id.asc(), _id.asc()))

    def __init__(self, name, recording_id, pickle, directory_path):
        self._name = name
        self._recording_id = recording_id
        self._pickle = pickle
        self._directory_path = directory_path

    @hybrid_property
    def directory_path(self):
        return self._directory_path

    @directory_path.setter
    def directory_path(self, directory_path):
        self._directory_path = directory_path

    @hybrid_property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @hybrid_property
    def pickle(self):
        return self._pickle

    @pickle.setter
    def pickle(self, pickle):
        self._pickle = pickle

    @hybrid_property
    def recording_id(self):
        return self._recording_id

    @recording_id.setter
    def recording_id(self, recording_id):
        self._recording_id = recording_id


class Setting(Base):
    __tablename__ = 'setting'

    _name = Column('name', String, primary_key=True)
    _value = Column('value', String, nullable=False)

    __table_args__ = (Index('setting_ix_name', _name.asc()),)

    def __init__(self, name, value):
        self._name = name
        self._value = value

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @hybrid_property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
