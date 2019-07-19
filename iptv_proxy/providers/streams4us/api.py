import logging

from rwlock import RWLock

from iptv_proxy.providers.streams4us.constants import Streams4UsConstants
from iptv_proxy.providers.iptv_provider.api import XtreamCodesProvider

logger = logging.getLogger(__name__)


class Streams4Us(XtreamCodesProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = Streams4UsConstants.PROVIDER_NAME.lower()
