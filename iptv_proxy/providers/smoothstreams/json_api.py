import logging

from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants

logger = logging.getLogger(__name__)


class SmoothStreamsConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
