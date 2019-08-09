import logging

from iptv_proxy.providers.hydrogen.constants import HydrogenConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class HydrogenConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = HydrogenConstants.PROVIDER_NAME.lower()
