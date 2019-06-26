import logging

from iptv_proxy.providers.beast.constants import BeastConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import XtreamCodesProviderHTMLTemplateEngine

logger = logging.getLogger(__name__)


class BeastHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = BeastConstants.PROVIDER_NAME.lower()
