import logging

from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class CoolAsIceConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['url', 'username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()


class CoolAsIceOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()
