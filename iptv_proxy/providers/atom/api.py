import logging

from rwlock import RWLock

from iptv_proxy.providers.atom.constants import AtomConstants
from iptv_proxy.providers.iptv_provider.api import XtreamCodesProvider

logger = logging.getLogger(__name__)


class Atom(XtreamCodesProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = AtomConstants.PROVIDER_NAME.lower()
