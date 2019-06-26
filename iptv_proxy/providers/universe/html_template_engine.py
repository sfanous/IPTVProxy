import logging

from iptv_proxy.providers.iptv_provider.html_template_engine import XtreamCodesProviderHTMLTemplateEngine
from iptv_proxy.providers.universe.constants import UniverseConstants

logger = logging.getLogger(__name__)


class UniverseHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = UniverseConstants.PROVIDER_NAME.lower()
