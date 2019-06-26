from abc import ABC
from abc import abstractmethod


class ProviderMap(ABC):
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
    @abstractmethod
    def initialize(cls):
        pass

    @classmethod
    def api_class(cls):
        return cls._api_class

    @classmethod
    def channel_class(cls):
        return cls._channel_class

    @classmethod
    def configuration_class(cls):
        return cls._configuration_class

    @classmethod
    def configuration_json_api_class(cls):
        return cls._configuration_json_api_class

    @classmethod
    def constants_class(cls):
        return cls._constants_class

    @classmethod
    def database_access_class(cls):
        return cls._database_access_class

    @classmethod
    def database_class(cls):
        return cls._database_class

    @classmethod
    def epg_class(cls):
        return cls._epg_class

    @classmethod
    def epg_source_enum(cls):
        return cls._epg_source_enum

    @classmethod
    def html_template_engine_class(cls):
        return cls._html_template_engine_class

    @classmethod
    def optional_settings_class(cls):
        return cls._optional_settings_class

    @classmethod
    def program_class(cls):
        return cls._program_class

    @classmethod
    def setting_class(cls):
        return cls._setting_class

    @classmethod
    def validations_class(cls):
        return cls._validations_class
