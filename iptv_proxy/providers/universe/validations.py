import logging

from iptv_proxy.providers.iptv_provider.validations import ProviderValidations
from iptv_proxy.providers.universe.constants import UniverseConstants

logger = logging.getLogger(__name__)


class UniverseValidations(ProviderValidations):
    __slots__ = []

    _provider_name = UniverseConstants.PROVIDER_NAME.lower()
