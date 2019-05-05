import logging

from iptv_proxy.providers.iptv_provider.validations import ProviderValidations
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants

logger = logging.getLogger(__name__)


class SmoothStreamsValidations(ProviderValidations):
    __slots__ = []

    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
