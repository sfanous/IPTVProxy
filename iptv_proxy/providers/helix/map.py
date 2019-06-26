import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class HelixMap(ProviderMap):
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
        from iptv_proxy.providers.helix.api import Helix
        from iptv_proxy.providers.helix.configuration import HelixConfiguration
        from iptv_proxy.providers.helix.configuration import HelixOptionalSettings
        from iptv_proxy.providers.helix.constants import HelixConstants
        from iptv_proxy.providers.helix.data_access import HelixDatabaseAccess
        from iptv_proxy.providers.helix.data_model import HelixChannel
        from iptv_proxy.providers.helix.data_model import HelixProgram
        from iptv_proxy.providers.helix.data_model import HelixSetting
        from iptv_proxy.providers.helix.db import HelixDatabase
        from iptv_proxy.providers.helix.enums import HelixEPGSource
        from iptv_proxy.providers.helix.epg import HelixEPG
        from iptv_proxy.providers.helix.html_template_engine import HelixHTMLTemplateEngine
        from iptv_proxy.providers.helix.json_api import HelixConfigurationJSONAPI
        from iptv_proxy.providers.helix.validations import HelixValidations

        cls._api_class = Helix
        cls._channel_class = HelixChannel
        cls._configuration_class = HelixConfiguration
        cls._configuration_json_api_class = HelixConfigurationJSONAPI
        cls._constants_class = HelixConstants
        cls._database_access_class = HelixDatabaseAccess
        cls._database_class = HelixDatabase
        cls._epg_class = HelixEPG
        cls._epg_source_enum = HelixEPGSource
        cls._html_template_engine_class = HelixHTMLTemplateEngine
        cls._optional_settings_class = HelixOptionalSettings
        cls._program_class = HelixProgram
        cls._setting_class = HelixSetting
        cls._validations_class = HelixValidations
