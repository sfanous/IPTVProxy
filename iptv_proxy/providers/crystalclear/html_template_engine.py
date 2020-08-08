import logging

from iptv_proxy.providers.crystalclear.constants import CrystalClearConstants
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    XtreamCodesProviderHTMLTemplateEngine,
)

logger = logging.getLogger(__name__)


class CrystalClearHTMLTemplateEngine(XtreamCodesProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = CrystalClearConstants.PROVIDER_NAME.lower()
