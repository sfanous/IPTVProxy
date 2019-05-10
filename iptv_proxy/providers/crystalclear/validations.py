import logging

from iptv_proxy.providers.crystalclear.constants import CrystalClearConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class CrystalClearValidations(ProviderValidations):
    __slots__ = []

    _provider_name = CrystalClearConstants.PROVIDER_NAME.lower()
