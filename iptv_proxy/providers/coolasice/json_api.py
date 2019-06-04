import logging

from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class CoolAsIceConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()
