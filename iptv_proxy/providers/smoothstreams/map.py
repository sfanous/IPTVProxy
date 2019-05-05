import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class SmoothStreamsMap(ProviderMap):
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
        from iptv_proxy.providers.smoothstreams.api import SmoothStreams
        from iptv_proxy.providers.smoothstreams.configuration import SmoothStreamsConfiguration
        from iptv_proxy.providers.smoothstreams.configuration import SmoothStreamsOptionalSettings
        from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants
        from iptv_proxy.providers.smoothstreams.data_access import SmoothStreamsDatabaseAccess
        from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsChannel
        from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsProgram
        from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsSetting
        from iptv_proxy.providers.smoothstreams.db import SmoothStreamsDatabase
        from iptv_proxy.providers.smoothstreams.enums import SmoothStreamsEPGSource
        from iptv_proxy.providers.smoothstreams.epg import SmoothStreamsEPG
        from iptv_proxy.providers.smoothstreams.json_api import SmoothStreamsConfigurationJSONAPI
        from iptv_proxy.providers.smoothstreams.validations import SmoothStreamsValidations

        cls._api_class = SmoothStreams
        cls._channel_class = SmoothStreamsChannel
        cls._configuration_class = SmoothStreamsConfiguration
        cls._configuration_json_api_class = SmoothStreamsConfigurationJSONAPI
        cls._constants_class = SmoothStreamsConstants
        cls._database_access_class = SmoothStreamsDatabaseAccess
        cls._database_class = SmoothStreamsDatabase
        cls._epg_class = SmoothStreamsEPG
        cls._epg_source_enum = SmoothStreamsEPGSource
        cls._optional_settings_class = SmoothStreamsOptionalSettings
        cls._program_class = SmoothStreamsProgram
        cls._setting_class = SmoothStreamsSetting
        cls._validations_class = SmoothStreamsValidations
