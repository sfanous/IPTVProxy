import logging

from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings
from iptv_proxy.providers.king.constants import KingConstants

logger = logging.getLogger(__name__)


class KingConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = KingConstants.PROVIDER_NAME.lower()


class KingOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = KingConstants.PROVIDER_NAME.lower()
