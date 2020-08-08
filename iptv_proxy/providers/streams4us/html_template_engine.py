import logging

from iptv_proxy.providers.streams4us.constants import Streams4UsConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    XtreamCodesProviderHTMLTemplateEngine,
)

logger = logging.getLogger(__name__)


class Streams4UsHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = Streams4UsConstants.PROVIDER_NAME.lower()
