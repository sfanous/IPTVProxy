import logging
from collections import OrderedDict
from threading import RLock

from rwlock import RWLock

from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.epg import XStreamCodesProviderEPG

logger = logging.getLogger(__name__)


class BeastEPG(XStreamCodesProviderEPG):
    __slots__ = []

    _channel_group_map = OrderedDict(
        [('name', OrderedDict()), ('number', OrderedDict())]
    )
    _channel_group_map_lock = RWLock()
    _channel_name_map = OrderedDict()
    _channel_name_map_lock = RWLock()
    _do_use_provider_icons = False
    _do_use_provider_icons_lock = RWLock()
    _ignored_channels = OrderedDict(
        [('name', OrderedDict()), ('number', OrderedDict())]
    )
    _ignored_channels_lock = RWLock()
    _ignored_m3u8_groups = []
    _ignored_m3u8_groups_lock = RWLock()
    _lock = RLock()
    _m3u8_group_map = OrderedDict()
    _m3u8_group_map_lock = RWLock()
    _provider_name = BeastConstants.PROVIDER_NAME.lower()
    _refresh_epg_timer = None
    _update_times = ['06:00:00']
    _update_times_lock = RWLock()
