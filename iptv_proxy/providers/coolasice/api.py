import logging

from rwlock import RWLock

from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
from iptv_proxy.providers.iptv_provider.api import XtreamCodesProvider

logger = logging.getLogger(__name__)


class CoolAsIce(XtreamCodesProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()
