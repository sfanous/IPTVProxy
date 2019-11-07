import logging

from iptv_proxy.providers.atom.constants import AtomConstants
from iptv_proxy.providers.iptv_provider.configuration import ProviderConfiguration
from iptv_proxy.providers.iptv_provider.configuration import ProviderOptionalSettings

logger = logging.getLogger(__name__)


class AtomConfiguration(ProviderConfiguration):
    __slots__ = []

    _configuration_schema = {'Provider': ['url', 'username', 'password'],
                             'Playlist': ['protocol', 'type'],
                             'EPG': ['source', 'url']}
    _provider_name = AtomConstants.PROVIDER_NAME.lower()


class AtomOptionalSettings(ProviderOptionalSettings):
    __slots__ = []

    _provider_name = AtomConstants.PROVIDER_NAME.lower()
