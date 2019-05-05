import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class VaderStreamsMap(ProviderMap):
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
        from iptv_proxy.providers.vaderstreams.api import VaderStreams
        from iptv_proxy.providers.vaderstreams.configuration import VaderStreamsConfiguration
        from iptv_proxy.providers.vaderstreams.configuration import VaderStreamsOptionalSettings
        from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants
        from iptv_proxy.providers.vaderstreams.data_access import VaderStreamsDatabaseAccess
        from iptv_proxy.providers.vaderstreams.data_model import VaderStreamsChannel
        from iptv_proxy.providers.vaderstreams.data_model import VaderStreamsProgram
        from iptv_proxy.providers.vaderstreams.data_model import VaderStreamsSetting
        from iptv_proxy.providers.vaderstreams.db import VaderStreamsDatabase
        from iptv_proxy.providers.vaderstreams.enums import VaderStreamsEPGSource
        from iptv_proxy.providers.vaderstreams.epg import VaderStreamsEPG
        from iptv_proxy.providers.vaderstreams.json_api import VaderStreamsConfigurationJSONAPI
        from iptv_proxy.providers.vaderstreams.validations import VaderStreamsValidations

        cls._api_class = VaderStreams
        cls._channel_class = VaderStreamsChannel
        cls._configuration_class = VaderStreamsConfiguration
        cls._constants_class = VaderStreamsConstants
        cls._database_access_class = VaderStreamsDatabaseAccess
        cls._database_class = VaderStreamsDatabase
        cls._epg_class = VaderStreamsEPG
        cls._epg_source_enum = VaderStreamsEPGSource
        cls._configuration_json_api_class = VaderStreamsConfigurationJSONAPI
        cls._optional_settings_class = VaderStreamsOptionalSettings
        cls._program_class = VaderStreamsProgram
        cls._setting_class = VaderStreamsSetting
        cls._validations_class = VaderStreamsValidations
