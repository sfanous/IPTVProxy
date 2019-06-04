import logging

from iptv_proxy.providers.inferno.constants import InfernoConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class InfernoValidations(ProviderValidations):
    __slots__ = []

    _provider_name = InfernoConstants.PROVIDER_NAME.lower()
