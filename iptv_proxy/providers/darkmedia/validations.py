import logging

from iptv_proxy.providers.darkmedia.constants import DarkMediaConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class DarkMediaValidations(ProviderValidations):
    __slots__ = []

    _provider_name = DarkMediaConstants.PROVIDER_NAME.lower()
