import logging

from iptv_proxy.providers.inferno.constants import InfernoConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class InfernoConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = InfernoConstants.PROVIDER_NAME.lower()


class InfernoOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = InfernoConstants.PROVIDER_NAME.lower()
