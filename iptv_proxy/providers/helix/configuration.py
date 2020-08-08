import logging

from iptv_proxy.providers.helix.constants import HelixConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class HelixConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {
        'Provider': ['url', 'username', 'password'],
        'Playlist': ['protocol', 'type'],
        'EPG': ['source', 'url'],
    }
    _provider_name = HelixConstants.PROVIDER_NAME.lower()


class HelixOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = HelixConstants.PROVIDER_NAME.lower()
