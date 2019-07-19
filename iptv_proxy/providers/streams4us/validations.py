import logging

from iptv_proxy.providers.streams4us.constants import Streams4UsConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class Streams4UsValidations(ProviderValidations):
    __slots__ = []

    _provider_name = Streams4UsConstants.PROVIDER_NAME.lower()
