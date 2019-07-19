import logging

from iptv_proxy.providers.streams4us.constants import Streams4UsConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class Streams4UsDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = Streams4UsConstants.PROVIDER_NAME.lower()
