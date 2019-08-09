import logging

from iptv_proxy.providers.hydrogen.constants import HydrogenConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class HydrogenValidations(ProviderValidations):
    __slots__ = []

    _provider_name = HydrogenConstants.PROVIDER_NAME.lower()
