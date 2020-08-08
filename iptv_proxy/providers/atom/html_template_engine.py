import logging

from iptv_proxy.providers.atom.constants import AtomConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    XtreamCodesProviderHTMLTemplateEngine,
)

logger = logging.getLogger(__name__)


class AtomHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = AtomConstants.PROVIDER_NAME.lower()
