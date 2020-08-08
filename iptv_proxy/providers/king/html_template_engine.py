import logging

from iptv_proxy.providers.iptv_provider.html_template_engine import (
    XtreamCodesProviderHTMLTemplateEngine,
)
from iptv_proxy.providers.king.constants import KingConstants

logger = logging.getLogger(__name__)


class KingHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = KingConstants.PROVIDER_NAME.lower()
