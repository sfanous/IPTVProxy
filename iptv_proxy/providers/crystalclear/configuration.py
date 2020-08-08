import logging

from iptv_proxy.providers.crystalclear.constants import CrystalClearConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class CrystalClearConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {
        'Provider': ['url', 'username', 'password'],
        'Playlist': ['protocol', 'type'],
        'EPG': ['source', 'url'],
    }
    _provider_name = CrystalClearConstants.PROVIDER_NAME.lower()


class CrystalClearOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = CrystalClearConstants.PROVIDER_NAME.lower()
