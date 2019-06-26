import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class InfernoMap(ProviderMap):
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
        from iptv_proxy.providers.inferno.api import Inferno
        from iptv_proxy.providers.inferno.configuration import InfernoConfiguration
        from iptv_proxy.providers.inferno.configuration import InfernoOptionalSettings
        from iptv_proxy.providers.inferno.constants import InfernoConstants
        from iptv_proxy.providers.inferno.data_access import InfernoDatabaseAccess
        from iptv_proxy.providers.inferno.data_model import InfernoChannel
        from iptv_proxy.providers.inferno.data_model import InfernoProgram
        from iptv_proxy.providers.inferno.data_model import InfernoSetting
        from iptv_proxy.providers.inferno.db import InfernoDatabase
        from iptv_proxy.providers.inferno.enums import InfernoEPGSource
        from iptv_proxy.providers.inferno.epg import InfernoEPG
        from iptv_proxy.providers.inferno.html_template_engine import InfernoHTMLTemplateEngine
        from iptv_proxy.providers.inferno.json_api import InfernoConfigurationJSONAPI
        from iptv_proxy.providers.inferno.validations import InfernoValidations

        cls._api_class = Inferno
        cls._channel_class = InfernoChannel
        cls._configuration_class = InfernoConfiguration
        cls._configuration_json_api_class = InfernoConfigurationJSONAPI
        cls._constants_class = InfernoConstants
        cls._database_access_class = InfernoDatabaseAccess
        cls._database_class = InfernoDatabase
        cls._epg_class = InfernoEPG
        cls._epg_source_enum = InfernoEPGSource
        cls._html_template_engine_class = InfernoHTMLTemplateEngine
        cls._optional_settings_class = InfernoOptionalSettings
        cls._program_class = InfernoProgram
        cls._setting_class = InfernoSetting
        cls._validations_class = InfernoValidations
