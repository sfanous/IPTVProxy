import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class Streams4UsMap(ProviderMap):
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
        from iptv_proxy.providers.streams4us.api import Streams4Us
        from iptv_proxy.providers.streams4us.configuration import Streams4UsConfiguration
        from iptv_proxy.providers.streams4us.configuration import Streams4UsOptionalSettings
        from iptv_proxy.providers.streams4us.constants import Streams4UsConstants
        from iptv_proxy.providers.streams4us.data_access import Streams4UsDatabaseAccess
        from iptv_proxy.providers.streams4us.data_model import Streams4UsChannel
        from iptv_proxy.providers.streams4us.data_model import Streams4UsProgram
        from iptv_proxy.providers.streams4us.data_model import Streams4UsSetting
        from iptv_proxy.providers.streams4us.db import Streams4UsDatabase
        from iptv_proxy.providers.streams4us.enums import Streams4UsEPGSource
        from iptv_proxy.providers.streams4us.epg import Streams4UsEPG
        from iptv_proxy.providers.streams4us.html_template_engine import Streams4UsHTMLTemplateEngine
        from iptv_proxy.providers.streams4us.json_api import Streams4UsConfigurationJSONAPI
        from iptv_proxy.providers.streams4us.validations import Streams4UsValidations

        cls._api_class = Streams4Us
        cls._channel_class = Streams4UsChannel
        cls._configuration_class = Streams4UsConfiguration
        cls._configuration_json_api_class = Streams4UsConfigurationJSONAPI
        cls._constants_class = Streams4UsConstants
        cls._database_access_class = Streams4UsDatabaseAccess
        cls._database_class = Streams4UsDatabase
        cls._epg_class = Streams4UsEPG
        cls._epg_source_enum = Streams4UsEPGSource
        cls._html_template_engine_class = Streams4UsHTMLTemplateEngine
        cls._optional_settings_class = Streams4UsOptionalSettings
        cls._program_class = Streams4UsProgram
        cls._setting_class = Streams4UsSetting
        cls._validations_class = Streams4UsValidations
