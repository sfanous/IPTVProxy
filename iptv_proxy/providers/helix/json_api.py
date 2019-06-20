import logging

from iptv_proxy.providers.helix.constants import HelixConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class HelixConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = HelixConstants.PROVIDER_NAME.lower()
