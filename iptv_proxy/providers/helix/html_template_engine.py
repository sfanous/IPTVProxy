import logging

from iptv_proxy.providers.helix.constants import HelixConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    XtreamCodesProviderHTMLTemplateEngine,
)

logger = logging.getLogger(__name__)


class HelixHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = HelixConstants.PROVIDER_NAME.lower()
