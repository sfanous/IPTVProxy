import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class DarkMediaMap(ProviderMap):
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
        from iptv_proxy.providers.darkmedia.api import DarkMedia
        from iptv_proxy.providers.darkmedia.configuration import DarkMediaConfiguration
        from iptv_proxy.providers.darkmedia.configuration import DarkMediaOptionalSettings
        from iptv_proxy.providers.darkmedia.constants import DarkMediaConstants
        from iptv_proxy.providers.darkmedia.data_access import DarkMediaDatabaseAccess
        from iptv_proxy.providers.darkmedia.data_model import DarkMediaChannel
        from iptv_proxy.providers.darkmedia.data_model import DarkMediaProgram
        from iptv_proxy.providers.darkmedia.data_model import DarkMediaSetting
        from iptv_proxy.providers.darkmedia.db import DarkMediaDatabase
        from iptv_proxy.providers.darkmedia.enums import DarkMediaEPGSource
        from iptv_proxy.providers.darkmedia.epg import DarkMediaEPG
        from iptv_proxy.providers.darkmedia.json_api import DarkMediaConfigurationJSONAPI
        from iptv_proxy.providers.darkmedia.validations import DarkMediaValidations

        cls._api_class = DarkMedia
        cls._channel_class = DarkMediaChannel
        cls._configuration_class = DarkMediaConfiguration
        cls._constants_class = DarkMediaConstants
        cls._database_access_class = DarkMediaDatabaseAccess
        cls._database_class = DarkMediaDatabase
        cls._epg_class = DarkMediaEPG
        cls._epg_source_enum = DarkMediaEPGSource
        cls._configuration_json_api_class = DarkMediaConfigurationJSONAPI
        cls._optional_settings_class = DarkMediaOptionalSettings
        cls._program_class = DarkMediaProgram
        cls._setting_class = DarkMediaSetting
        cls._validations_class = DarkMediaValidations
