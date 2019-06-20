import logging

from iptv_proxy.providers.helix.constants import HelixConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class HelixDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = HelixConstants.PROVIDER_NAME.lower()
