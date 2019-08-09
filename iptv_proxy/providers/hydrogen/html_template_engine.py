import logging

from iptv_proxy.providers.hydrogen.constants import HydrogenConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import XtreamCodesProviderHTMLTemplateEngine

logger = logging.getLogger(__name__)


class HydrogenHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = HydrogenConstants.PROVIDER_NAME.lower()
