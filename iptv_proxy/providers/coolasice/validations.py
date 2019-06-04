import logging

from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class CoolAsIceValidations(ProviderValidations):
    __slots__ = []

    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()
