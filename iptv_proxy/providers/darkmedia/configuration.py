import logging

from iptv_proxy.providers.darkmedia.constants import DarkMediaConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class DarkMediaConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {
        'Provider': ['url', 'username', 'password'],
        'Playlist': ['protocol', 'type'],
        'EPG': ['source', 'url'],
    }
    _provider_name = DarkMediaConstants.PROVIDER_NAME.lower()


class DarkMediaOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = DarkMediaConstants.PROVIDER_NAME.lower()
