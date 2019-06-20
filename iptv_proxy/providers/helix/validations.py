import logging

from iptv_proxy.providers.helix.constants import HelixConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class HelixValidations(ProviderValidations):
    __slots__ = []

    _provider_name = HelixConstants.PROVIDER_NAME.lower()
