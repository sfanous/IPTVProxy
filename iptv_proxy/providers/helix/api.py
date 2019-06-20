import logging

from rwlock import RWLock

from iptv_proxy.providers.helix.constants import HelixConstants
from iptv_proxy.providers.iptv_provider.api import XtreamCodesProvider

logger = logging.getLogger(__name__)


class Helix(XtreamCodesProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = HelixConstants.PROVIDER_NAME.lower()
