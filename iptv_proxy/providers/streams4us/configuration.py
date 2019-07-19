import logging

from iptv_proxy.providers.streams4us.constants import Streams4UsConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class Streams4UsConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = Streams4UsConstants.PROVIDER_NAME.lower()


class Streams4UsOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = Streams4UsConstants.PROVIDER_NAME.lower()
