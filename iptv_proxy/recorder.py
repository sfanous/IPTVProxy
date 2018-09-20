import base64
import copy
import json
import logging.handlers
import math
import os
import re
import shutil
import sys
import time
import traceback
import urllib.parse
import uuid
from datetime import datetime
from threading import Event
from threading import RLock
from threading import Thread
from threading import Timer

import m3u8
import pytz
import requests
import tzlocal
from persistent import Persistent

from .configuration import IPTVProxyConfiguration
from .db import IPTVProxyDB
from .enums import IPTVProxyRecordingStatus
from .exceptions import IPTVProxyDuplicateRecordingError
from .exceptions import IPTVProxyRecordingNotFoundError
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class IPTVProxyPVR():
    __slots__ = []

    _live_recordings_to_recording_thread = {}
    _live_recordings_to_recording_thread_lock = RLock()
    _recordings_directory_path = None
    _start_recording_timer = None
    _start_recording_timer_lock = RLock()

    @classmethod
    def _get_persistent_recordings(cls):
        persistent_recordings = []

        recordings_directory_path = cls._recordings_directory_path
        recordings_top_level_directory = [recording_top_level_directory
                                          for recording_top_level_directory in os.listdir(recordings_directory_path)
                                          if os.path.isdir(os.path.join(recordings_directory_path,
                                                                        recording_top_level_directory))]
        if recordings_top_level_directory:
            for recording_top_level_directory in recordings_top_level_directory:
                try:
                    recording_top_level_directory_path = os.path.join(recordings_directory_path,
                                                                      recording_top_level_directory,
                                                                      '.MANIFEST')
                    with open(recording_top_level_directory_path, 'r') as input_file:
                        recording_manifest = json.load(input_file)
                        if recording_manifest['status'] == 'Completed':
                            recording = IPTVProxyRecording(recording_manifest['channel_name'],
                                                           recording_manifest['channel_number'],
                                                           datetime.strptime(
                                                               recording_manifest[
                                                                   'actual_end_date_time_in_utc'],
                                                               '%Y-%m-%d %H:%M:%S%z'),
                                                           recording_manifest['id'],
                                                           recording_manifest['program_title'],
                                                           recording_manifest['provider'],
                                                           datetime.strptime(
                                                               recording_manifest[
                                                                   'actual_start_date_time_in_utc'],
                                                               '%Y-%m-%d %H:%M:%S%z'),
                                                           IPTVProxyRecordingStatus.PERSISTED.value)
                            recording.base_recording_directory = recording_manifest['base_recording_directory']
                            persistent_recordings.append(recording)
                except OSError:
                    logger.error('Failed to open .MANIFEST\n'
                                 '.MANIFEST file path => {0}'.format(os.path.join(recordings_directory_path,
                                                                                  recording_top_level_directory,
                                                                                  '.MANIFEST')))

        return persistent_recordings

    @classmethod
    def _get_scheduled_recordings(cls):
        scheduled_recordings = []

        db = IPTVProxyDB()

        for recording in db.retrieve(['recordings']):
            if recording.status == IPTVProxyRecordingStatus.SCHEDULED.value:
                scheduled_recordings.append(recording)

        db.close()

        return scheduled_recordings

    @classmethod
    def _set_live_recordings_to_recording_thread(cls, live_recordings_to_recording_thread):
        with cls._live_recordings_to_recording_thread_lock:
            cls._live_recordings_to_recording_thread = live_recordings_to_recording_thread

    @classmethod
    def _restart_live_recordings(cls):
        live_recordings_to_recording_thread = {}

        db = IPTVProxyDB()

        for recording in db.retrieve(['recordings']):
            if recording.status == IPTVProxyRecordingStatus.LIVE.value:
                live_recordings_to_recording_thread[recording.id] = IPTVProxyRecordingThread(recording)

        db.close()

        cls._set_live_recordings_to_recording_thread(live_recordings_to_recording_thread)

    @classmethod
    def _set_start_recording_timer(cls):
        with cls._start_recording_timer_lock:
            if cls._start_recording_timer:
                cls._start_recording_timer.cancel()

            soonest_scheduled_recording_start_date_time_in_utc = None
            current_date_time_in_utc = datetime.now(pytz.utc)

            for scheduled_recording in cls._get_scheduled_recordings():
                scheduled_recording_start_date_time_in_utc = scheduled_recording.start_date_time_in_utc

                if current_date_time_in_utc > scheduled_recording_start_date_time_in_utc:
                    db = IPTVProxyDB()

                    # Generate a new id for the recording when we change it's status
                    scheduled_recording.id = '{0}'.format(uuid.uuid4())
                    scheduled_recording.status = IPTVProxyRecordingStatus.LIVE.value

                    db.close(do_commit_transaction=True)

                    with cls._live_recordings_to_recording_thread_lock:
                        cls._live_recordings_to_recording_thread[
                            scheduled_recording.id] = IPTVProxyRecordingThread(scheduled_recording)
                elif not soonest_scheduled_recording_start_date_time_in_utc:
                    soonest_scheduled_recording_start_date_time_in_utc = scheduled_recording_start_date_time_in_utc
                elif soonest_scheduled_recording_start_date_time_in_utc > scheduled_recording_start_date_time_in_utc:
                    soonest_scheduled_recording_start_date_time_in_utc = scheduled_recording_start_date_time_in_utc

            if soonest_scheduled_recording_start_date_time_in_utc:
                interval = (soonest_scheduled_recording_start_date_time_in_utc - datetime.now(pytz.utc)).total_seconds()
                cls._start_recording_timer = Timer(interval, cls._start_recording)
                cls._start_recording_timer.daemon = True
                cls._start_recording_timer.start()

                logger.debug('Starting recording timer\n'
                             'Interval => {0} seconds'.format(interval))

    @classmethod
    def _start_recording(cls):
        current_date_time_in_utc = datetime.now(pytz.utc)

        for scheduled_recording in cls._get_scheduled_recordings():
            scheduled_recording_start_date_time_in_utc = scheduled_recording.start_date_time_in_utc

            if current_date_time_in_utc > scheduled_recording_start_date_time_in_utc:
                db = IPTVProxyDB()

                # Generate a new id for the recording when we change it's status
                scheduled_recording.id = '{0}'.format(uuid.uuid4())
                scheduled_recording.status = IPTVProxyRecordingStatus.LIVE.value

                db.close(do_commit_transaction=True)

                with cls._live_recordings_to_recording_thread_lock:
                    cls._live_recordings_to_recording_thread[
                        scheduled_recording.id] = IPTVProxyRecordingThread(scheduled_recording)

        cls._set_start_recording_timer()

    @classmethod
    def add_scheduled_recording(cls, scheduled_recording):
        db = IPTVProxyDB()
        recordings = db.retrieve(['recordings'])

        if scheduled_recording not in recordings:
            recordings.append(scheduled_recording)

            db.close(do_commit_transaction=True)

            cls._set_start_recording_timer()
        else:
            db.close()

            raise IPTVProxyDuplicateRecordingError

    @classmethod
    def cancel_start_recording_timer(cls):
        if cls._start_recording_timer:
            cls._start_recording_timer.cancel()

    @classmethod
    def delete_live_recording(cls, live_recording):
        db = IPTVProxyDB()
        recordings = db.retrieve(['recordings'])
        recordings.remove(live_recording)
        db.close(do_commit_transaction=True)

    @classmethod
    def delete_persisted_recording(cls, persisted_recording):
        shutil.rmtree(os.path.join(cls._recordings_directory_path, persisted_recording.base_recording_directory))

    @classmethod
    def delete_scheduled_recording(cls, scheduled_recording):
        db = IPTVProxyDB()
        recordings = db.retrieve(['recordings'])
        recordings.remove(scheduled_recording)
        db.close(do_commit_transaction=True)

        cls._set_start_recording_timer()

    @classmethod
    def generate_recording_playlist_url(cls,
                                        is_server_secure,
                                        server_hostname,
                                        server_port,
                                        client_uuid,
                                        base_recording_directory,
                                        http_token):
        return '{0}://{1}:{2}/vod/playlist.m3u8?client_uuid={3}&http_token={4}&program_title={5}'.format(
            'https' if is_server_secure else 'http',
            server_hostname,
            server_port,
            client_uuid,
            urllib.parse.quote(http_token) if http_token else '',
            urllib.parse.quote(base_recording_directory))

    @classmethod
    def generate_vod_playlist_m3u8(cls, is_server_secure, client_ip_address, client_uuid, http_token):
        playlist_m3u8 = []

        client_ip_address_type = IPTVProxyUtility.determine_ip_address_type(client_ip_address)
        server_hostname = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
        server_port = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure else ''))

        for persistent_recording in cls._get_persistent_recordings():
            playlist_m3u8.append(
                '#EXTINF:-1,{0} - [{1} - {2}]\n'
                '{3}\n'.format(
                    persistent_recording.program_title,
                    persistent_recording.start_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z'),
                    persistent_recording.end_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z'),
                    cls.generate_recording_playlist_url(is_server_secure,
                                                        server_hostname,
                                                        server_port,
                                                        client_uuid,
                                                        persistent_recording.base_recording_directory,
                                                        http_token)))

        if playlist_m3u8:
            playlist_m3u8 = '#EXTM3U\n{0}'.format(''.join(playlist_m3u8))

            logger.debug('Generated VOD playlist.m3u8')
        else:
            logger.debug('No persistent recordings found. VOD playlist.m3u8 will not be generated')

        return playlist_m3u8

    @classmethod
    def get_recording(cls, recording_id):
        db = IPTVProxyDB()

        for recording in db.retrieve(['recordings']) + cls._get_persistent_recordings():
            if recording.id == recording_id:
                db.close()

                return recording

        db.close()

        raise IPTVProxyRecordingNotFoundError

    @classmethod
    def get_recordings(cls):
        db = IPTVProxyDB()
        recordings = [copy.deepcopy(recording)
                      for recording in db.retrieve(['recordings'])] + cls._get_persistent_recordings()
        db.close()

        return recordings

    @classmethod
    def get_recordings_directory_path(cls):
        return cls._recordings_directory_path

    @classmethod
    def initialize(cls):
        deleted_recordings_log_message = []
        loaded_recordings_log_message = []

        do_commit_transaction = False

        db = IPTVProxyDB()
        recordings = db.retrieve(['recordings'])

        for (recording_index, recording) in enumerate(recordings[:]):
            current_date_time_in_utc = datetime.now(pytz.utc)

            if current_date_time_in_utc >= recording.end_date_time_in_utc:
                do_commit_transaction = True

                recordings.pop(recording_index)

                deleted_recordings_log_message.append(
                    'Provider          => {0}\n'
                    'Channel name      => {1}\n'
                    'Channel number    => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}\n'
                    'Status            => {6}\n'.format(recording.provider,
                                                        recording.channel_name,
                                                        recording.channel_number,
                                                        recording.program_title,
                                                        recording.start_date_time_in_utc.astimezone(
                                                            tzlocal.get_localzone()).strftime(
                                                            '%Y-%m-%d %H:%M:%S'),
                                                        recording.end_date_time_in_utc.astimezone(
                                                            tzlocal.get_localzone()).strftime(
                                                            '%Y-%m-%d %H:%M:%S'),
                                                        recording.status))
            else:
                loaded_recordings_log_message.append(
                    'Provider          => {0}\n'
                    'Channel name      => {1}\n'
                    'Channel number    => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}\n'
                    'Status            => {6}\n'.format(recording.provider,
                                                        recording.channel_name,
                                                        recording.channel_number,
                                                        recording.program_title,
                                                        recording.start_date_time_in_utc.astimezone(
                                                            tzlocal.get_localzone()).strftime(
                                                            '%Y-%m-%d %H:%M:%S'),
                                                        recording.end_date_time_in_utc.astimezone(
                                                            tzlocal.get_localzone()).strftime(
                                                            '%Y-%m-%d %H:%M:%S'),
                                                        recording.status))

        db.close(do_commit_transaction=do_commit_transaction)

        if deleted_recordings_log_message:
            deleted_recordings_log_message.insert(0, 'Deleted expired recording{0}\n'.format(
                's' if len(deleted_recordings_log_message) > 1 else ''))

            logger.debug('\n'.join(deleted_recordings_log_message).strip())

        if loaded_recordings_log_message:
            loaded_recordings_log_message.insert(0, 'Loaded recording{0}\n'.format(
                's' if len(loaded_recordings_log_message) > 1 else ''))

            logger.debug('\n'.join(loaded_recordings_log_message).strip())

    @classmethod
    def read_ts_file(cls, path, program_title):
        ts_file_path = os.path.join(cls._recordings_directory_path,
                                    program_title,
                                    'segments',
                                    re.sub(r'/vod/(.*)\?.*', r'\1', path))

        return IPTVProxyUtility.read_file(ts_file_path, in_binary=True)

    @classmethod
    def read_vod_playlist_m3u8(cls, client_uuid, program_title, http_token):
        vod_playlist_m3u8_file_path = os.path.join(cls._recordings_directory_path,
                                                   program_title,
                                                   'playlist',
                                                   'playlist.m3u8')

        return re.sub(r'(\.ts\?)(.*)',
                      r'\1client_uuid={0}&http_token={1}&\2'.format(
                          client_uuid,
                          urllib.parse.quote(http_token) if http_token else ''),
                      IPTVProxyUtility.read_file(vod_playlist_m3u8_file_path))

    @classmethod
    def set_recordings_directory_path(cls, recordings_directory_path):
        cls._recordings_directory_path = recordings_directory_path

    @classmethod
    def start(cls):
        cls._restart_live_recordings()
        cls._set_start_recording_timer()

    @classmethod
    def stop_live_recording(cls, live_recording):
        with cls._live_recordings_to_recording_thread_lock:
            cls._live_recordings_to_recording_thread[live_recording.id].force_stop()


class IPTVProxyRecording(Persistent):
    __slots__ = ['_base_recording_directory', '_channel_name', '_channel_number', '_end_date_time_in_utc', '_id',
                 '_program_title', '_provider', '_start_date_time_in_utc', '_status']

    def __init__(self,
                 channel_name,
                 channel_number,
                 end_date_time_in_utc,
                 id_,
                 program_title,
                 provider,
                 start_date_time_in_utc,
                 status):
        self._base_recording_directory = None
        self._channel_name = channel_name
        self._channel_number = channel_number
        self._end_date_time_in_utc = end_date_time_in_utc
        self._id = id_
        self._program_title = program_title
        self._provider = provider
        self._start_date_time_in_utc = start_date_time_in_utc
        self._status = status

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.channel_number, self._end_date_time_in_utc, self._start_date_time_in_utc) == (
                other._channel_number, other._end_date_time_in_utc, other._start_date_time_in_utc)
        return False

    def __repr__(self):
        return '{0}('.format(self.__class__.__name__) + ', '.join(
            ['{0}={1!r}'.format(attribute_name[1:], getattr(self, attribute_name)) for attribute_name in
             self.__slots__]) + ')'

    def __str__(self):
        return '{0}('.format(self.__class__.__name__) + ', '.join(
            ['{0}={1!s}'.format(attribute_name, getattr(self, attribute_name)) for attribute_name in
             self.__slots__]) + ')'

    @property
    def base_recording_directory(self):
        return self._base_recording_directory

    @base_recording_directory.setter
    def base_recording_directory(self, base_recording_directory):
        self._base_recording_directory = base_recording_directory

    @property
    def channel_name(self):
        return self._channel_name

    @property
    def channel_number(self):
        return self._channel_number

    @property
    def end_date_time_in_utc(self):
        return self._end_date_time_in_utc

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id_):
        self._id = id_

    @property
    def program_title(self):
        return self._program_title

    @property
    def provider(self):
        return self._provider

    @property
    def start_date_time_in_utc(self):
        return self._start_date_time_in_utc

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status


class IPTVProxyRecordingThread(Thread):
    def __init__(self, recording):
        Thread.__init__(self)

        self._id = uuid.uuid3(uuid.NAMESPACE_OID, 'IPTVProxyRecordingThread')
        self._recording = recording
        self._recording_directory_path = None

        self._stop_recording_event = Event()
        self._stop_recording_timer = Timer(
            (self._recording.end_date_time_in_utc - datetime.now(pytz.utc)).total_seconds(),
            self._set_stop_recording_event)
        self._stop_recording_timer.daemon = True
        self._stop_recording_timer.start()

        self.start()

    def _create_recording_directory_tree(self):
        recording_directory_suffix_counter = 0
        recording_directory_suffix = ''

        did_make_directory = False
        while not did_make_directory:
            # base64.urlsafe_b64encode() the base directory. This results in a valid directory name on any OS at the
            # expense of human readability.
            recording_directory_path = os.path.join(IPTVProxyPVR.get_recordings_directory_path(),
                                                    base64.urlsafe_b64encode('{0}{1}'.format(
                                                        self._recording.program_title,
                                                        recording_directory_suffix).encode()).decode())
            if os.path.exists(recording_directory_path):
                recording_directory_suffix_counter += 1
                recording_directory_suffix = '_{0}'.format(recording_directory_suffix_counter)
            else:
                logger.debug('Creating recording directory tree for {0}\n'
                             'Path => {1}'.format(self._recording.program_title, recording_directory_path))

                try:
                    os.makedirs(recording_directory_path)
                    os.makedirs(os.path.join(recording_directory_path, 'playlist'))
                    os.makedirs(os.path.join(recording_directory_path, 'segments'))

                    did_make_directory = True
                    self._recording_directory_path = recording_directory_path

                    db = IPTVProxyDB()
                    self._recording.base_recording_directory = os.path.split(recording_directory_path)[-1]
                    db.close(do_commit_transaction=True)

                    logger.debug('Created recording directory tree for {0}\n'
                                 'Path => {1}'.format(self._recording.program_title, recording_directory_path))
                except OSError:
                    logger.error('Failed to create recording directory tree for {0}\n'
                                 'Path => {1}'.format(self._recording.program_title, recording_directory_path))

                    recording_directory_suffix_counter += 1
                    recording_directory_suffix = '_{0}'.format(recording_directory_suffix_counter)

    def _save_manifest_file(self,
                            actual_end_date_time_in_utc,
                            actual_start_date_time_in_utc,
                            id_,
                            playlist_file,
                            status):
        manifest_file_path = os.path.join(self._recording_directory_path, '.MANIFEST')

        try:
            with open(manifest_file_path, 'w') as out_file:
                json.dump({
                    'actual_end_date_time_in_utc': actual_end_date_time_in_utc,
                    'actual_start_date_time_in_utc': actual_start_date_time_in_utc,
                    'channel_name': self._recording.channel_name,
                    'base_recording_directory': self._recording.base_recording_directory,
                    'channel_number': self._recording.channel_number,
                    'id': id_,
                    'playlist_directory': os.path.join(self._recording_directory_path, 'playlist'),
                    'playlist_file': playlist_file,
                    'program_title': self._recording.program_title,
                    'provider': self._recording.provider,
                    'segments_directory': os.path.join(self._recording_directory_path, 'segments'),
                    'scheduled_end_date_time_in_utc': self._recording.end_date_time_in_utc.strftime(
                        '%Y-%m-%d %H:%M:%S%z'),
                    'scheduled_start_date_time_in_utc': self._recording.start_date_time_in_utc.strftime(
                        '%Y-%m-%d %H:%M:%S%z'),
                    'status': status},
                    out_file,
                    sort_keys=True,
                    indent=4)

                logger.debug('Saved .MANIFEST\n'
                             'Path => {0}'.format(manifest_file_path))
        except OSError:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

    def _save_playlist_file(self, playlist_file_name, playlist_file_content):
        playlist_file_path = os.path.join(self._recording_directory_path, 'playlist', playlist_file_name)

        try:
            with open(playlist_file_path, 'w') as out_file:
                out_file.write(playlist_file_content)

                logger.debug('Saved playlist\n'
                             'Path => {0}'.format(playlist_file_path))
        except OSError:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

    def _save_segment_file(self, segment_file_name, segment_file_content):
        segment_file_path = os.path.join(self._recording_directory_path, 'segments', segment_file_name)

        try:
            with open(segment_file_path, 'wb') as out_file:
                out_file.write(segment_file_content)

                logger.debug('Saved segment\n'
                             'Path => {0}'.format(segment_file_path))
        except OSError:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

    def _set_stop_recording_event(self):
        self._stop_recording_event.set()

        logger.info('Stopping recording\n'
                    'Provider          => {0}\n'
                    'Channel name      => {1}\n'
                    'Channel number    => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}'.format(self._recording.provider,
                                                      self._recording.channel_name,
                                                      self._recording.channel_number,
                                                      self._recording.program_title,
                                                      self._recording.start_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                                                      self._recording.end_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))

    def force_stop(self):
        self._set_stop_recording_event()

    def run(self):
        logger.info('Starting recording\n'
                    'Provider          => {0}\n'
                    'Channel name      => {1}\n'
                    'Channel number    => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}'.format(self._recording.provider,
                                                      self._recording.channel_name,
                                                      self._recording.channel_number,
                                                      self._recording.program_title,
                                                      self._recording.start_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                                                      self._recording.end_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))
        actual_start_date_time_in_utc = datetime.now(pytz.utc)

        self._create_recording_directory_tree()
        persisted_recording_id = '{0}'.format(uuid.uuid4())
        self._save_manifest_file(None,
                                 actual_start_date_time_in_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
                                 persisted_recording_id,
                                 None,
                                 'Started')

        provider_name = self._recording.provider.lower()
        provider = IPTVProxyConfiguration.get_provider(provider_name)

        for number_of_times_attempted_to_download_playlist_m3u8 in range(1, 11):
            try:
                # <editor-fold desc="Download playlist.m3u8">
                playlist_m3u8_content = provider['api'].download_playlist_m3u8(
                    '127.0.0.1',
                    self._id,
                    '/live/{0}/playlist.m3u8'.format(provider_name),
                    dict(channel_number=self._recording.channel_number,
                         protocol='hls'))
                # </editor-fold>

                self._save_manifest_file(None,
                                         actual_start_date_time_in_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
                                         persisted_recording_id,
                                         None,
                                         'In Progress')

                playlist_m3u8_object = m3u8.loads(playlist_m3u8_content)
                chunks_url = '/live/{0}/{1}'.format(provider_name, playlist_m3u8_object.data['playlists'][0]['uri'])

                break
            except requests.exceptions.HTTPError:
                time_to_sleep_before_next_attempt = math.ceil(
                    number_of_times_attempted_to_download_playlist_m3u8 / 5) * 5

                logger.error('Attempt #{0}\n'
                             'Failed to download playlist.m3u8\n'
                             'Will try again in {1} seconds'.format(number_of_times_attempted_to_download_playlist_m3u8,
                                                                    time_to_sleep_before_next_attempt))

                time.sleep(time_to_sleep_before_next_attempt)
        else:
            logger.error('Exhausted attempts to download playlist.m3u8')

            logger.info('Canceling recording\n'
                        'Provider          => {0}\n'
                        'Channel name      => {1}\n'
                        'Channel number    => {2}\n'
                        'Program title     => {3}\n'
                        'Start date & time => {4}\n'
                        'End date & time   => {5}'.format(self._recording.provider,
                                                          self._recording.channel_name,
                                                          self._recording.channel_number,
                                                          self._recording.program_title,
                                                          self._recording.start_date_time_in_utc.astimezone(
                                                              tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                                                          self._recording.end_date_time_in_utc.astimezone(
                                                              tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))

            self._save_manifest_file(datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S%z'),
                                     actual_start_date_time_in_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
                                     persisted_recording_id,
                                     None,
                                     'Canceled')

            return

        vod_playlist_m3u8_object = None
        downloaded_segment_file_names = []

        while not self._stop_recording_event.is_set():
            try:
                # <editor-fold desc="Download chunks.m3u8">
                chunks_url_components = urllib.parse.urlparse(chunks_url)
                chunks_query_string_parameters = dict(urllib.parse.parse_qsl(chunks_url_components.query))

                chunks_m3u8_content = provider['api'].download_chunks_m3u8('127.0.0.1',
                                                                           self._id,
                                                                           chunks_url_components.path,
                                                                           chunks_query_string_parameters)
                # </editor-fold>
                chunks_m3u8_download_date_time_in_utc = datetime.now(pytz.utc)
                chunks_m3u8_total_duration = 0
                chunks_m3u8_object = m3u8.loads(chunks_m3u8_content)

                if not vod_playlist_m3u8_object:
                    vod_playlist_m3u8_object = chunks_m3u8_object

                indices_of_skipped_segments = []
                for (segment_index, segment) in enumerate(chunks_m3u8_object.segments):
                    segment_url = '/live/{0}'.format(segment.uri)
                    segment_url_components = urllib.parse.urlparse(segment_url)
                    segment_query_string_parameters = dict(urllib.parse.parse_qsl(segment_url_components.query))
                    segment_file_name = re.sub(r'(/.*)?(/)(.*\.ts)', r'\3', segment_url_components.path)

                    chunks_m3u8_total_duration += segment.duration

                    if segment_file_name not in downloaded_segment_file_names:
                        try:
                            # <editor-fold desc="Download ts file">
                            ts_file_content = provider['api'].download_ts_file('127.0.0.1',
                                                                               self._id,
                                                                               segment_url_components.path,
                                                                               segment_query_string_parameters)
                            # </editor-fold>
                            logger.debug('Downloaded segment\n'
                                         'Segment => {0}'.format(segment_file_name))

                            downloaded_segment_file_names.append(segment_file_name)
                            self._save_segment_file(segment_file_name, ts_file_content)

                            segment.uri = '{0}?program_title={1}'.format(
                                segment_file_name,
                                urllib.parse.quote(self._recording.base_recording_directory))

                            if segment not in vod_playlist_m3u8_object.segments:
                                vod_playlist_m3u8_object.segments.append(segment)
                        except requests.exceptions.HTTPError:
                            logger.error('Failed to download segment\n'
                                         'Segment => {0}'.format(segment_file_name))
                    else:
                        logger.debug('Skipped segment since it was already downloaded\n'
                                     'Segment => {0} '.format(segment_file_name))

                        indices_of_skipped_segments.append(segment_index)

                for segment_index_to_delete in indices_of_skipped_segments:
                    del chunks_m3u8_object.segments[segment_index_to_delete]
            except requests.exceptions.HTTPError:
                logger.error('Failed to download chunks.m3u8')

                return

            current_date_time_in_utc = datetime.now(pytz.utc)
            wait_duration = chunks_m3u8_total_duration - (
                    current_date_time_in_utc - chunks_m3u8_download_date_time_in_utc).total_seconds()
            if wait_duration > 0:
                self._stop_recording_event.wait(wait_duration)

        if vod_playlist_m3u8_object:
            vod_playlist_m3u8_object.playlist_type = 'VOD'
            self._save_playlist_file('playlist.m3u8', '{0}\n'
                                                      '{1}'.format(vod_playlist_m3u8_object.dumps(), '#EXT-X-ENDLIST'))

        self._save_manifest_file(datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S%z'),
                                 actual_start_date_time_in_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
                                 persisted_recording_id,
                                 'playlist.m3u8',
                                 'Completed')

        IPTVProxyPVR.delete_live_recording(self._recording)

        logger.info('Finished recording\n'
                    'Channel name      => {0}\n'
                    'Channel number    => {1}\n'
                    'Program title     => {2}\n'
                    'Start date & time => {3}\n'
                    'End date & time   => {4}'.format(self._recording.channel_name,
                                                      self._recording.channel_number,
                                                      self._recording.program_title,
                                                      self._recording.start_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                                                      self._recording.end_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))
