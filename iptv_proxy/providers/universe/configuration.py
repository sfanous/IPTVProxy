import logging

from iptv_proxy.providers.universe.constants import UniverseConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class UniverseConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = UniverseConstants.PROVIDER_NAME.lower()


class UniverseOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = UniverseConstants.PROVIDER_NAME.lower()
