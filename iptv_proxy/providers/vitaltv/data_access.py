import logging

from iptv_proxy.providers.vitaltv.constants import VitalTVConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class VitalTVDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = VitalTVConstants.PROVIDER_NAME.lower()
