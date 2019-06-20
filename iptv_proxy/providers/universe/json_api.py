import logging

from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI
from iptv_proxy.providers.universe.constants import UniverseConstants

logger = logging.getLogger(__name__)


class UniverseConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = UniverseConstants.PROVIDER_NAME.lower()
