import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class VitalTVMap(ProviderMap):
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
        from iptv_proxy.providers.vitaltv.api import VitalTV
        from iptv_proxy.providers.vitaltv.configuration import VitalTVConfiguration
        from iptv_proxy.providers.vitaltv.configuration import VitalTVOptionalSettings
        from iptv_proxy.providers.vitaltv.constants import VitalTVConstants
        from iptv_proxy.providers.vitaltv.data_access import VitalTVDatabaseAccess
        from iptv_proxy.providers.vitaltv.data_model import VitalTVChannel
        from iptv_proxy.providers.vitaltv.data_model import VitalTVProgram
        from iptv_proxy.providers.vitaltv.data_model import VitalTVSetting
        from iptv_proxy.providers.vitaltv.db import VitalTVDatabase
        from iptv_proxy.providers.vitaltv.enums import VitalTVEPGSource
        from iptv_proxy.providers.vitaltv.epg import VitalTVEPG
        from iptv_proxy.providers.vitaltv.html_template_engine import VitalTVHTMLTemplateEngine
        from iptv_proxy.providers.vitaltv.json_api import VitalTVConfigurationJSONAPI
        from iptv_proxy.providers.vitaltv.validations import VitalTVValidations

        cls._api_class = VitalTV
        cls._channel_class = VitalTVChannel
        cls._configuration_class = VitalTVConfiguration
        cls._configuration_json_api_class = VitalTVConfigurationJSONAPI
        cls._constants_class = VitalTVConstants
        cls._database_access_class = VitalTVDatabaseAccess
        cls._database_class = VitalTVDatabase
        cls._epg_class = VitalTVEPG
        cls._epg_source_enum = VitalTVEPGSource
        cls._html_template_engine_class = VitalTVHTMLTemplateEngine
        cls._optional_settings_class = VitalTVOptionalSettings
        cls._program_class = VitalTVProgram
        cls._setting_class = VitalTVSetting
        cls._validations_class = VitalTVValidations
