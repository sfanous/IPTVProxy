import logging
from datetime import datetime
from datetime import timedelta
from threading import Event
from threading import Timer

import pytz
from rwlock import RWLock

from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.constants import CACHE_TIME_TO_LIVE
from iptv_proxy.constants import CACHE_WAIT_TIME
from iptv_proxy.enums import CacheResponseType

logger = logging.getLogger(__name__)


class CacheEntry(object):
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


class CacheManager():
    __slots__ = []

    _cache = {}
    _cleanup_cache_timer = None
    _do_cache_downloaded_segments = True
    _lock = RWLock()

    @classmethod
    def _cleanup_cache(cls):
        current_date_time_in_utc = datetime.now(pytz.utc)

        logger.trace('Cache cleanup started\n'
                     'Cutoff date & time => {0}'.format(current_date_time_in_utc))

        with cls._lock.writer_lock:
            for provider in cls._cache:
                for channel_number in list(cls._cache[provider].keys()):
                    cache_bucket = cls._cache[provider][channel_number]

                    for segment_file_name in list(cache_bucket.keys()):
                        cache_entry = cache_bucket[segment_file_name]

                        if (cache_entry.expiry_date_time_in_utc and
                            current_date_time_in_utc > cache_entry.expiry_date_time_in_utc) or \
                                (cache_entry.segment_file_content is None and
                                 current_date_time_in_utc > cache_entry.creation_date_time_in_utc + timedelta(
                                            seconds=CACHE_TIME_TO_LIVE)):
                            del cache_bucket[segment_file_name]

                            logger.trace('Deleted expired cache entry\n'
                                         'Provider             => {0}\n'
                                         'Channel number       => {1}\n'
                                         'Segment file name    => {2}\n'
                                         'Creation date & time => {3}\n'
                                         'Expiry date & time   => {4}'.format(provider,
                                                                              channel_number,
                                                                              segment_file_name,
                                                                              cache_entry.expiry_date_time_in_utc,
                                                                              cache_entry.creation_date_time_in_utc))

                    if not cache_bucket:
                        del cls._cache[provider][channel_number]

                        logger.trace('Deleted expired cache bucket\n'
                                     'Provider       => {0}\n'
                                     'Channel number => {1}'.format(provider, channel_number))

            for provider in cls._cache:
                if cls._cache[provider]:
                    cls._cleanup_cache_timer = Timer(CACHE_TIME_TO_LIVE, cls._cleanup_cache)
                    cls._cleanup_cache_timer.daemon = True
                    cls._cleanup_cache_timer.start()

                    break
            else:
                cls._cleanup_cache_timer = None

                logger.debug('Deleted all cache buckets')

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_do_cache_downloaded_segments(
                OptionalSettings.get_optional_settings_parameter('cache_downloaded_segments'))
        except KeyError:
            pass

    @classmethod
    def _query_cache(cls, provider, channel_number, segment_file_name):
        if provider in cls._cache and channel_number in cls._cache[provider]:
            cache_bucket = cls._cache[provider][channel_number]

            if segment_file_name in cache_bucket:
                cache_entry = cache_bucket[segment_file_name]

                # Expiry date for a cache entry is set to CACHE_TIME_TO_LIVE seconds following the last time the
                # entry was accessed
                cache_entry.expiry_date_time_in_utc = datetime.now(pytz.utc) + timedelta(seconds=CACHE_TIME_TO_LIVE)

                if cache_entry.segment_file_content:
                    cache_response_type = CacheResponseType.HARD_HIT

                    logger.trace('Cache response\n'
                                 'Type              => Hard hit\n'
                                 'Provider          => {0}\n'
                                 'Channel number    => {1}\n'
                                 'Segment file name => {2}'.format(provider, channel_number, segment_file_name))
                else:
                    cache_response_type = CacheResponseType.SOFT_HIT

                    logger.trace('Cache response\n'
                                 'Type              => Soft hit\n'
                                 'Provider          => {0}\n'
                                 'Channel number    => {1}\n'
                                 'Segment file name => {2}'.format(provider, channel_number, segment_file_name))
            else:
                cache_entry = None
                cache_response_type = CacheResponseType.MISS

                cache_bucket[segment_file_name] = CacheEntry()

                logger.trace('Cache response\n'
                             'Type              => Miss\n'
                             'Provider          => {0}\n'
                             'Channel number    => {1}\n'
                             'Segment file name => {2}'.format(provider, channel_number, segment_file_name))

                logger.trace('Created cache entry\n'
                             'Provider          => {0}\n'
                             'Channel number    => {1}\n'
                             'Segment file name => {2}'.format(provider, channel_number, segment_file_name))
        else:
            cache_entry = None
            cache_response_type = CacheResponseType.MISS

            if provider not in cls._cache:
                cls._cache[provider] = {}

            cls._cache[provider][channel_number] = {}
            cls._cache[provider][channel_number][segment_file_name] = CacheEntry()

            logger.trace('Created cache bucket & entry\n'
                         'Provider          => {0}\n'
                         'Channel number    => {1}\n'
                         'Segment file name => {2}'.format(provider, channel_number, segment_file_name))

        if cache_response_type == CacheResponseType.MISS:
            if cls._cleanup_cache_timer is None:
                cls._cleanup_cache_timer = Timer(CACHE_TIME_TO_LIVE, cls._cleanup_cache)
                cls._cleanup_cache_timer.daemon = True
                cls._cleanup_cache_timer.start()

        return CacheResponse(cache_entry, cache_response_type)

    @classmethod
    def cancel_cleanup_cache_timer(cls):
        if cls._cleanup_cache_timer:
            cls._cleanup_cache_timer.cancel()

    @classmethod
    def initialize(cls):
        cls._initialize_class_variables()

    @classmethod
    def query_cache(cls, provider, channel_number, segment_file_name):
        segment_file_content = None

        with cls._lock.reader_lock:
            if cls._do_cache_downloaded_segments:
                logger.trace('Querying cache\n'
                             'Provider          => {0}\n'
                             'Channel number    => {1}\n'
                             'Segment file name => {2}'.format(provider, channel_number, segment_file_name))

                cache_response = cls._query_cache(provider, channel_number, segment_file_name)

                if cache_response.response_type == CacheResponseType.HARD_HIT:
                    segment_file_content = cache_response.entry.segment_file_content
                elif cache_response.response_type == CacheResponseType.SOFT_HIT:
                    cache_response.entry.primed_event.wait(CACHE_WAIT_TIME)

                    cache_response = cls._query_cache(provider, channel_number, segment_file_name)

                    if cache_response.response_type == CacheResponseType.HARD_HIT:
                        segment_file_content = cache_response.entry.segment_file_content

        return segment_file_content

    @classmethod
    def set_do_cache_downloaded_segments(cls, do_cache_downloaded_segments):
        with cls._lock.writer_lock:
            cls._do_cache_downloaded_segments = do_cache_downloaded_segments

    @classmethod
    def update_cache(cls, provider, channel_number, segment_file_name, segment_file_content):
        with cls._lock.writer_lock:
            if cls._do_cache_downloaded_segments:
                try:
                    cache_bucket = cls._cache[provider][channel_number]

                    try:
                        cache_entry = cache_bucket[segment_file_name]
                    except KeyError:
                        cache_entry = CacheEntry()

                        cache_bucket[segment_file_name] = cache_entry
                except KeyError:
                    cache_entry = CacheEntry()

                    cls._cache[provider][channel_number] = {}
                    cls._cache[provider][channel_number][segment_file_name] = cache_entry

                cache_entry.segment_file_content = segment_file_content

                cache_entry.expiry_date_time_in_utc = datetime.now(pytz.utc) + timedelta(seconds=CACHE_TIME_TO_LIVE)
                cache_entry.primed_event.set()

                if cls._cleanup_cache_timer is None:
                    cls._cleanup_cache_timer = Timer(CACHE_TIME_TO_LIVE, cls._cleanup_cache)
                    cls._cleanup_cache_timer.daemon = True
                    cls._cleanup_cache_timer.start()

                logger.trace('Updated cache entry\n'
                             'Provider           => {0}\n'
                             'Channel number     => {1}\n'
                             'Segment file name  => {2}\n'
                             'Expiry date & time => {3}'.format(provider,
                                                                channel_number,
                                                                segment_file_name,
                                                                cache_entry.expiry_date_time_in_utc))


class CacheResponse():
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
