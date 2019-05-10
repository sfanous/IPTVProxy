import logging

from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class BeastValidations(ProviderValidations):
    __slots__ = []

    _provider_name = BeastConstants.PROVIDER_NAME.lower()
