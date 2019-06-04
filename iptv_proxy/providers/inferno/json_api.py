import logging

from iptv_proxy.providers.inferno.constants import InfernoConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class InfernoConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = InfernoConstants.PROVIDER_NAME.lower()
