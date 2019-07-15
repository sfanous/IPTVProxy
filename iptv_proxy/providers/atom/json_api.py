import logging

from iptv_proxy.providers.atom.constants import AtomConstants
from iptv_proxy.providers.iptv_provider.json_api import ProviderConfigurationJSONAPI

logger = logging.getLogger(__name__)


class AtomConfigurationJSONAPI(ProviderConfigurationJSONAPI):
    __slots__ = []

    _provider_name = AtomConstants.PROVIDER_NAME.lower()
