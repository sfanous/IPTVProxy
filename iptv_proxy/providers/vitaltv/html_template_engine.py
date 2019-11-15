import logging

from iptv_proxy.providers.vitaltv.constants import VitalTVConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import XtreamCodesProviderHTMLTemplateEngine

logger = logging.getLogger(__name__)


class VitalTVHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = VitalTVConstants.PROVIDER_NAME.lower()
