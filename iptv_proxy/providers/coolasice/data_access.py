import logging

from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class CoolAsIceDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()
