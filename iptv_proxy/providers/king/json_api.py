import logging

from iptv_proxy.providers.king.constants import KingConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class KingConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = KingConstants.PROVIDER_NAME.lower()
