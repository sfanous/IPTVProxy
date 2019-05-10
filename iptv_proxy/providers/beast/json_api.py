import logging

from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class BeastConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = BeastConstants.PROVIDER_NAME.lower()
