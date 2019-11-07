import logging

from iptv_proxy.providers import ProvidersController

logger = logging.getLogger(__name__)


class ProviderConfigurationJSONAPI(object):
    __slots__ = []

    _provider_name = None

    @classmethod
    def create_get_request_response_content(cls, configuration):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        provider_configuration_schema = provider_map_class.configuration_class().get_configuration_schema()

        configuration_parameter_name_prefix = cls._provider_name.upper()

        provider_configuration = {}

        if 'service' in provider_configuration_schema['Provider']:
            if '{0}_SERVICE'.format(configuration_parameter_name_prefix) in configuration:
                provider_configuration['{0}_service'.format(cls._provider_name)] = configuration['{0}_SERVICE'.format(
                    configuration_parameter_name_prefix)]
            else:
                provider_configuration['{0}_service'.format(cls._provider_name)] = ''

        if 'server' in provider_configuration_schema['Provider']:
            if '{0}_SERVER'.format(configuration_parameter_name_prefix) in configuration:
                provider_configuration['{0}_server'.format(cls._provider_name)] = configuration['{0}_SERVER'.format(
                    configuration_parameter_name_prefix)]
            else:
                provider_configuration['{0}_server'.format(cls._provider_name)] = ''

        if 'url' in provider_configuration_schema['Provider']:
            if '{0}_URL'.format(configuration_parameter_name_prefix) in configuration:
                provider_configuration['{0}_url'.format(cls._provider_name)] = configuration['{0}_URL'.format(
                    configuration_parameter_name_prefix)]
            else:
                provider_configuration['{0}_url'.format(cls._provider_name)] = ''

        if 'username' in provider_configuration_schema['Provider']:
            if '{0}_USERNAME'.format(configuration_parameter_name_prefix) in configuration:
                provider_configuration['{0}_username'.format(cls._provider_name)] = configuration['{0}_USERNAME'.format(
                    configuration_parameter_name_prefix)]
            else:
                provider_configuration['{0}_username'.format(cls._provider_name)] = ''

        if 'password' in provider_configuration_schema['Provider']:
            if '{0}_PASSWORD'.format(configuration_parameter_name_prefix) in configuration:
                provider_configuration['{0}_password'.format(cls._provider_name)] = configuration['{0}_PASSWORD'.format(
                    configuration_parameter_name_prefix)]
            else:
                provider_configuration['{0}_password'.format(cls._provider_name)] = ''

        if 'Playlist' in provider_configuration_schema:
            if 'protocol' in provider_configuration_schema['Playlist']:
                if '{0}_PLAYLIST_PROTOCOL'.format(configuration_parameter_name_prefix) in configuration:
                    provider_configuration['{0}_playlist_protocol'.format(cls._provider_name)] = \
                        configuration['{0}_PLAYLIST_PROTOCOL'.format(configuration_parameter_name_prefix)]
                else:
                    provider_configuration['{0}_playlist_protocol'.format(cls._provider_name)] = ''

            if 'type' in provider_configuration_schema['Playlist']:
                if '{0}_PLAYLIST_TYPE'.format(configuration_parameter_name_prefix) in configuration:
                    provider_configuration['{0}_playlist_type'.format(cls._provider_name)] = \
                        configuration['{0}_PLAYLIST_TYPE'.format(configuration_parameter_name_prefix)]
                else:
                    provider_configuration['{0}_playlist_type'.format(cls._provider_name)] = ''

        if 'EPG' in provider_configuration_schema:
            if 'source' in provider_configuration_schema['EPG']:
                if '{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix) in configuration:
                    provider_configuration['{0}_epg_source'.format(cls._provider_name)] = \
                        configuration['{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)]
                else:
                    provider_configuration['{0}_epg_source'.format(cls._provider_name)] = ''

            if 'url' in provider_configuration_schema['EPG']:
                if '{0}_EPG_URL'.format(configuration_parameter_name_prefix) in configuration and \
                        configuration['{0}_EPG_URL'.format(configuration_parameter_name_prefix)] is not None:
                    provider_configuration['{0}_epg_url'.format(cls._provider_name)] = \
                        configuration['{0}_EPG_URL'.format(configuration_parameter_name_prefix)]
                else:
                    provider_configuration['{0}_epg_url'.format(cls._provider_name)] = ''

        return provider_configuration

    @classmethod
    def create_patch_request_update_configuration_request(cls, request_body):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        provider_configuration_schema = provider_map_class.configuration_class().get_configuration_schema()

        configuration_parameter_name_prefix = cls._provider_name.upper()

        update_configuration_request = {}

        attributes = request_body['data']['attributes']

        if attributes['{0}_enabled'.format(cls._provider_name)]:
            if 'service' in provider_configuration_schema['Provider']:
                update_configuration_request['{0}_SERVICE'.format(configuration_parameter_name_prefix)] = \
                    attributes['{0}_service'.format(cls._provider_name)].lower()

            if 'server' in provider_configuration_schema['Provider']:
                update_configuration_request['{0}_SERVER'.format(configuration_parameter_name_prefix)] = \
                    attributes['{0}_server'.format(cls._provider_name)].lower()

            if 'url' in provider_configuration_schema['Provider']:
                update_configuration_request['{0}_URL'.format(configuration_parameter_name_prefix)] = \
                    attributes['{0}_url'.format(cls._provider_name)].lower()

            if 'username' in provider_configuration_schema['Provider']:
                update_configuration_request['{0}_USERNAME'.format(configuration_parameter_name_prefix)] = \
                    attributes['{0}_username'.format(cls._provider_name)]

            if 'password' in provider_configuration_schema['Provider']:
                update_configuration_request['{0}_PASSWORD'.format(configuration_parameter_name_prefix)] = \
                    attributes['{0}_password'.format(cls._provider_name)]

            if 'Playlist' in provider_configuration_schema:
                if 'protocol' in provider_configuration_schema['Playlist']:
                    update_configuration_request['{0}_PLAYLIST_PROTOCOL'.format(
                        configuration_parameter_name_prefix)] = \
                        attributes['{0}_playlist_protocol'.format(cls._provider_name)].lower()

                if 'type' in provider_configuration_schema['Playlist']:
                    update_configuration_request['{0}_PLAYLIST_TYPE'.format(configuration_parameter_name_prefix)] = \
                        attributes['{0}_playlist_type'.format(cls._provider_name)].lower()

            if 'EPG' in provider_configuration_schema:
                if 'source' in provider_configuration_schema['EPG']:
                    update_configuration_request['{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)] = \
                        attributes['{0}_epg_source'.format(cls._provider_name)].lower()

                if 'url' in provider_configuration_schema['EPG']:
                    update_configuration_request['{0}_EPG_URL'.format(configuration_parameter_name_prefix)] = \
                        attributes['{0}_epg_url'.format(cls._provider_name)].lower()

        return update_configuration_request

    @classmethod
    def create_validate_patch_request_body_schema(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        provider_configuration_schema = provider_map_class.configuration_class().get_configuration_schema()

        validate_patch_request_body_schema = {}
        required = {'required': True}

        validate_patch_request_body_schema['{0}_enabled'.format(cls._provider_name)] = required

        if 'service' in provider_configuration_schema['Provider']:
            validate_patch_request_body_schema['{0}_service'.format(cls._provider_name)] = required

        if 'server' in provider_configuration_schema['Provider']:
            validate_patch_request_body_schema['{0}_server'.format(cls._provider_name)] = required

        if 'url' in provider_configuration_schema['Provider']:
            validate_patch_request_body_schema['{0}_url'.format(cls._provider_name)] = required

        if 'username' in provider_configuration_schema['Provider']:
            validate_patch_request_body_schema['{0}_username'.format(cls._provider_name)] = required

        if 'password' in provider_configuration_schema['Provider']:
            validate_patch_request_body_schema['{0}_password'.format(cls._provider_name)] = required

        if 'Playlist' in provider_configuration_schema:
            if 'protocol' in provider_configuration_schema['Playlist']:
                validate_patch_request_body_schema['{0}_playlist_protocol'.format(cls._provider_name)] = required

            if 'type' in provider_configuration_schema['Playlist']:
                validate_patch_request_body_schema['{0}_playlist_type'.format(cls._provider_name)] = required

        if 'EPG' in provider_configuration_schema:
            if 'source' in provider_configuration_schema['EPG']:
                validate_patch_request_body_schema['{0}_epg_source'.format(cls._provider_name)] = required

            if 'url' in provider_configuration_schema['EPG']:
                validate_patch_request_body_schema['{0}_epg_url'.format(cls._provider_name)] = required

        return validate_patch_request_body_schema
