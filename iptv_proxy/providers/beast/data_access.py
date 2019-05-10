import logging

from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class BeastDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = BeastConstants.PROVIDER_NAME.lower()
