import logging

from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants

logger = logging.getLogger(__name__)


class VaderStreamsDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()
