import logging

from iptv_proxy.providers.atom.constants import AtomConstants
from iptv_proxy.providers.iptv_provider.data_access import ProviderDatabaseAccess

logger = logging.getLogger(__name__)


class AtomDatabaseAccess(ProviderDatabaseAccess):
    __slots__ = []

    _provider_name = AtomConstants.PROVIDER_NAME.lower()
