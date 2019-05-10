import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class BeastMap(ProviderMap):
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
    _optional_settings_class = None
    _program_class = None
    _setting_class = None
    _validations_class = None

    @classmethod
    def initialize(cls):
        from iptv_proxy.providers.beast.api import Beast
        from iptv_proxy.providers.beast.configuration import BeastConfiguration
        from iptv_proxy.providers.beast.configuration import BeastOptionalSettings
        from iptv_proxy.providers.beast.constants import BeastConstants
        from iptv_proxy.providers.beast.data_access import BeastDatabaseAccess
        from iptv_proxy.providers.beast.data_model import BeastChannel
        from iptv_proxy.providers.beast.data_model import BeastProgram
        from iptv_proxy.providers.beast.data_model import BeastSetting
        from iptv_proxy.providers.beast.db import BeastDatabase
        from iptv_proxy.providers.beast.enums import BeastEPGSource
        from iptv_proxy.providers.beast.epg import BeastEPG
        from iptv_proxy.providers.beast.json_api import BeastConfigurationJSONAPI
        from iptv_proxy.providers.beast.validations import BeastValidations

        cls._api_class = Beast
        cls._channel_class = BeastChannel
        cls._configuration_class = BeastConfiguration
        cls._constants_class = BeastConstants
        cls._database_access_class = BeastDatabaseAccess
        cls._database_class = BeastDatabase
        cls._epg_class = BeastEPG
        cls._epg_source_enum = BeastEPGSource
        cls._configuration_json_api_class = BeastConfigurationJSONAPI
        cls._optional_settings_class = BeastOptionalSettings
        cls._program_class = BeastProgram
        cls._setting_class = BeastSetting
        cls._validations_class = BeastValidations
