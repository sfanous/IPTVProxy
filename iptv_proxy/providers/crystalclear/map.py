import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class CrystalClearMap(ProviderMap):
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
        from iptv_proxy.providers.crystalclear.api import CrystalClear
        from iptv_proxy.providers.crystalclear.configuration import CrystalClearConfiguration
        from iptv_proxy.providers.crystalclear.configuration import CrystalClearOptionalSettings
        from iptv_proxy.providers.crystalclear.constants import CrystalClearConstants
        from iptv_proxy.providers.crystalclear.data_access import CrystalClearDatabaseAccess
        from iptv_proxy.providers.crystalclear.data_model import CrystalClearChannel
        from iptv_proxy.providers.crystalclear.data_model import CrystalClearProgram
        from iptv_proxy.providers.crystalclear.data_model import CrystalClearSetting
        from iptv_proxy.providers.crystalclear.db import CrystalClearDatabase
        from iptv_proxy.providers.crystalclear.enums import CrystalClearEPGSource
        from iptv_proxy.providers.crystalclear.epg import CrystalClearEPG
        from iptv_proxy.providers.crystalclear.html_template_engine import CrystalClearHTMLTemplateEngine
        from iptv_proxy.providers.crystalclear.json_api import CrystalClearConfigurationJSONAPI
        from iptv_proxy.providers.crystalclear.validations import CrystalClearValidations

        cls._api_class = CrystalClear
        cls._channel_class = CrystalClearChannel
        cls._configuration_class = CrystalClearConfiguration
        cls._configuration_json_api_class = CrystalClearConfigurationJSONAPI
        cls._constants_class = CrystalClearConstants
        cls._database_access_class = CrystalClearDatabaseAccess
        cls._database_class = CrystalClearDatabase
        cls._epg_class = CrystalClearEPG
        cls._epg_source_enum = CrystalClearEPGSource
        cls._html_template_engine_class = CrystalClearHTMLTemplateEngine
        cls._optional_settings_class = CrystalClearOptionalSettings
        cls._program_class = CrystalClearProgram
        cls._setting_class = CrystalClearSetting
        cls._validations_class = CrystalClearValidations
