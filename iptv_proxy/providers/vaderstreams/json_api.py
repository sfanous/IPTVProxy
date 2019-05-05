import logging

from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants

logger = logging.getLogger(__name__)


class VaderStreamsConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()
