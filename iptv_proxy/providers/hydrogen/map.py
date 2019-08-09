import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class HydrogenMap(ProviderMap):
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
        from iptv_proxy.providers.hydrogen.api import Hydrogen
        from iptv_proxy.providers.hydrogen.configuration import HydrogenConfiguration
        from iptv_proxy.providers.hydrogen.configuration import HydrogenOptionalSettings
        from iptv_proxy.providers.hydrogen.constants import HydrogenConstants
        from iptv_proxy.providers.hydrogen.data_access import HydrogenDatabaseAccess
        from iptv_proxy.providers.hydrogen.data_model import HydrogenChannel
        from iptv_proxy.providers.hydrogen.data_model import HydrogenProgram
        from iptv_proxy.providers.hydrogen.data_model import HydrogenSetting
        from iptv_proxy.providers.hydrogen.db import HydrogenDatabase
        from iptv_proxy.providers.hydrogen.enums import HydrogenEPGSource
        from iptv_proxy.providers.hydrogen.epg import HydrogenEPG
        from iptv_proxy.providers.hydrogen.html_template_engine import HydrogenHTMLTemplateEngine
        from iptv_proxy.providers.hydrogen.json_api import HydrogenConfigurationJSONAPI
        from iptv_proxy.providers.hydrogen.validations import HydrogenValidations

        cls._api_class = Hydrogen
        cls._channel_class = HydrogenChannel
        cls._configuration_class = HydrogenConfiguration
        cls._configuration_json_api_class = HydrogenConfigurationJSONAPI
        cls._constants_class = HydrogenConstants
        cls._database_access_class = HydrogenDatabaseAccess
        cls._database_class = HydrogenDatabase
        cls._epg_class = HydrogenEPG
        cls._epg_source_enum = HydrogenEPGSource
        cls._html_template_engine_class = HydrogenHTMLTemplateEngine
        cls._optional_settings_class = HydrogenOptionalSettings
        cls._program_class = HydrogenProgram
        cls._setting_class = HydrogenSetting
        cls._validations_class = HydrogenValidations
