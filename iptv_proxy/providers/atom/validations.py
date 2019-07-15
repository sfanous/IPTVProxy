import logging

from iptv_proxy.providers.atom.constants import AtomConstants
from iptv_proxy.providers.iptv_provider.validations import ProviderValidations

logger = logging.getLogger(__name__)


class AtomValidations(ProviderValidations):
    __slots__ = []

    _provider_name = AtomConstants.PROVIDER_NAME.lower()
