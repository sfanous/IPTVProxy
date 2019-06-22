import logging
import os
import pickle
import re
import shutil
import sys
import traceback
import urllib.parse
import uuid
from datetime import datetime
from threading import Event
from threading import RLock
from threading import Thread
from threading import Timer

import m3u8
import math
import pytz
import requests
import tzlocal
from m3u8 import M3U8
from sqlalchemy.exc import IntegrityError

from iptv_proxy.cache import CacheManager
from iptv_proxy.configuration import Configuration
from iptv_proxy.data_access import DatabaseAccess
from iptv_proxy.data_model import Segment
from iptv_proxy.db import Database
from iptv_proxy.enums import RecordingStatus
from iptv_proxy.exceptions import DuplicateRecordingError
from iptv_proxy.exceptions import HLSPlaylistDownloadError
from iptv_proxy.exceptions import ProviderNotFoundError
from iptv_proxy.exceptions import RecordingNotFoundError
from iptv_proxy.exceptions import SegmentNotFoundError
from iptv_proxy.hls import HLSClient
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class PVR(object):
    __slots__ = []

    _live_recordings_to_recording_thread = {}
    _live_recordings_to_recording_thread_lock = RLock()
    _recordings_directory_path = None
    _start_recording_timer = None
    _start_recording_timer_lock = RLock()

    @classmethod
    def _initialize_recordings(cls, db_session):
        deleted_recordings_log_message = []
        loaded_recordings_log_message = []

        unformatted_message_to_log = 'Provider          => {0}\n' \
                                     'Channel number    => {1}\n' \
                                     'Channel name      => {2}\n' \
                                     'Program title     => {3}\n' \
                                     'Start date & time => {4}\n' \
                                     'End date & time   => {5}\n' \
                                     'Status            => {6}\n'

        for recording in DatabaseAccess.query_recordings(db_session):
            current_date_time_in_utc = datetime.now(pytz.utc)

            formatted_message_to_log = unformatted_message_to_log.format(recording.provider,
                                                                         recording.channel_number,
                                                                         recording.channel_name,
                                                                         recording.program_title,
                                                                         recording.start_date_time_in_utc.astimezone(
                                                                             tzlocal.get_localzone()).strftime(
                                                                             '%Y-%m-%d %H:%M:%S%z'),
                                                                         recording.end_date_time_in_utc.astimezone(
                                                                             tzlocal.get_localzone()).strftime(
                                                                             '%Y-%m-%d %H:%M:%S%z'),
                                                                         recording.status)

            if current_date_time_in_utc >= recording.end_date_time_in_utc:
                if recording.status == RecordingStatus.LIVE.value:
                    segment_row = DatabaseAccess.query_segments_count(db_session, recording.id)

                    if segment_row is not None and segment_row.count > 0:
                        recording.status = RecordingStatus.PERSISTED.value

                        loaded_recordings_log_message.append(formatted_message_to_log)
                    else:
                        DatabaseAccess.delete_recording(db_session, recording.id)

                        deleted_recordings_log_message.append(formatted_message_to_log)
                elif recording.status == RecordingStatus.SCHEDULED.value:
                    DatabaseAccess.delete_recording(db_session, recording.id)

                    deleted_recordings_log_message.append(formatted_message_to_log)
            else:
                loaded_recordings_log_message.append(formatted_message_to_log)

        if deleted_recordings_log_message:
            deleted_recordings_log_message.insert(0, 'Deleted expired recording{0}\n'.format(
                's' if len(deleted_recordings_log_message) > 1
                else ''))

            logger.debug('\n'.join(deleted_recordings_log_message).strip())

        if loaded_recordings_log_message:
            loaded_recordings_log_message.insert(0, 'Loaded recording{0}\n'.format(
                's' if len(loaded_recordings_log_message) > 1
                else ''))

            logger.debug('\n'.join(loaded_recordings_log_message).strip())

    @classmethod
    def _restart_live_recordings(cls, db_session):
        current_date_time_in_utc = datetime.now(pytz.utc)

        live_recordings_to_recording_thread = {}

        for live_recording in DatabaseAccess.query_live_recordings(db_session):
            if live_recording.end_date_time_in_utc > current_date_time_in_utc:
                live_recordings_to_recording_thread[live_recording.id] = RecordingThread(live_recording)
                live_recordings_to_recording_thread[live_recording.id].start()

        cls._set_live_recordings_to_recording_thread(live_recordings_to_recording_thread)

    @classmethod
    def _set_live_recordings_to_recording_thread(cls, live_recordings_to_recording_thread):
        with cls._live_recordings_to_recording_thread_lock:
            cls._live_recordings_to_recording_thread = live_recordings_to_recording_thread

    @classmethod
    def _set_start_recording_timer(cls, db_session):
        with cls._start_recording_timer_lock:
            if cls._start_recording_timer:
                cls._start_recording_timer.cancel()

            soonest_scheduled_recording_start_date_time_in_utc = None
            current_date_time_in_utc = datetime.now(pytz.utc)

            for scheduled_recording in DatabaseAccess.query_scheduled_recordings(db_session):
                scheduled_recording_start_date_time_in_utc = scheduled_recording.start_date_time_in_utc

                if current_date_time_in_utc > scheduled_recording_start_date_time_in_utc:
                    scheduled_recording.status = RecordingStatus.LIVE.value

                    with cls._live_recordings_to_recording_thread_lock:
                        cls._live_recordings_to_recording_thread[scheduled_recording.id] = RecordingThread(
                            scheduled_recording)
                        cls._live_recordings_to_recording_thread[scheduled_recording.id].start()
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

        with Database.get_write_lock():
            db_session = Database.create_session()

            try:
                for scheduled_recording in DatabaseAccess.query_scheduled_recordings(db_session):
                    scheduled_recording_start_date_time_in_utc = scheduled_recording.start_date_time_in_utc

                    if current_date_time_in_utc > scheduled_recording_start_date_time_in_utc:
                        scheduled_recording.status = RecordingStatus.LIVE.value

                        with cls._live_recordings_to_recording_thread_lock:
                            cls._live_recordings_to_recording_thread[scheduled_recording.id] = RecordingThread(
                                scheduled_recording)
                            cls._live_recordings_to_recording_thread[scheduled_recording.id].start()

                db_session.commit()

                cls._set_start_recording_timer(db_session)
            except Exception:
                (type_, value_, traceback_) = sys.exc_info()
                logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                db_session.rollback()
            finally:
                db_session.close()

    @classmethod
    def add_scheduled_recording(cls, db_session, scheduled_recording):
        try:
            db_session.add(scheduled_recording)
            db_session.flush()

            cls._set_start_recording_timer(db_session)
        except IntegrityError:
            raise DuplicateRecordingError

    @classmethod
    def cancel_start_recording_timer(cls):
        if cls._start_recording_timer:
            cls._start_recording_timer.cancel()

    @classmethod
    def cleanup_live_recording(cls, recording):
        with cls._live_recordings_to_recording_thread_lock:
            del cls._live_recordings_to_recording_thread[recording.id]

    @classmethod
    def delete_recording(cls, db_session, recording):
        DatabaseAccess.delete_recording(db_session, recording.id)

        for segment_row in DatabaseAccess.query_segments_directory_path(db_session, recording.id):
            try:
                shutil.rmtree(segment_row.directory_path)
            except OSError:
                pass

        DatabaseAccess.delete_segments(db_session, recording.id)
        db_session.flush()

        if not db_session.deleted:
            if recording.status == RecordingStatus.SCHEDULED.value:
                cls._set_start_recording_timer(db_session)
        else:
            raise RecordingNotFoundError

    @classmethod
    def generate_vod_index_playlist_m3u8(cls, is_server_secure, client_ip_address, client_uuid, http_token):
        playlist_m3u8 = []

        client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)
        server_hostname = Configuration.get_configuration_parameter(
            'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
        server_port = Configuration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                         else ''))

        db_session = Database.create_session()

        try:
            for persistent_recording in DatabaseAccess.query_persisted_recordings(db_session):
                playlist_m3u8.append(
                    '#EXTINF:-1,{0} - [{1} - {2}]\n'
                    '{3}\n'.format(
                        persistent_recording.program_title,
                        persistent_recording.start_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z'),
                        persistent_recording.end_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z'),
                        cls.generate_vod_recording_playlist_url(is_server_secure,
                                                                server_hostname,
                                                                server_port,
                                                                client_uuid,
                                                                persistent_recording.id,
                                                                http_token)))
        finally:
            db_session.close()

        if playlist_m3u8:
            playlist_m3u8 = '#EXTM3U\n{0}'.format(''.join(playlist_m3u8))

            logger.debug('Generated VOD playlist.m3u8')
        else:
            logger.debug('No persistent recordings found. VOD playlist.m3u8 will not be generated')

        return playlist_m3u8

    @classmethod
    def generate_vod_recording_playlist_m3u8(cls, client_uuid, recording_id, http_token):
        db_session = Database.create_session()

        try:
            vod_playlist_m3u8_object = M3U8()
            vod_playlist_m3u8_object.media_sequence = 0
            vod_playlist_m3u8_object.version = '3'
            vod_playlist_m3u8_object.target_duration = 0
            vod_playlist_m3u8_object.playlist_type = 'VOD'

            for segment_row in DatabaseAccess.query_segment_pickle(db_session, recording_id):
                segment = pickle.loads(segment_row.pickle)

                if segment.duration > vod_playlist_m3u8_object.target_duration:
                    vod_playlist_m3u8_object.target_duration = math.ceil(segment.duration)

                vod_playlist_m3u8_object.add_segment(segment)

            return re.sub(r'(\.ts\?)(.*)',
                          r'\1client_uuid={0}&http_token={1}&\2'.format(
                              client_uuid,
                              urllib.parse.quote(http_token) if http_token
                              else ''),
                          '{0}\n'
                          '{1}'.format(vod_playlist_m3u8_object.dumps(), '#EXT-X-ENDLIST'))
        finally:
            db_session.close()

    @classmethod
    def generate_vod_recording_playlist_url(cls,
                                            is_server_secure,
                                            server_hostname,
                                            server_port,
                                            client_uuid,
                                            recording_id,
                                            http_token):
        return '{0}://{1}:{2}/vod/playlist.m3u8?client_uuid={3}&http_token={4}&recording_id={5}'.format(
            'https' if is_server_secure
            else 'http',
            server_hostname,
            server_port,
            client_uuid,
            urllib.parse.quote(http_token) if http_token
            else '',
            urllib.parse.quote(recording_id))

    @classmethod
    def get_recording(cls, db_session, recording_id):
        recording = DatabaseAccess.query_recording(db_session, recording_id)

        if recording is not None:
            return recording

        raise RecordingNotFoundError

    @classmethod
    def get_recording_program_title(cls, recording_id):
        db_session = Database.create_session()

        try:
            recording = DatabaseAccess.query_recording(db_session, recording_id)

            if recording is not None:
                program_title = recording.program_title
            else:
                program_title = 'Recording {0}'.format(recording_id)

            return program_title
        finally:
            db_session.close()

    @classmethod
    def get_recordings(cls):
        recordings = []

        db_session = Database.create_session()

        try:
            for recording in DatabaseAccess.query_recordings(db_session):
                recordings.append(recording)
        finally:
            db_session.close()

        return recordings

    @classmethod
    def get_recordings_directory_path(cls):
        return cls._recordings_directory_path

    @classmethod
    def initialize(cls):
        with Database.get_write_lock():
            db_session = Database.create_session()

            try:
                cls._initialize_recordings(db_session)

                db_session.commit()
            except Exception:
                (type_, value_, traceback_) = sys.exc_info()
                logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                db_session.rollback()
            finally:
                db_session.close()

    @classmethod
    def load_ts_file(cls, path, recording_id):
        db_session = Database.create_session()

        try:
            segment_name = re.sub(r'/vod/(.*)\?.*', r'\1', path)

            segment_row = DatabaseAccess.query_segment_directory_path(db_session,
                                                                      segment_name,
                                                                      recording_id)

            if segment_row is not None:
                return Utility.read_file(os.path.join(segment_row.directory_path, segment_name), in_binary=True)
            else:
                raise SegmentNotFoundError
        finally:
            db_session.close()

    @classmethod
    def set_recordings_directory_path(cls, recordings_directory_path):
        cls._recordings_directory_path = recordings_directory_path

    @classmethod
    def start(cls):
        with Database.get_write_lock():
            db_session = Database.create_session()

            try:
                cls._restart_live_recordings(db_session)
                cls._set_start_recording_timer(db_session)

                db_session.commit()
            except Exception:
                (type_, value_, traceback_) = sys.exc_info()
                logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                db_session.rollback()
            finally:
                db_session.close()

    @classmethod
    def stop(cls):
        with cls._live_recordings_to_recording_thread_lock:
            for live_recording_id in cls._live_recordings_to_recording_thread:
                cls._live_recordings_to_recording_thread[live_recording_id].force_stop()

                del cls._live_recordings_to_recording_thread[live_recording_id]

    @classmethod
    def stop_live_recording(cls, db_session, recording):
        with cls._live_recordings_to_recording_thread_lock:
            try:
                cls._live_recordings_to_recording_thread[recording.id].force_stop()

                del cls._live_recordings_to_recording_thread[recording.id]
            except KeyError:
                recording = DatabaseAccess.query_recording(db_session, recording.id)

                if recording is not None:
                    if recording.status == RecordingStatus.LIVE.value:
                        segment_row = DatabaseAccess.query_segments_count(db_session, recording.id)

                        if segment_row is not None and segment_row.count > 0:
                            recording.status = RecordingStatus.PERSISTED.value
                else:
                    raise RecordingNotFoundError


class RecordingThread(Thread):
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

    def _create_recording_directory_tree(self):
        recording_directory_path = os.path.join(PVR.get_recordings_directory_path(), self._recording.id)

        if not os.path.exists(recording_directory_path):
            try:
                os.makedirs(recording_directory_path)
            except OSError:
                logger.error('Failed to create recording directory for {0}\n'
                             'Path => {1}'.format(self._recording.program_title, recording_directory_path))

        self._recording_directory_path = recording_directory_path

    def _set_stop_recording_event(self):
        logger.info('Stopping recording\n'
                    'Provider          => {0}\n'
                    'Channel number    => {1}\n'
                    'Channel name      => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}'.format(self._recording.provider,
                                                      self._recording.channel_number,
                                                      self._recording.channel_name,
                                                      self._recording.program_title,
                                                      self._recording.start_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                                                      self._recording.end_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))

        self._stop_recording_event.set()

    def force_stop(self):
        self._set_stop_recording_event()

    def run(self):
        logger.info('Starting recording\n'
                    'Provider          => {0}\n'
                    'Channel number    => {1}\n'
                    'Channel name      => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}'.format(self._recording.provider,
                                                      self._recording.channel_number,
                                                      self._recording.channel_name,
                                                      self._recording.program_title,
                                                      self._recording.start_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                                                      self._recording.end_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))

        self._create_recording_directory_tree()

        try:
            hls_client = HLSClient(self._id, self._recording.provider.lower(), self._recording.channel_number)

            playlist_m3u8_object = m3u8.loads(hls_client.download_playlist_m3u8())
            chunks_m3u8_object = None

            try:
                chunks_url = '/live/{0}/{1}'.format(self._recording.provider.lower(),
                                                    playlist_m3u8_object.data['playlists'][0]['uri'])
            except IndexError:
                chunks_m3u8_object = playlist_m3u8_object

            downloaded_segment_file_names = []

            while not self._stop_recording_event.is_set():
                try:
                    chunks_m3u8_object = m3u8.loads(hls_client.download_chunks_m3u8(chunks_url))
                except NameError:
                    if chunks_m3u8_object is None:
                        chunks_m3u8_object = m3u8.loads(hls_client.download_playlist_m3u8())

                chunks_m3u8_download_date_time_in_utc = datetime.now(pytz.utc)
                chunks_m3u8_total_duration = 0

                for (segment_index, segment) in enumerate(chunks_m3u8_object.segments):
                    segment_url = '/live/{0}'.format(segment.uri)
                    segment_url_components = urllib.parse.urlparse(segment_url)
                    segment_file_name = re.sub(r'(/.*)?(/)(.*\.ts)', r'\3', segment_url_components.path)

                    if segment_file_name not in downloaded_segment_file_names:
                        try:
                            ts_file_content = CacheManager.query_cache(self._recording.provider.lower(),
                                                                       self._recording.channel_number,
                                                                       segment_file_name.lower())
                            if ts_file_content is None:
                                ts_file_content = hls_client.download_ts_file(segment_url)

                                CacheManager.update_cache(self._recording.provider.lower(),
                                                          self._recording.channel_number,
                                                          segment_file_name.lower(),
                                                          ts_file_content)

                                logger.debug('Downloaded segment\n'
                                             'Segment => {0}'.format(segment_file_name))

                            segment.uri = '{0}?recording_id={1}'.format(segment_file_name,
                                                                        urllib.parse.quote(self._recording.id))
                            downloaded_segment_file_names.append(segment_file_name)

                            Utility.write_file(ts_file_content,
                                               os.path.join(self._recording_directory_path,
                                                            segment_file_name),
                                               in_binary=True)

                            with Database.get_write_lock():
                                db_session = Database.create_session()

                                try:
                                    db_session.add(Segment(segment_file_name,
                                                           self._recording.id,
                                                           pickle.dumps(segment, protocol=pickle.HIGHEST_PROTOCOL),
                                                           self._recording_directory_path))
                                    db_session.commit()
                                except Exception:
                                    (type_, value_, traceback_) = sys.exc_info()
                                    logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                                    db_session.rollback()
                                finally:
                                    db_session.close()
                        except requests.exceptions.HTTPError:
                            logger.error('Failed to download segment\n'
                                         'Segment => {0}'.format(segment_file_name))
                    else:
                        logger.debug('Skipped segment since it was already downloaded\n'
                                     'Segment => {0} '.format(segment_file_name))

                    chunks_m3u8_total_duration += segment.duration

                current_date_time_in_utc = datetime.now(pytz.utc)
                wait_duration = chunks_m3u8_total_duration - (
                        current_date_time_in_utc - chunks_m3u8_download_date_time_in_utc).total_seconds()
                if wait_duration > 0:
                    self._stop_recording_event.wait(wait_duration)

                chunks_m3u8_object = None

            self._recording.status = RecordingStatus.PERSISTED.value

            db_session.merge(self._recording)
            db_session.commit()

            logger.info('Finished recording\n'
                        'Provider          => {0}\n'
                        'Channel number    => {1}\n'
                        'Channel name      => {2}\n'
                        'Program title     => {3}\n'
                        'Start date & time => {4}\n'
                        'End date & time   => {5}'.format(self._recording.provider,
                                                          self._recording.channel_number,
                                                          self._recording.channel_name,
                                                          self._recording.program_title,
                                                          self._recording.start_date_time_in_utc.astimezone(
                                                              tzlocal.get_localzone()).strftime(
                                                              '%Y-%m-%d %H:%M:%S'),
                                                          self._recording.end_date_time_in_utc.astimezone(
                                                              tzlocal.get_localzone()).strftime(
                                                              '%Y-%m-%d %H:%M:%S')))
        except (HLSPlaylistDownloadError, ProviderNotFoundError):
            if self._stop_recording_event.is_set():
                self._recording.status = RecordingStatus.PERSISTED.value

                db_session.merge(self._recording)
                db_session.commit()

                logger.info('Finished recording\n'
                            'Provider          => {0}\n'
                            'Channel number    => {1}\n'
                            'Channel name      => {2}\n'
                            'Program title     => {3}\n'
                            'Start date & time => {4}\n'
                            'End date & time   => {5}'.format(self._recording.provider,
                                                              self._recording.channel_number,
                                                              self._recording.channel_name,
                                                              self._recording.program_title,
                                                              self._recording.start_date_time_in_utc.astimezone(
                                                                  tzlocal.get_localzone()).strftime(
                                                                  '%Y-%m-%d %H:%M:%S'),
                                                              self._recording.end_date_time_in_utc.astimezone(
                                                                  tzlocal.get_localzone()).strftime(
                                                                  '%Y-%m-%d %H:%M:%S')))
            else:
                logger.info('Canceling recording\n'
                            'Provider          => {0}\n'
                            'Channel number    => {1}\n'
                            'Channel name      => {2}\n'
                            'Program title     => {3}\n'
                            'Start date & time => {4}\n'
                            'End date & time   => {5}'.format(self._recording.provider,
                                                              self._recording.channel_number,
                                                              self._recording.channel_name,
                                                              self._recording.program_title,
                                                              self._recording.start_date_time_in_utc.astimezone(
                                                                  tzlocal.get_localzone()).strftime(
                                                                  '%Y-%m-%d %H:%M:%S'),
                                                              self._recording.end_date_time_in_utc.astimezone(
                                                                  tzlocal.get_localzone()).strftime(
                                                                  '%Y-%m-%d %H:%M:%S')))
        finally:
            PVR.cleanup_live_recording(self._recording)
