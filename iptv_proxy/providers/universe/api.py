import logging

from rwlock import RWLock

from iptv_proxy.providers.iptv_provider.api import XtreamCodesProvider
from iptv_proxy.providers.universe.constants import UniverseConstants

logger = logging.getLogger(__name__)


class Universe(XtreamCodesProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = UniverseConstants.PROVIDER_NAME.lower()
