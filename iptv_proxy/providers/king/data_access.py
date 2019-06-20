import logging

from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess
from iptv_proxy.providers.king.constants import KingConstants

logger = logging.getLogger(__name__)


class KingDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = KingConstants.PROVIDER_NAME.lower()
