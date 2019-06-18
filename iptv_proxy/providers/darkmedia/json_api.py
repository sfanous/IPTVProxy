import logging

from iptv_proxy.providers.darkmedia.constants import DarkMediaConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class DarkMediaConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = DarkMediaConstants.PROVIDER_NAME.lower()
