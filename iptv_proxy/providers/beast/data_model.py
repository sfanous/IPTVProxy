import logging

from sqlalchemy import Column
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property

from iptv_proxy.data_model import DateTimeUTC
from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.beast.db import Base

logger = logging.getLogger(__name__)


class BeastChannel(Base):
    _provider_name = BeastConstants.PROVIDER_NAME.lower()

    __tablename__ = 'channel'

    _id = Column('id', String, primary_key=True, autoincrement=False)
    _m3u8_group = Column('m3u8_group', String, nullable=False)
    _number = Column('number', Integer, nullable=False)
    _name = Column('name', String, nullable=False)
    _pickle = Column('pickle', LargeBinary, nullable=False)
    _complete_xmltv = Column('complete_xmltv', String, nullable=False)
    _minimal_xmltv = Column('minimal_xmltv', String, nullable=False)

    __table_args__ = (Index('{0}_channel_ix_id'.format(_provider_name), _id.asc()),
                      Index('{0}_channel_ix_m3u8_group'.format(_provider_name), _m3u8_group.asc()),
                      Index('{0}_channel_ix_m3u8_group_&_number'.format(_provider_name),
                            _m3u8_group.asc(),
                            _number.asc()),
                      Index('{0}_channel_ix_number'.format(_provider_name), _number.asc()))

    def __init__(self, id_, m3u8_group, number, name, pickle, complete_xmltv, minimal_xmltv):
        self._id = id_
        self._m3u8_group = m3u8_group
        self._number = number
        self._name = name
        self._pickle = pickle
        self._complete_xmltv = complete_xmltv
        self._minimal_xmltv = minimal_xmltv

    @hybrid_property
    def complete_xmltv(self):
        return self._complete_xmltv

    @complete_xmltv.setter
    def complete_xmltv(self, complete_xmltv):
        self._complete_xmltv = complete_xmltv

    @hybrid_property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @hybrid_property
    def m3u8_group(self):
        return self._m3u8_group

    @m3u8_group.setter
    def m3u8_group(self, m3u8_group):
        self._m3u8_group = m3u8_group

    @hybrid_property
    def minimal_xmltv(self):
        return self._minimal_xmltv

    @minimal_xmltv.setter
    def minimal_xmltv(self, minimal_xmltv):
        self._minimal_xmltv = minimal_xmltv

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @hybrid_property
    def number(self):
        return self._number

    @number.setter
    def number(self, number):
        self._number = number

    @hybrid_property
    def pickle(self):
        return self._pickle

    @pickle.setter
    def pickle(self, pickle):
        self._pickle = pickle


class BeastProgram(Base):
    _provider_name = BeastConstants.PROVIDER_NAME.lower()

    __tablename__ = 'program'

    _id = Column('id', String, primary_key=True, autoincrement=False)
    _start = Column('start', DateTimeUTC(timezone=True), nullable=False)
    _stop = Column('stop', DateTimeUTC(timezone=True), nullable=False)
    _channel_xmltv_id = Column('channel_xmltv_id', String, nullable=False)
    _channel_number = Column('channel_number', Integer, nullable=False)
    _pickle = Column('pickle', LargeBinary, nullable=False)
    _complete_xmltv = Column('complete_xmltv', String, nullable=False)
    _minimal_xmltv = Column('minimal_xmltv', String, nullable=False)

    __table_args__ = (
        Index('{0}_program_ix_id'.format(_provider_name), _id.asc()),
        Index('{0}_program_ix_channel_number_&_start'.format(_provider_name), _channel_number.asc(), _start.asc()),
        Index('{0}_program_ix_channel_xmltv_id_&_start'.format(_provider_name), _channel_xmltv_id.asc(), _start.asc()),
        Index('{0}_program_ix_channel_xmltv_id_&_start_&_stop'.format(_provider_name),
              _channel_xmltv_id.asc(),
              _start.asc(),
              _stop.asc()),
        Index('{0}_program_ix_start'.format(_provider_name), _start.asc()))

    def __init__(self,
                 id_,
                 start,
                 stop,
                 channel_xmltv_id,
                 channel_number,
                 pickle,
                 complete_xmltv,
                 minimal_xmltv):
        self._id = id_
        self._start = start
        self._stop = stop
        self._channel_xmltv_id = channel_xmltv_id
        self._channel_number = channel_number
        self._pickle = pickle
        self._complete_xmltv = complete_xmltv
        self._minimal_xmltv = minimal_xmltv

    @hybrid_property
    def channel_number(self):
        return self._channel_number

    @channel_number.setter
    def channel_number(self, channel_number):
        self._channel_number = channel_number

    @hybrid_property
    def channel_xmltv_id(self):
        return self._channel_xmltv_id

    @channel_xmltv_id.setter
    def channel_xmltv_id(self, channel_xmltv_id):
        self._channel_xmltv_id = channel_xmltv_id

    @hybrid_property
    def complete_xmltv(self):
        return self._complete_xmltv

    @complete_xmltv.setter
    def complete_xmltv(self, complete_xmltv):
        self._complete_xmltv = complete_xmltv

    @hybrid_property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @hybrid_property
    def minimal_xmltv(self):
        return self._minimal_xmltv

    @minimal_xmltv.setter
    def minimal_xmltv(self, minimal_xmltv):
        self._minimal_xmltv = minimal_xmltv

    @hybrid_property
    def pickle(self):
        return self._pickle

    @pickle.setter
    def pickle(self, pickle):
        self._pickle = pickle

    @hybrid_property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @hybrid_property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, stop):
        self._stop = stop


class BeastSetting(Base):
    _provider_name = BeastConstants.PROVIDER_NAME.lower()

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
