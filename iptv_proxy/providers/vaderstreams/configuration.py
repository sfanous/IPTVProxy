import logging

from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants

logger = logging.getLogger(__name__)


class VaderStreamsConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['server', 'username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()


class VaderStreamsOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()
