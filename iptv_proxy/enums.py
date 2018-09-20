from enum import Enum


class IPTVProxyCacheResponseType(Enum):
    HARD_HIT = 'Hard Hit'
    MISS = 'Miss'
    SOFT_HIT = 'Soft Hit'


class IPTVProxyEPGSource(Enum):
    FOG = 'fog'
    SMOOTH_STREAMS = 'smoothstreams'


class IPTVProxyIPAddressType(Enum):
    LOOPBACK = 'LOOPBACK'
    PRIVATE = 'PRIVATE'
    PUBLIC = 'PUBLIC'


class IPTVProxyPasswordState(Enum):
    DECRYPTED = 0
    ENCRYPTED = 1


class IPTVProxyRecordingStatus(Enum):
    LIVE = 'live'
    PERSISTED = 'persisted'
    SCHEDULED = 'scheduled'
