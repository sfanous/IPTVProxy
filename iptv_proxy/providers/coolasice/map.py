import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class CoolAsIceMap(ProviderMap):
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
        from iptv_proxy.providers.coolasice.api import CoolAsIce
        from iptv_proxy.providers.coolasice.configuration import CoolAsIceConfiguration
        from iptv_proxy.providers.coolasice.configuration import CoolAsIceOptionalSettings
        from iptv_proxy.providers.coolasice.constants import CoolAsIceConstants
        from iptv_proxy.providers.coolasice.data_access import CoolAsIceDatabaseAccess
        from iptv_proxy.providers.coolasice.data_model import CoolAsIceChannel
        from iptv_proxy.providers.coolasice.data_model import CoolAsIceProgram
        from iptv_proxy.providers.coolasice.data_model import CoolAsIceSetting
        from iptv_proxy.providers.coolasice.db import CoolAsIceDatabase
        from iptv_proxy.providers.coolasice.enums import CoolAsIceEPGSource
        from iptv_proxy.providers.coolasice.epg import CoolAsIceEPG
        from iptv_proxy.providers.coolasice.html_template_engine import CoolAsIceHTMLTemplateEngine
        from iptv_proxy.providers.coolasice.json_api import CoolAsIceConfigurationJSONAPI
        from iptv_proxy.providers.coolasice.validations import CoolAsIceValidations

        cls._api_class = CoolAsIce
        cls._channel_class = CoolAsIceChannel
        cls._configuration_class = CoolAsIceConfiguration
        cls._configuration_json_api_class = CoolAsIceConfigurationJSONAPI
        cls._constants_class = CoolAsIceConstants
        cls._database_access_class = CoolAsIceDatabaseAccess
        cls._database_class = CoolAsIceDatabase
        cls._epg_class = CoolAsIceEPG
        cls._epg_source_enum = CoolAsIceEPGSource
        cls._html_template_engine_class = CoolAsIceHTMLTemplateEngine
        cls._optional_settings_class = CoolAsIceOptionalSettings
        cls._program_class = CoolAsIceProgram
        cls._setting_class = CoolAsIceSetting
        cls._validations_class = CoolAsIceValidations
