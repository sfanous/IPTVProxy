import logging

from iptv_proxy.providers.iptv_provider.map import ProviderMap

logger = logging.getLogger(__name__)


class AtomMap(ProviderMap):
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
        from iptv_proxy.providers.atom.api import Atom
        from iptv_proxy.providers.atom.configuration import AtomConfiguration
        from iptv_proxy.providers.atom.configuration import AtomOptionalSettings
        from iptv_proxy.providers.atom.constants import AtomConstants
        from iptv_proxy.providers.atom.data_access import AtomDatabaseAccess
        from iptv_proxy.providers.atom.data_model import AtomChannel
        from iptv_proxy.providers.atom.data_model import AtomProgram
        from iptv_proxy.providers.atom.data_model import AtomSetting
        from iptv_proxy.providers.atom.db import AtomDatabase
        from iptv_proxy.providers.atom.enums import AtomEPGSource
        from iptv_proxy.providers.atom.epg import AtomEPG
        from iptv_proxy.providers.atom.html_template_engine import AtomHTMLTemplateEngine
        from iptv_proxy.providers.atom.json_api import AtomConfigurationJSONAPI
        from iptv_proxy.providers.atom.validations import AtomValidations

        cls._api_class = Atom
        cls._channel_class = AtomChannel
        cls._configuration_class = AtomConfiguration
        cls._configuration_json_api_class = AtomConfigurationJSONAPI
        cls._constants_class = AtomConstants
        cls._database_access_class = AtomDatabaseAccess
        cls._database_class = AtomDatabase
        cls._epg_class = AtomEPG
        cls._epg_source_enum = AtomEPGSource
        cls._html_template_engine_class = AtomHTMLTemplateEngine
        cls._optional_settings_class = AtomOptionalSettings
        cls._program_class = AtomProgram
        cls._setting_class = AtomSetting
        cls._validations_class = AtomValidations
