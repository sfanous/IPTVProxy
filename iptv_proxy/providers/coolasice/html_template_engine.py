import logging

from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import XtreamCodesProviderHTMLTemplateEngine

logger = logging.getLogger(__name__)


class CoolAsIceHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = CoolAsIceConstants.PROVIDER_NAME.lower()
