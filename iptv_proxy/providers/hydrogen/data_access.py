import logging

from iptv_proxy.providers.hydrogen.constants import HydrogenConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class HydrogenDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = HydrogenConstants.PROVIDER_NAME.lower()
