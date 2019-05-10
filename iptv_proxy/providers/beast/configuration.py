import logging

from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class BeastConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = BeastConstants.PROVIDER_NAME.lower()


class BeastOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = BeastConstants.PROVIDER_NAME.lower()
