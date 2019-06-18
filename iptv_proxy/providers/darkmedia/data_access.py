import logging

from iptv_proxy.providers.darkmedia.constants import DarkMediaConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class DarkMediaDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = DarkMediaConstants.PROVIDER_NAME.lower()
