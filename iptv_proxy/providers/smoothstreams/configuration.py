import logging

from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants

logger = logging.getLogger(__name__)


class SmoothStreamsConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['service', 'server', 'username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()


class SmoothStreamsOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
