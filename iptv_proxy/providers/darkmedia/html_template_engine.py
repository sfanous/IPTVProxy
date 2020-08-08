import logging

from iptv_proxy.providers.darkmedia.constants import DarkMediaConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    XtreamCodesProviderHTMLTemplateEngine,
)

logger = logging.getLogger(__name__)


class DarkMediaHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = DarkMediaConstants.PROVIDER_NAME.lower()
