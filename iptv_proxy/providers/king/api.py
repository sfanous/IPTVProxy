import logging

from rwlock import RWLock

from iptv_proxy.providers.iptv_provider.api import XtreamCodesProvider
from iptv_proxy.providers.king.constants import KingConstants

logger = logging.getLogger(__name__)


class King(XtreamCodesProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = KingConstants.PROVIDER_NAME.lower()
