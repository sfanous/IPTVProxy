import logging

from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants

logger = logging.getLogger(__name__)


class SmoothStreamsDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
