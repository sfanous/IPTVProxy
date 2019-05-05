import logging

from iptv_proxy.providers.iptv_provider.validations import ProviderValidations
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants

logger = logging.getLogger(__name__)


class VaderStreamsValidations(ProviderValidations):
    __slots__ = []

    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()
