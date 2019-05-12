import copy
import json
import logging

from iptv_proxy.providers import ProvidersController
from iptv_proxy.security import SecurityManager

logger = logging.getLogger(__name__)


class ProviderConfiguration(object):
    __slots__ = []

    _configuration_schema = {}
    _provider_name = None

    @classmethod
    def _scrub_password(cls, configuration_object, configuration):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        section_name = provider_map_class.api_class().__name__

        password = SecurityManager.scrub_password(section_name, configuration_object[section_name]['password'])

        configuration_object[section_name]['password'] = password
        configuration['{0}_PASSWORD'.format(section_name.upper())] = password

    @classmethod
    def create_section(cls, configuration):
        configuration_parameter_name_prefix = cls._provider_name.upper()

        configuration_section = {}

        try:
            if 'service' in cls._configuration_schema['Provider']:
                configuration_section['service'] = configuration['{0}_SERVICE'.format(
                    configuration_parameter_name_prefix)]

            if 'server' in cls._configuration_schema['Provider']:
                configuration_section['server'] = configuration['{0}_SERVER'.format(
                    configuration_parameter_name_prefix)]

            if 'username' in cls._configuration_schema['Provider']:
                configuration_section['username'] = configuration['{0}_USERNAME'.format(
                    configuration_parameter_name_prefix)]

            if 'password' in cls._configuration_schema['Provider']:
                configuration_section['password'] = configuration['{0}_PASSWORD'.format(
                    configuration_parameter_name_prefix)]

            if 'Playlist' in cls._configuration_schema:
                configuration_section['Playlist'] = {}

                if 'protocol' in cls._configuration_schema['Playlist']:
                    configuration_section['Playlist']['protocol'] = configuration['{0}_PLAYLIST_PROTOCOL'.format(
                        configuration_parameter_name_prefix)]

                if 'type' in cls._configuration_schema['Playlist']:
                    configuration_section['Playlist']['type'] = configuration['{0}_PLAYLIST_TYPE'.format(
                        configuration_parameter_name_prefix)]

            if 'EPG' in cls._configuration_schema:
                configuration_section['EPG'] = {}

                if 'source' in cls._configuration_schema['EPG']:
                    configuration_section['EPG']['source'] = configuration['{0}_EPG_SOURCE'.format(
                        configuration_parameter_name_prefix)]

                if 'url' in cls._configuration_schema['EPG']:
                    if configuration['{0}_EPG_URL'.format(configuration_parameter_name_prefix)] is not None:
                        configuration_section['EPG']['url'] = configuration['{0}_EPG_URL'.format(
                            configuration_parameter_name_prefix)]
                    else:
                        configuration_section['EPG']['url'] = ''
        except KeyError:
            pass

        return configuration_section

    @classmethod
    def get_configuration_schema(cls):
        return copy.deepcopy(cls._configuration_schema)

    @classmethod
    def process_configuration_file_updates(cls, configuration, previous_configuration):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        section_name = provider_map_class.api_class().__name__
        configuration_parameter_name_prefix = section_name.upper()

        provider_in_configuration = len([parameter_name for parameter_name in configuration
                                         if parameter_name.startswith(configuration_parameter_name_prefix)])
        provider_in_previous_configuration = len([parameter_name for parameter_name in previous_configuration
                                                  if parameter_name.startswith(configuration_parameter_name_prefix)])

        if provider_in_configuration and provider_in_previous_configuration:
            message_to_log = []

            do_reinitialize = False
            do_refresh_session = False

            # <editor-fold desc="Detect and handle updates to the SERVICE option">
            if 'service' in cls._configuration_schema['Provider']:
                service_parameter_name = '{0}_SERVICE'.format(configuration_parameter_name_prefix)

                if configuration[service_parameter_name] != previous_configuration[service_parameter_name]:
                    do_reinitialize = True
                    do_refresh_session = True

                    message_to_log.append(
                        'Detected a change in the service option in the [{0}] section\n'
                        'Old value => {1}\n'
                        'New value => {2}\n'
                        ''.format(section_name,
                                  previous_configuration[service_parameter_name],
                                  configuration[service_parameter_name]))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the SERVER option">
            if 'server' in cls._configuration_schema['Provider']:
                server_parameter_name = '{0}_SERVER'.format(configuration_parameter_name_prefix)

                if configuration[server_parameter_name] != previous_configuration[server_parameter_name]:
                    if message_to_log:
                        message_to_log.append('')

                    message_to_log.append(
                        'Detected a change in the server option in the [{0}] section\n'
                        'Old value => {1}\n'
                        'New value => {2}\n'
                        ''.format(section_name,
                                  previous_configuration[server_parameter_name],
                                  configuration[server_parameter_name]))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the USERNAME option">
            if 'username' in cls._configuration_schema['Provider']:
                username_parameter_name = '{0}_USERNAME'.format(configuration_parameter_name_prefix)

                if configuration[username_parameter_name] != previous_configuration[username_parameter_name]:
                    do_reinitialize = True
                    do_refresh_session = True

                    if message_to_log:
                        message_to_log.append('')

                    message_to_log.append(
                        'Detected a change in the username option in the [{0}] section\n'
                        'Old value => {1}\n'
                        'New value => {2}\n'
                        ''.format(section_name,
                                  previous_configuration[username_parameter_name],
                                  configuration[username_parameter_name]))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the PASSWORD option">
            if 'password' in cls._configuration_schema['Provider']:
                password_parameter_name = '{0}_PASSWORD'.format(configuration_parameter_name_prefix)

                if configuration[password_parameter_name] != previous_configuration[password_parameter_name]:
                    do_reinitialize = True
                    do_refresh_session = True

                    if message_to_log:
                        message_to_log.append('')

                    message_to_log.append(
                        'Detected a change in the password option in the [{0}] section\n'
                        'Old value => {1}\n'
                        'New value => {2}\n'
                        ''.format(section_name,
                                  SecurityManager.decrypt_password(
                                      previous_configuration[password_parameter_name]).decode(),
                                  SecurityManager.decrypt_password(configuration[password_parameter_name]).decode()))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the PLAYLIST_PROTOCOL option">
            if 'Playlist' in cls._configuration_schema and 'protocol' in cls._configuration_schema['Playlist']:
                playlist_protocol_parameter_name = '{0}_PLAYLIST_PROTOCOL'.format(configuration_parameter_name_prefix)

                if configuration[playlist_protocol_parameter_name] != \
                        previous_configuration[playlist_protocol_parameter_name]:
                    if message_to_log:
                        message_to_log.append('')

                    message_to_log.append(
                        'Detected a change in the protocol option in the [Playlist] section\n'
                        'Old value => {0}\n'
                        'New value => {1}\n'
                        ''.format(previous_configuration[playlist_protocol_parameter_name],
                                  configuration[playlist_protocol_parameter_name]))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the PLAYLIST_TYPE option">
            if 'Playlist' in cls._configuration_schema and 'type' in cls._configuration_schema['Playlist']:
                playlist_type_parameter_name = '{0}_PLAYLIST_TYPE'.format(configuration_parameter_name_prefix)

                if configuration[playlist_type_parameter_name] != previous_configuration[playlist_type_parameter_name]:
                    if message_to_log:
                        message_to_log.append('')

                    message_to_log.append(
                        'Detected a change in the type option in the [Playlist] section\n'
                        'Old value => {0}\n'
                        'New value => {1}\n'
                        ''.format(previous_configuration[playlist_type_parameter_name],
                                  configuration[playlist_type_parameter_name]))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the EPG_SOURCE option">
            if 'EPG' in cls._configuration_schema and 'source' in cls._configuration_schema['EPG']:
                epg_source_parameter_name = '{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)

                if configuration[epg_source_parameter_name] != previous_configuration[epg_source_parameter_name]:
                    do_reinitialize = True

                    if message_to_log:
                        message_to_log.append('')

                    message_to_log.append(
                        'Detected a change in the source option in the [EPG] section\n'
                        'Old value => {0}\n'
                        'New value => {1}\n'
                        ''.format(previous_configuration[epg_source_parameter_name],
                                  configuration[epg_source_parameter_name]))
            # </editor-fold>

            # <editor-fold desc="Detect and handle updates to the EPG_URL option">
            if 'EPG' in cls._configuration_schema and 'url' in cls._configuration_schema['EPG']:
                epg_source_parameter_name = '{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)
                epg_url_parameter_name = '{0}_EPG_URL'.format(configuration_parameter_name_prefix)

                if configuration[epg_source_parameter_name] == provider_map_class.epg_source_enum().OTHER.value:
                    if configuration[epg_url_parameter_name] != previous_configuration[epg_url_parameter_name]:
                        do_reinitialize = True

                        if message_to_log:
                            message_to_log.append('')

                        message_to_log.append(
                            'Detected a change in the url option in the [EPG] section\n'
                            'Old value => {0}\n'
                            'New value => {1}\n'
                            ''.format(
                                previous_configuration[
                                    epg_url_parameter_name] if previous_configuration[
                                                                   epg_url_parameter_name] is not None
                                else 'N/A',
                                configuration[epg_url_parameter_name]))
            # </editor-fold>

            if message_to_log:
                if do_reinitialize:
                    message_to_log.append('Action => Reinitializing {0}'.format(section_name))
                else:
                    message_to_log.append('Action => N/A')

                logger.debug('\n'.join(message_to_log))

                if do_reinitialize:
                    ProvidersController.initialize_provider(cls._provider_name, do_refresh_session=do_refresh_session)
            else:
                logger.debug('No changes detected in the {0} section'.format(section_name))
        elif provider_in_configuration and not provider_in_previous_configuration:
            logger.debug('Detected the addition of the {0} section'.format(section_name))

            ProvidersController.initialize_provider(cls._provider_name)
        elif not provider_in_configuration and provider_in_previous_configuration:
            logger.debug('Detected the removal of the {0} section'.format(section_name))

            ProvidersController.terminate_provider(cls._provider_name)

    @classmethod
    def read_configuration_file(cls,
                                configuration_object,
                                configuration,
                                providers,
                                message_to_log,
                                error_message_to_log):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        section_name = provider_map_class.api_class().__name__
        configuration_parameter_name_prefix = section_name.upper()

        is_valid_section = True
        section_found = True

        last_error_message_index = len(error_message_to_log)

        service = None
        server = None
        username = None
        password = None
        playlist_protocol = None
        playlist_type = None
        epg_source = None
        epg_url = None

        try:
            provider_section = configuration_object[section_name]

            if 'service' in cls._configuration_schema['Provider']:
                try:
                    service = provider_section['service'].lower()

                    if not provider_map_class.validations_class().is_valid_service(service):
                        is_valid_section = False

                        error_message_to_log.append(
                            'The service option in the [{0}] section must be one of\n'
                            '{1}\n'.format(
                                section_name,
                                '\n'.join(['\u2022 {0}'.format(service)
                                           for service in provider_map_class.constants_class().VALID_SERVICE_VALUES])))
                except KeyError:
                    is_valid_section = False

                    error_message_to_log.append(
                        'Could not find a service option in the [{0}] section\n'
                        'The service option in the [{0}] section must be one of\n'
                        '{1}\n'.format(
                            section_name,
                            '\n'.join(['\u2022 {0}'.format(service)
                                       for service in provider_map_class.constants_class().VALID_SERVICE_VALUES])))

            if 'server' in cls._configuration_schema['Provider']:
                try:
                    server = provider_section['server'].lower()

                    if not provider_map_class.validations_class().is_valid_server(server):
                        is_valid_section = False

                        error_message_to_log.append(
                            'The server option in the [{0}] section must be one of\n'
                            '{1}\n'.format(
                                section_name,
                                '\n'.join(['\u2022 {0}'.format(server)
                                           for server in provider_map_class.constants_class().VALID_SERVER_VALUES])))
                except KeyError:
                    is_valid_section = False

                    error_message_to_log.append(
                        'Could not find a server option in the [{0}] section\n'
                        'The server option in the [{0}] section must be one of\n{1}\n'.format(
                            section_name,
                            '\n'.join(['\u2022 {0}'.format(server)
                                       for server in provider_map_class.constants_class().VALID_SERVER_VALUES])))

            if 'username' in cls._configuration_schema['Provider']:
                try:
                    username = provider_section['username']
                except KeyError:
                    is_valid_section = False

                    error_message_to_log.append('Could not find a username option in the [{0}] section\n').format(
                        section_name)

            if 'password' in cls._configuration_schema['Provider']:
                try:
                    password = provider_section['password']
                except KeyError:
                    is_valid_section = False

                    error_message_to_log.append('Could not find a password option in the [{0}] section\n').format(
                        section_name)

            if 'Playlist' in cls._configuration_schema:
                try:
                    playlist_section = provider_section['Playlist']

                    if 'protocol' in cls._configuration_schema['Playlist']:
                        playlist_protocol = provider_map_class.constants_class().DEFAULT_PLAYLIST_PROTOCOL

                        try:
                            playlist_protocol = playlist_section['protocol'].lower()

                            if not provider_map_class.validations_class().is_valid_playlist_protocol(playlist_protocol):
                                playlist_protocol = provider_map_class.constants_class().DEFAULT_PLAYLIST_PROTOCOL

                                error_message_to_log.append(
                                    'The protocol option in the [Playlist] section must be one of\n'
                                    '{0}Defaulting to {1}\n'.format(
                                        '\n'.join([
                                            '\u2022 {0}'.format(protocol)
                                            for protocol in
                                            provider_map_class.constants_class().VALID_PLAYLIST_PROTOCOL_VALUES]),
                                        playlist_protocol))
                        except KeyError:
                            error_message_to_log.append(
                                'Could not find a protocol option in the [Playlist] section\n'
                                'The protocol option in the [Playlist] section must be one of\n{0}\n'
                                'Defaulting to {1}\n'.format(
                                    '\n'.join(['\u2022 {0}'.format(protocol)
                                               for protocol in
                                               provider_map_class.constants_class().VALID_PLAYLIST_PROTOCOL_VALUES]),
                                    playlist_protocol))

                    if 'type' in cls._configuration_schema['Playlist']:
                        playlist_type = provider_map_class.constants_class().DEFAULT_PLAYLIST_TYPE

                        try:
                            playlist_type = playlist_section['type'].lower()

                            if not provider_map_class.validations_class().is_valid_playlist_type(playlist_type):
                                playlist_type = provider_map_class.constants_class().DEFAULT_PLAYLIST_TYPE

                                error_message_to_log.append(
                                    'The type option in the [Playlist] section must be one of\n'
                                    '{0}Defaulting to {1}\n'.format(
                                        '\n'.join(['\u2022 {0}'.format(type_)
                                                   for type_ in
                                                   provider_map_class.constants_class().VALID_PLAYLIST_TYPE_VALUES]),
                                        playlist_type))
                        except KeyError:
                            error_message_to_log.append(
                                'Could not find a type option in the [Playlist] section\n'
                                'The type option in the [Playlist] section must be one of\n{0}\n'
                                'Defaulting to {1}\n'.format(
                                    '\n'.join([
                                        '\u2022 {0}'.format(type_)
                                        for type_ in provider_map_class.constants_class().VALID_PLAYLIST_TYPE_VALUES]),
                                    playlist_type))
                except KeyError:
                    error_message_to_log.append('Could not find a [Playlist] section\n'
                                                'Defaulting the protocol option to {0}\n'
                                                'Defaulting the type option to {1}\n'.format(playlist_protocol,
                                                                                             playlist_type))

            if 'EPG' in cls._configuration_schema:
                try:
                    epg_section = provider_section['EPG']

                    if 'source' in cls._configuration_schema['EPG']:
                        epg_source = provider_map_class.constants_class().DEFAULT_EPG_SOURCE

                        try:
                            epg_source = epg_section['source'].lower()

                            if not provider_map_class.validations_class().is_valid_epg_source(epg_source):
                                epg_source = provider_map_class.constants_class().DEFAULT_EPG_SOURCE

                                error_message_to_log.append(
                                    'The source option in the [EPG] section must be one of\n'
                                    '{0}\n'
                                    'Defaulting to {1}\n'.format(
                                        '\n'.join(['\u2022 {0}'.format(source)
                                                   for source in
                                                   provider_map_class.constants_class().VALID_EPG_SOURCE_VALUES]),
                                        epg_source))
                        except KeyError:
                            error_message_to_log.append(
                                'Could not find a source option in the [EPG] section\n'
                                'The source option in the [EPG] section must be one of\n'
                                '{0}\n'
                                'Defaulting to {1}\n'.format(
                                    '\n'.join(['\u2022 {0}'.format(source)
                                               for source in
                                               provider_map_class.constants_class().VALID_EPG_SOURCE_VALUES]),
                                    epg_source))

                    if 'url' in cls._configuration_schema['EPG']:
                        try:
                            epg_url = epg_section['url']

                            if epg_source == provider_map_class.epg_source_enum().OTHER.value and not \
                                    provider_map_class.validations_class().is_valid_epg_url(epg_url):
                                error_message_to_log.append(
                                    'Could not find a url option in the [EPG] section\n'
                                    'The url option in the [EPG] section must be a valid url to a XMLTV file')
                        except KeyError:
                            if epg_source == provider_map_class.epg_source_enum().OTHER.value:
                                error_message_to_log.append(
                                    'Could not find a url option in the [EPG] section\n'
                                    'The url option in the [EPG] section must be a valid url to a XMLTV file')
                except KeyError:
                    error_message_to_log.append('Could not find an [EPG] section\n'
                                                'Defaulting the source option to {0}\n'.format(epg_source))
        except KeyError:
            is_valid_section = False
            section_found = False

            error_message_to_log.append('Could not find a [{0}] section\n'.format(section_name))

        if is_valid_section:
            providers.append(cls._provider_name)

            if 'service' in cls._configuration_schema['Provider']:
                configuration['{0}_SERVICE'.format(configuration_parameter_name_prefix)] = service

            if 'server' in cls._configuration_schema['Provider']:
                configuration['{0}_SERVER'.format(configuration_parameter_name_prefix)] = server

            if 'username' in cls._configuration_schema['Provider']:
                configuration['{0}_USERNAME'.format(configuration_parameter_name_prefix)] = username

            if 'password' in cls._configuration_schema['Provider']:
                configuration['{0}_PASSWORD'.format(configuration_parameter_name_prefix)] = password

            if 'Playlist' in cls._configuration_schema and 'protocol' in cls._configuration_schema['Playlist']:
                configuration['{0}_PLAYLIST_PROTOCOL'.format(configuration_parameter_name_prefix)] = playlist_protocol

            if 'Playlist' in cls._configuration_schema and 'type' in cls._configuration_schema['Playlist']:
                configuration['{0}_PLAYLIST_TYPE'.format(configuration_parameter_name_prefix)] = playlist_type

            if 'EPG' in cls._configuration_schema and 'source' in cls._configuration_schema['EPG']:
                configuration['{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)] = epg_source

            if 'EPG' in cls._configuration_schema and 'url' in cls._configuration_schema['EPG']:
                configuration['{0}_EPG_URL'.format(configuration_parameter_name_prefix)] = epg_url

            message_to_log.append(
                '\n'
                '{0}'
                '{1}'
                '{2}'
                '{3}'
                '{4}'
                '{5}'
                '{6}'
                '{7}'.format(
                    '{0}_SERVICE           => {1}\n'.format(configuration_parameter_name_prefix,
                                                            service) if service is not None
                    else '',
                    '{0}_SERVER            => {1}\n'.format(configuration_parameter_name_prefix,
                                                            server) if server is not None
                    else '',
                    '{0}_USERNAME          => {1}\n'.format(configuration_parameter_name_prefix,
                                                            username) if username is not None
                    else '',
                    '{0}_PASSWORD          => {1}\n'.format(configuration_parameter_name_prefix,
                                                            password if SecurityManager.is_password_decrypted(password)
                                                            else SecurityManager.decrypt_password(password).decode())
                    if password is not None
                    else '',
                    '{0}_PLAYLIST_PROTOCOL => {1}\n'.format(configuration_parameter_name_prefix,
                                                            playlist_protocol) if playlist_protocol is not None
                    else '',
                    '{0}_PLAYLIST_TYPE     => {1}\n'.format(configuration_parameter_name_prefix,
                                                            playlist_type) if playlist_type is not None
                    else '',
                    '{0}_EPG_SOURCE        => {1}'.format(configuration_parameter_name_prefix,
                                                          epg_source) if epg_source is not None
                    else '',
                    '\n'
                    '{0}_EPG_URL           => {1}'.format(configuration_parameter_name_prefix,
                                                          epg_url) if epg_url is not None
                    else ''))

            if 'password' in cls._configuration_schema['Provider']:
                cls._scrub_password(configuration_object, configuration)
        else:
            if section_found:
                error_message_to_log.insert(last_error_message_index,
                                            'Ignoring the [{0}] section due to invalid values\n'.format(section_name))

    @classmethod
    def validate_update_configuration_request(cls, configuration, errors):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        section_name = provider_map_class.api_class().__name__
        configuration_parameter_name_prefix = section_name.upper()
        errors_parameter_name_prefix = '{0}{1}'.format(section_name[0].lower(), section_name[1:])

        provider_in_configuration = True if len(
            [parameter_name for parameter_name in configuration
             if parameter_name.startswith(configuration_parameter_name_prefix)]) else False

        if provider_in_configuration:
            if 'service' in cls._configuration_schema['Provider']:
                try:
                    if not provider_map_class.validations_class().is_valid_service(
                            configuration['{0}_SERVICE'.format(configuration_parameter_name_prefix)]):
                        errors['{0}Service'.format(errors_parameter_name_prefix)] = 'Must be one of [{0}]'.format(
                            ', '.join(['\'{0}\''.format(service)
                                       for service in provider_map_class.constants_class().VALID_SERVICE_VALUES]))
                except KeyError:
                    errors['{0}Service'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'server' in cls._configuration_schema['Provider']:
                try:
                    if not provider_map_class.validations_class().is_valid_server(
                            configuration['{0}_SERVER'.format(configuration_parameter_name_prefix)]):
                        errors['{0}Server'.format(errors_parameter_name_prefix)] = 'Must be one of [{0}]'.format(
                            ', '.join(['\'{0}\''.format(server)
                                       for server in provider_map_class.constants_class().VALID_SERVER_VALUES]))
                except KeyError:
                    errors['{0}Server'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'username' in cls._configuration_schema['Provider']:
                try:
                    if not provider_map_class.validations_class().is_valid_username(
                            configuration['{0}_USERNAME'.format(configuration_parameter_name_prefix)]):
                        errors['{0}Username'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'
                except KeyError:
                    errors['{0}Username'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'password' in cls._configuration_schema['Provider']:
                try:
                    if not provider_map_class.validations_class().is_valid_password(
                            configuration['{0}_PASSWORD'.format(configuration_parameter_name_prefix)]):
                        errors['{0}Password'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'
                except KeyError:
                    errors['{0}Password'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'Playlist' in cls._configuration_schema and 'protocol' in cls._configuration_schema['Playlist']:
                try:
                    if not provider_map_class.validations_class().is_valid_playlist_protocol(
                            configuration['{0}_PLAYLIST_PROTOCOL'.format(configuration_parameter_name_prefix)]):
                        errors[
                            '{0}PlaylistProtocol'.format(errors_parameter_name_prefix)] = 'Must be one of [{0}]'.format(
                            ', '.join(['\'{0}\''.format(service) for service in
                                       provider_map_class.constants_class().VALID_PLAYLIST_PROTOCOL_VALUES]))
                except KeyError:
                    errors['{0}PlaylistProtocol'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'Playlist' in cls._configuration_schema and 'type' in cls._configuration_schema['Playlist']:
                try:
                    if not provider_map_class.validations_class().is_valid_playlist_type(
                            configuration['{0}_PLAYLIST_TYPE'.format(configuration_parameter_name_prefix)]):
                        errors['{0}PlaylistType'.format(errors_parameter_name_prefix)] = 'Must be one of [{0}]'.format(
                            ', '.join(['\'{0}\''.format(service)
                                       for service in provider_map_class.constants_class().VALID_PLAYLIST_TYPE_VALUES]))
                except KeyError:
                    errors['{0}PlaylistType'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'EPG' in cls._configuration_schema and 'source' in cls._configuration_schema['EPG']:
                try:
                    if not provider_map_class.validations_class().is_valid_epg_source(
                            configuration['{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)]):
                        errors['{0}EpgSource'.format(errors_parameter_name_prefix)] = 'Must be one of [{0}]'.format(
                            ', '.join(['\'{0}\''.format(service)
                                       for service in provider_map_class.constants_class().VALID_EPG_SOURCE_VALUES]))
                except KeyError:
                    errors['{0}EpgSource'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'

            if 'EPG' in cls._configuration_schema and 'url' in cls._configuration_schema['EPG']:
                try:
                    if '{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix) in configuration and \
                            configuration['{0}_EPG_SOURCE'.format(configuration_parameter_name_prefix)] == \
                            provider_map_class.epg_source_enum().OTHER.value and not \
                            provider_map_class.validations_class().is_valid_epg_url(
                                configuration['{0}_EPG_URL'.format(configuration_parameter_name_prefix)]):
                        errors['{0}EpgUrl'.format(errors_parameter_name_prefix)] = 'Must be a valid url to a XMLTV file'
                except KeyError:
                    errors['{0}EpgUrl'.format(errors_parameter_name_prefix)] = 'Must not be an empty value'


class ProviderOptionalSettings(object):
    __slots__ = []

    _provider_name = None

    @classmethod
    def process_optional_settings_file_updates(cls, optional_settings, previous_optional_settings):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        message_to_log = []

        do_reinitialize = False

        # <editor-fold desc="Detect and handle reduce_delay change">
        if provider_map_class.api_class().is_attribute_supported('_do_reduce_hls_stream_delay'):
            reduce_delay_key_name = 'reduce_{0}_delay'.format(cls._provider_name)

            if reduce_delay_key_name not in optional_settings:
                optional_settings[reduce_delay_key_name] = True

            if reduce_delay_key_name not in previous_optional_settings:
                previous_optional_settings[reduce_delay_key_name] = True

            if optional_settings[reduce_delay_key_name] != previous_optional_settings[reduce_delay_key_name]:
                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(reduce_delay_key_name,
                                                json.dumps(previous_optional_settings[reduce_delay_key_name],
                                                           indent=2),
                                                json.dumps(optional_settings[reduce_delay_key_name],
                                                           indent=2)))

                provider_map_class.api_class().set_do_reduce_hls_stream_delay(optional_settings[reduce_delay_key_name])
        # </editor-fold>

        # <editor-fold desc="Detect and handle channel_group_map change">
        if provider_map_class.epg_class().is_attribute_supported('_channel_group_map'):
            channel_group_map_key_name = '{0}_channel_group_map'.format(cls._provider_name)

            if channel_group_map_key_name not in optional_settings:
                optional_settings[channel_group_map_key_name] = {'name': {}, 'number': {}}

            if channel_group_map_key_name not in previous_optional_settings:
                previous_optional_settings[channel_group_map_key_name] = {'name': {}, 'number': {}}

            if optional_settings[channel_group_map_key_name] != previous_optional_settings[channel_group_map_key_name]:
                do_reinitialize = True

                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(channel_group_map_key_name,
                                                json.dumps(
                                                    previous_optional_settings[channel_group_map_key_name],
                                                    indent=2),
                                                json.dumps(optional_settings[channel_group_map_key_name],
                                                           indent=2)))

                provider_map_class.epg_class().set_channel_group_map(
                    optional_settings[channel_group_map_key_name])
        # </editor-fold>

        # <editor-fold desc="Detect and handle channel_name_map change">
        if provider_map_class.epg_class().is_attribute_supported('_channel_name_map'):
            channel_name_map_key_name = '{0}_channel_name_map'.format(cls._provider_name)

            if channel_name_map_key_name not in optional_settings:
                optional_settings[channel_name_map_key_name] = {}

            if channel_name_map_key_name not in previous_optional_settings:
                previous_optional_settings[channel_name_map_key_name] = {}

            if optional_settings[channel_name_map_key_name] != previous_optional_settings[channel_name_map_key_name]:
                do_reinitialize = True

                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(channel_name_map_key_name,
                                                json.dumps(previous_optional_settings[channel_name_map_key_name],
                                                           indent=2),
                                                json.dumps(optional_settings[channel_name_map_key_name],
                                                           indent=2)))

                provider_map_class.epg_class().set_channel_name_map(optional_settings[channel_name_map_key_name])
        # </editor-fold>

        # <editor-fold desc="Detect and handle use_icons change">
        if provider_map_class.epg_class().is_attribute_supported('_do_use_provider_icons'):
            ignored_m3u8_groups_key_name = 'use_{0}_icons'.format(cls._provider_name)

            if ignored_m3u8_groups_key_name not in optional_settings:
                optional_settings[ignored_m3u8_groups_key_name] = False

            if ignored_m3u8_groups_key_name not in previous_optional_settings:
                previous_optional_settings[ignored_m3u8_groups_key_name] = False

            if optional_settings[ignored_m3u8_groups_key_name] != \
                    previous_optional_settings[ignored_m3u8_groups_key_name]:
                do_reinitialize = True

                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(ignored_m3u8_groups_key_name,
                                                json.dumps(previous_optional_settings[ignored_m3u8_groups_key_name],
                                                           indent=2),
                                                json.dumps(optional_settings[ignored_m3u8_groups_key_name],
                                                           indent=2)))

                provider_map_class.epg_class().set_do_use_provider_icons(
                    optional_settings[ignored_m3u8_groups_key_name])
        # </editor-fold>

        # <editor-fold desc="Detect and handle ignored_channels change">
        if provider_map_class.epg_class().is_attribute_supported('_ignored_channels'):
            ignored_m3u8_groups_key_name = '{0}_ignored_channels'.format(cls._provider_name)

            if ignored_m3u8_groups_key_name not in optional_settings:
                optional_settings[ignored_m3u8_groups_key_name] = {'name': {}, 'number': {}}

            if ignored_m3u8_groups_key_name not in previous_optional_settings:
                previous_optional_settings[ignored_m3u8_groups_key_name] = {'name': {}, 'number': {}}

            if optional_settings[ignored_m3u8_groups_key_name] != \
                    previous_optional_settings[ignored_m3u8_groups_key_name]:
                do_reinitialize = True

                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(ignored_m3u8_groups_key_name,
                                                json.dumps(previous_optional_settings[ignored_m3u8_groups_key_name],
                                                           indent=2),
                                                json.dumps(optional_settings[ignored_m3u8_groups_key_name],
                                                           indent=2)))

                provider_map_class.epg_class().set_ignored_channels(optional_settings[ignored_m3u8_groups_key_name])
        # </editor-fold>

        # <editor-fold desc="Detect and handle ignored_m3u8_groups change">
        if provider_map_class.epg_class().is_attribute_supported('_ignored_m3u8_groups'):
            ignored_m3u8_groups_key_name = '{0}_ignored_m3u8_groups'.format(cls._provider_name)

            if ignored_m3u8_groups_key_name not in optional_settings:
                optional_settings[ignored_m3u8_groups_key_name] = []

            if ignored_m3u8_groups_key_name not in previous_optional_settings:
                previous_optional_settings[ignored_m3u8_groups_key_name] = []

            if optional_settings[ignored_m3u8_groups_key_name] != \
                    previous_optional_settings[ignored_m3u8_groups_key_name]:
                do_reinitialize = True

                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(ignored_m3u8_groups_key_name,
                                                json.dumps(
                                                    previous_optional_settings[ignored_m3u8_groups_key_name],
                                                    indent=2),
                                                json.dumps(optional_settings[ignored_m3u8_groups_key_name],
                                                           indent=2)))

                provider_map_class.epg_class().set_ignored_channels(
                    optional_settings[ignored_m3u8_groups_key_name])
        # </editor-fold>

        # <editor-fold desc="Detect and handle m3u8_group_map change">
        if provider_map_class.epg_class().is_attribute_supported('_m3u8_group_map'):
            m3u8_group_map_key_name = '{0}_m3u8_group_map'.format(cls._provider_name)

            if m3u8_group_map_key_name not in optional_settings:
                optional_settings[m3u8_group_map_key_name] = {}

            if m3u8_group_map_key_name not in previous_optional_settings:
                previous_optional_settings[m3u8_group_map_key_name] = {}

            if optional_settings[m3u8_group_map_key_name] != previous_optional_settings[m3u8_group_map_key_name]:
                do_reinitialize = True

                message_to_log.append(
                    'Detected a change in the {0} setting\n'
                    'Old value => {1}\n'
                    'New value => {2}\n'.format(m3u8_group_map_key_name,
                                                json.dumps(
                                                    previous_optional_settings[m3u8_group_map_key_name],
                                                    indent=2),
                                                json.dumps(optional_settings[m3u8_group_map_key_name],
                                                           indent=2)))

                provider_map_class.epg_class().set_ignored_channels(
                    optional_settings[m3u8_group_map_key_name])
        # </editor-fold>

        if message_to_log:
            if do_reinitialize and cls._provider_name in ProvidersController.get_active_providers():
                message_to_log.append('Action => Reinitializing {0}'.format(provider_map_class.api_class.__name__))
            else:
                message_to_log.append('Action => N/A')

            logger.debug('\n'.join(message_to_log))

            if do_reinitialize and cls._provider_name in ProvidersController.get_active_providers():
                ProvidersController.initialize_provider(cls._provider_name)
