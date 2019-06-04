import logging

from iptv_proxy.providers.inferno.constants import InfernoConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class InfernoDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = InfernoConstants.PROVIDER_NAME.lower()
