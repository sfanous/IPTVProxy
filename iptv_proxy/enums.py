from enum import Enum


class CacheResponseType(Enum):
    HARD_HIT = 'Hard Hit'
    MISS = 'Miss'
    SOFT_HIT = 'Soft Hit'


class EPGStyle(Enum):
    COMPLETE = 'Complete'
    MINIMAL = 'Minimal'


class IPAddressType(Enum):
    LOOPBACK = 'LOOPBACK'
    PRIVATE = 'PRIVATE'
    PUBLIC = 'PUBLIC'


class PasswordState(Enum):
    DECRYPTED = 0
    ENCRYPTED = 1


class RecordingStatus(Enum):
    LIVE = 'live'
    PERSISTED = 'persisted'
    SCHEDULED = 'scheduled'


class M388PlaylistSortOrder(Enum):
    CHANNEL_NAME = 0
    CHANNEL_NUMBER = 1
