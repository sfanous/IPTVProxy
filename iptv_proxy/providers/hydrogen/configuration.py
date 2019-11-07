import logging

from iptv_proxy.providers.hydrogen.constants import HydrogenConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class HydrogenConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['url', 'username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = HydrogenConstants.PROVIDER_NAME.lower()


class HydrogenOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = HydrogenConstants.PROVIDER_NAME.lower()
