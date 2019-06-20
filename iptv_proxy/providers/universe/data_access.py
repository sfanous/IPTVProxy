import logging

from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess
from iptv_proxy.providers.universe.constants import UniverseConstants

logger = logging.getLogger(__name__)


class UniverseDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = UniverseConstants.PROVIDER_NAME.lower()
