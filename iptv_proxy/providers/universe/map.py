import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class UniverseMap(ProviderMap):
    __slots__ = []

    _api_class = None
    _channel_class = None
    _configuration_class = None
    _configuration_json_api_class = None
    _constants_class = None
    _database_access_class = None
    _database_class = None
    _epg_class = None
    _epg_source_enum = None
    _html_template_engine_class = None
    _optional_settings_class = None
    _program_class = None
    _setting_class = None
    _validations_class = None

    @classmethod
    def initialize(cls):
        from iptv_proxy.providers.universe.api import Universe
        from iptv_proxy.providers.universe.configuration import UniverseConfiguration
        from iptv_proxy.providers.universe.configuration import UniverseOptionalSettings
        from iptv_proxy.providers.universe.constants import UniverseConstants
        from iptv_proxy.providers.universe.data_access import UniverseDatabaseAccess
        from iptv_proxy.providers.universe.data_model import UniverseChannel
        from iptv_proxy.providers.universe.data_model import UniverseProgram
        from iptv_proxy.providers.universe.data_model import UniverseSetting
        from iptv_proxy.providers.universe.db import UniverseDatabase
        from iptv_proxy.providers.universe.enums import UniverseEPGSource
        from iptv_proxy.providers.universe.epg import UniverseEPG
        from iptv_proxy.providers.universe.html_template_engine import (
            UniverseHTMLTemplateEngine,
        )
        from iptv_proxy.providers.universe.json_api import UniverseConfigurationJSONAPI
        from iptv_proxy.providers.universe.validations import UniverseValidations

        cls._api_class = Universe
        cls._channel_class = UniverseChannel
        cls._configuration_class = UniverseConfiguration
        cls._configuration_json_api_class = UniverseConfigurationJSONAPI
        cls._constants_class = UniverseConstants
        cls._database_access_class = UniverseDatabaseAccess
        cls._database_class = UniverseDatabase
        cls._epg_class = UniverseEPG
        cls._epg_source_enum = UniverseEPGSource
        cls._html_template_engine_class = UniverseHTMLTemplateEngine
        cls._optional_settings_class = UniverseOptionalSettings
        cls._program_class = UniverseProgram
        cls._setting_class = UniverseSetting
        cls._validations_class = UniverseValidations
