import logging

from iptv_proxy.providers.vitaltv.constants import VitalTVConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class VitalTVValidations(ProviderValidations):
    __slots__ = []

    _provider_name = VitalTVConstants.PROVIDER_NAME.lower()
