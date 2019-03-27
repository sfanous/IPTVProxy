import logging
from datetime import datetime
from datetime import timedelta
from threading import Event
from threading import RLock
from threading import Timer

import pytz

from .constants import CACHE_TIME_TO_LIVE
from .enums import IPTVProxyCacheResponseType

logger = logging.getLogger(__name__)


class IPTVProxyCacheEntry(object):
    __slots__ = ['_creation_date_time_in_utc', '_expiry_date_time_in_utc', '_primed_event', '_segment_file_content']

    def __init__(self):
        self._creation_date_time_in_utc = datetime.now(pytz.utc)
        self._expiry_date_time_in_utc = None
        self._primed_event = Event()
        self._segment_file_content = None

    @property
    def creation_date_time_in_utc(self):
        return self._creation_date_time_in_utc

    @property
    def expiry_date_time_in_utc(self):
        return self._expiry_date_time_in_utc

    @expiry_date_time_in_utc.setter
    def expiry_date_time_in_utc(self, expiry_date_time_in_utc):
        self._expiry_date_time_in_utc = expiry_date_time_in_utc

    @property
    def primed_event(self):
        return self._primed_event

    @property
    def segment_file_content(self):
        return self._segment_file_content

    @segment_file_content.setter
    def segment_file_content(self, segment_file_content):
        self._segment_file_content = segment_file_content


class IPTVProxyCacheManager():
    __slots__ = []

    _cache = {}
    _cleanup_cache_timer = None
    _do_cache_downloaded_segments = True
    _lock = RLock()

    @classmethod
    def _cleanup_cache(cls):
        current_date_time_in_utc = datetime.now(pytz.utc)

        # noinspection PyUnresolvedReferences
        logger.trace('Cache cleanup started\n'
                     'Cutoff date & time => {0}'.format(current_date_time_in_utc))

        with cls._lock:
            for channel_number in list(cls._cache.keys()):
                cache_bucket = cls._cache[channel_number]

                for segment_file_name in list(cache_bucket.keys()):
                    cache_entry = cache_bucket[segment_file_name]

                    if (cache_entry.expiry_date_time_in_utc and
                        current_date_time_in_utc > cache_entry.expiry_date_time_in_utc) or \
                            (cache_entry.segment_file_content is None and
                             current_date_time_in_utc > cache_entry.creation_date_time_in_utc + timedelta(
                                        seconds=CACHE_TIME_TO_LIVE)):
                        del cache_bucket[segment_file_name]

                        # noinspection PyUnresolvedReferences
                        logger.trace('Deleted expired cache entry\n'
                                     'Channel number       => {0}\n'
                                     'Segment file name    => {1}\n'
                                     'Creation date & time => {2}\n'
                                     'Expiry date & time   => {3}'.format(channel_number,
                                                                          segment_file_name,
                                                                          cache_entry.expiry_date_time_in_utc,
                                                                          cache_entry.creation_date_time_in_utc))

                if not cache_bucket:
                    del cache_bucket

                    # noinspection PyUnresolvedReferences
                    logger.trace('Deleted expired cache bucket\n'
                                 'Channel number => {0}'.format(channel_number))

            if len(cls._cache):
                cls._cleanup_cache_timer = Timer(CACHE_TIME_TO_LIVE, cls._cleanup_cache)
                cls._cleanup_cache_timer.daemon = True
                cls._cleanup_cache_timer.start()
            else:
                cls._cleanup_cache_timer = None

    @classmethod
    def cancel_cleanup_cache_timer(cls):
        if cls._cleanup_cache_timer:
            cls._cleanup_cache_timer.cancel()

    @classmethod
    def get_do_cache_downloaded_segments(cls):
        return cls._do_cache_downloaded_segments

    @classmethod
    def query_cache(cls, channel_number, segment_file_name):
        with cls._lock:
            if channel_number in cls._cache:
                cache_bucket = cls._cache[channel_number]

                if segment_file_name in cache_bucket:
                    cache_entry = cache_bucket[segment_file_name]

                    # Expiry date for a cache entry is set to CACHE_TIME_TO_LIVE seconds following the last time the
                    # entry was accessed
                    cache_entry.expiry_date_time_in_utc = datetime.now(pytz.utc) + timedelta(seconds=CACHE_TIME_TO_LIVE)

                    if cache_entry.segment_file_content:
                        cache_response_type = IPTVProxyCacheResponseType.HARD_HIT

                        # noinspection PyUnresolvedReferences
                        logger.trace('Hard hit cache entry\n'
                                     'Channel number    => {0}\n'
                                     'Segment file name => {1}'.format(channel_number, segment_file_name))
                    else:
                        cache_response_type = IPTVProxyCacheResponseType.SOFT_HIT

                        # noinspection PyUnresolvedReferences
                        logger.trace('Soft hit cache entry\n'
                                     'Channel number    => {0}\n'
                                     'Segment file name => {1}'.format(channel_number, segment_file_name))
                else:
                    cache_entry = None
                    cache_response_type = IPTVProxyCacheResponseType.MISS

                    cache_bucket[segment_file_name] = IPTVProxyCacheEntry()

                    # noinspection PyUnresolvedReferences
                    logger.trace('Created cache entry\n'
                                 'Channel number    => {0}\n'
                                 'Segment file name => {1}'.format(channel_number, segment_file_name))
            else:
                cache_entry = None
                cache_response_type = IPTVProxyCacheResponseType.MISS

                cls._cache[channel_number] = {}
                cls._cache[channel_number][segment_file_name] = IPTVProxyCacheEntry()

                # noinspection PyUnresolvedReferences
                logger.trace('Created cache bucket & entry\n'
                             'Channel number    => {0}\n'
                             'Segment file name => {1}'.format(channel_number, segment_file_name))

            # noinspection PyUnresolvedReferences
            logger.trace('Query cache\n'
                         'Channel number    => {0}\n'
                         'Segment file name => {1}\n'
                         'Result            => {2}'.format(channel_number,
                                                           segment_file_name,
                                                           cache_response_type.value))

            return IPTVProxyCacheResponse(cache_entry, cache_response_type)

    @classmethod
    def set_do_cache_downloaded_segments(cls, do_cache_downloaded_segments):
        cls._do_cache_downloaded_segments = do_cache_downloaded_segments

    @classmethod
    def update_cache(cls, channel_number, segment_file_name, segment_file_content):
        with cls._lock:
            try:
                cache_bucket = cls._cache[channel_number]

                try:
                    cache_entry = cache_bucket[segment_file_name]
                except KeyError:
                    cache_entry = IPTVProxyCacheEntry()

                    cache_bucket[segment_file_name] = cache_entry
            except KeyError:
                cache_entry = IPTVProxyCacheEntry()

                cls._cache[channel_number] = {}
                cls._cache[channel_number][segment_file_name] = cache_entry

            cache_entry.segment_file_content = segment_file_content

            cache_entry.expiry_date_time_in_utc = datetime.now(pytz.utc) + timedelta(seconds=CACHE_TIME_TO_LIVE)
            cache_entry.primed_event.set()

            if cls._cleanup_cache_timer is None:
                cls._cleanup_cache_timer = Timer(CACHE_TIME_TO_LIVE, cls._cleanup_cache)
                cls._cleanup_cache_timer.daemon = True
                cls._cleanup_cache_timer.start()

            # noinspection PyUnresolvedReferences
            logger.trace('Updated cache entry\n'
                         'Channel number     => {0}\n'
                         'Segment file name  => {1}\n'
                         'Expiry date & time => {2}'.format(channel_number,
                                                            segment_file_name,
                                                            cache_entry.expiry_date_time_in_utc))


class IPTVProxyCacheResponse():
    __slots__ = ['_entry', '_response_type']

    def __init__(self, entry, response_type):
        self._entry = entry
        self._response_type = response_type

    @property
    def entry(self):
        return self._entry

    @property
    def response_type(self):
        return self._response_type
