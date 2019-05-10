import logging

from iptv_proxy.providers.crystalclear.constants import CrystalClearConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class CrystalClearDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = CrystalClearConstants.PROVIDER_NAME.lower()
