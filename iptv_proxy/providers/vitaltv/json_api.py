import logging

from iptv_proxy.providers.vitaltv.constants import VitalTVConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class VitalTVConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = VitalTVConstants.PROVIDER_NAME.lower()
