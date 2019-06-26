import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class KingMap(ProviderMap):
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
        from iptv_proxy.providers.king.api import King
        from iptv_proxy.providers.king.configuration import KingConfiguration
        from iptv_proxy.providers.king.configuration import KingOptionalSettings
        from iptv_proxy.providers.king.constants import KingConstants
        from iptv_proxy.providers.king.data_access import KingDatabaseAccess
        from iptv_proxy.providers.king.data_model import KingChannel
        from iptv_proxy.providers.king.data_model import KingProgram
        from iptv_proxy.providers.king.data_model import KingSetting
        from iptv_proxy.providers.king.db import KingDatabase
        from iptv_proxy.providers.king.enums import KingEPGSource
        from iptv_proxy.providers.king.epg import KingEPG
        from iptv_proxy.providers.king.html_template_engine import KingHTMLTemplateEngine
        from iptv_proxy.providers.king.json_api import KingConfigurationJSONAPI
        from iptv_proxy.providers.king.validations import KingValidations

        cls._api_class = King
        cls._channel_class = KingChannel
        cls._configuration_class = KingConfiguration
        cls._configuration_json_api_class = KingConfigurationJSONAPI
        cls._constants_class = KingConstants
        cls._database_access_class = KingDatabaseAccess
        cls._database_class = KingDatabase
        cls._epg_class = KingEPG
        cls._epg_source_enum = KingEPGSource
        cls._html_template_engine_class = KingHTMLTemplateEngine
        cls._optional_settings_class = KingOptionalSettings
        cls._program_class = KingProgram
        cls._setting_class = KingSetting
        cls._validations_class = KingValidations
