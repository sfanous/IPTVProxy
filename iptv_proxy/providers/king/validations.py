import logging

from iptv_proxy.providers.iptv_provider.validations import ProviderValidations
from iptv_proxy.providers.king.constants import KingConstants

logger = logging.getLogger(__name__)


class KingValidations(ProviderValidations):
    __slots__ = []

    _provider_name = KingConstants.PROVIDER_NAME.lower()
