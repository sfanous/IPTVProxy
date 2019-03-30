import logging

from .constants import DEFAULT_VADER_STREAMS_PLAYLIST_PROTOCOL
from .constants import DEFAULT_VADER_STREAMS_PLAYLIST_TYPE
from .constants import VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES
from .constants import VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES
from .constants import VALID_VADER_STREAMS_SERVER_VALUES
from .validations import VaderStreamsValidations

logger = logging.getLogger(__name__)


class VaderStreamsConfiguration(object):
    __slots__ = []

    @classmethod
    def create_section(cls, configuration):
        configuration_section = None

        if configuration['VADER_STREAMS_SERVER'] and configuration['VADER_STREAMS_USERNAME'] and \
                configuration['VADER_STREAMS_PASSWORD'] and configuration['VADER_STREAMS_PLAYLIST_PROTOCOL'] and \
                configuration['VADER_STREAMS_PLAYLIST_TYPE']:
            configuration_section = {
                'server': configuration['VADER_STREAMS_SERVER'],
                'username': configuration['VADER_STREAMS_USERNAME'],
                'password': configuration['VADER_STREAMS_PASSWORD'],
                'Playlist': {
                    'protocol': configuration['VADER_STREAMS_PLAYLIST_PROTOCOL'],
                    'type': configuration['VADER_STREAMS_PLAYLIST_TYPE']
                }
            }

        return configuration_section

    @classmethod
    def process_configuration_file_updates(cls, configuration, previous_configuration):
        # <editor-fold desc="Detect and handle updates to the VADER_STREAMS_PASSWORD option">
        if configuration['VADER_STREAMS_PASSWORD'] != previous_configuration['VADER_STREAMS_PASSWORD']:
            # Disable the configuration file watchdog to avoid processing of the event that results from scrubbing the
            # password in the configuration file
            from ...configuration import IPTVProxyConfiguration
            from ...security import IPTVProxySecurityManager

            IPTVProxyConfiguration.stop_configuration_file_watchdog_observer()
            encrypted_password = IPTVProxySecurityManager.scrub_password('VaderStreams',
                                                                         configuration['VADER_STREAMS_PASSWORD'])

            if configuration['VADER_STREAMS_PASSWORD'] != encrypted_password:
                IPTVProxyConfiguration.update_configuration_file('VaderStreams', 'password', encrypted_password)
                IPTVProxyConfiguration.set_configuration_parameter('VADER_STREAMS_PASSWORD', encrypted_password)

            IPTVProxyConfiguration.start_configuration_file_watchdog_observer()

            logger.debug('Detected a change in the password option within the [VaderStreams] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Refreshing the authorization hash'
                         ''.format(previous_configuration['VADER_STREAMS_PASSWORD'],
                                   configuration['VADER_STREAMS_PASSWORD']))
        # </editor-fold>

    @classmethod
    def read_configuration_file(cls, configuration_object, error_messages):
        is_valid_section = True
        section_found = True

        last_error_message_index = len(error_messages)

        server = None
        username = None
        password = None
        playlist_protocol = DEFAULT_VADER_STREAMS_PLAYLIST_PROTOCOL
        playlist_type = DEFAULT_VADER_STREAMS_PLAYLIST_TYPE

        try:
            vader_streams_section = configuration_object['VaderStreams']

            try:
                server = vader_streams_section['server'].lower()
                if not VaderStreamsValidations.is_valid_server(server):
                    is_valid_section = False

                    error_messages.append(
                        'The server option within the [VaderStreams] section must be one of\n'
                        '{0}\n'.format('\n'.join(['\u2022 {0}'.format(server)
                                                  for server in VALID_VADER_STREAMS_SERVER_VALUES])))
            except KeyError:
                is_valid_section = False

                error_messages.append(
                    'Could not find a server option within the [VaderStreams] section\n'
                    'The server option within the [VaderStreams] section must be one of\n{0}\n'.format(
                        '\n'.join(['\u2022 {0}'.format(server) for server in VALID_VADER_STREAMS_SERVER_VALUES])))

            try:
                username = vader_streams_section['username']
            except KeyError:
                is_valid_section = False

                error_messages.append('Could not find a username option within the [VaderStreams] section\n')

            try:
                password = vader_streams_section['password']
            except KeyError:
                is_valid_section = False

                error_messages.append('Could not find a password option within the [VaderStreams] section\n')

            try:
                playlist_section = vader_streams_section['Playlist']

                try:
                    playlist_protocol = playlist_section['protocol'].lower()
                    if not VaderStreamsValidations.is_valid_playlist_protocol(playlist_protocol):
                        playlist_protocol = DEFAULT_VADER_STREAMS_PLAYLIST_PROTOCOL

                        error_messages.append(
                            'The protocol option within the [Playlist] section must be one of\n'
                            '{0}Defaulting to {1}\n'.format(
                                '\n'.join(['\u2022 {0}'.format(protocol)
                                           for protocol in VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES]),
                                playlist_protocol))
                except KeyError:
                    error_messages.append(
                        'Could not find a protocol option within the [Playlist] section\n'
                        'The protocol option within the [Playlist] section must be one of\n{0}\n'
                        'Defaulting to {1}\n'.format(
                            '\n'.join(['\u2022 {0}'.format(protocol)
                                       for protocol in VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES]),
                            playlist_protocol))

                try:
                    playlist_type = playlist_section['type'].lower()
                    if not VaderStreamsValidations.is_valid_playlist_type(playlist_type):
                        playlist_type = DEFAULT_VADER_STREAMS_PLAYLIST_TYPE

                        error_messages.append(
                            'The type option within the [Playlist] section must be one of\n'
                            '{0}Defaulting to {1}\n'.format(
                                '\n'.join(['\u2022 {0}'.format(type_)
                                           for type_ in VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES]),
                                playlist_type))
                except KeyError:
                    error_messages.append(
                        'Could not find a type option within the [Playlist] section\n'
                        'The type option within the [Playlist] section must be one of\n{0}\n'
                        'Defaulting to {1}\n'.format(
                            '\n'.join(['\u2022 {0}'.format(type_)
                                       for type_ in VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES]),
                            playlist_type))
            except KeyError:
                error_messages.append('Could not find a [Playlist] section\n'
                                      'Defaulting the protocol option to {0}\n'
                                      'Defaulting the type option to {1}\n'.format(playlist_protocol,
                                                                                   playlist_type))
        except KeyError:
            is_valid_section = False

            error_messages.append('Could not find a [VaderStreams] section\n')

        if not is_valid_section and section_found:
            error_messages.insert(last_error_message_index,
                                  'Ignoring the [VaderStreams] section due to invalid values\n')

        return (is_valid_section,
                server,
                username,
                password,
                playlist_protocol,
                playlist_type)

    @classmethod
    def validate_update_configuration_request(cls, configuration, errors):
        if configuration['VADER_STREAMS_SERVER'] or configuration['VADER_STREAMS_USERNAME'] or \
                configuration['VADER_STREAMS_PASSWORD'] or configuration['VADER_STREAMS_PLAYLIST_PROTOCOL'] or \
                configuration['VADER_STREAMS_PLAYLIST_TYPE']:
            if configuration['VADER_STREAMS_SERVER'] and not \
                    VaderStreamsValidations.is_valid_server(configuration['VADER_STREAMS_SERVER']):
                errors['vaderStreamsServer'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(server) for server in VALID_VADER_STREAMS_SERVER_VALUES]))

            if configuration['VADER_STREAMS_USERNAME'] and not \
                    VaderStreamsValidations.is_valid_username(configuration['VADER_STREAMS_USERNAME']):
                errors['vaderStreamsUsername'] = 'Must not be an empty value'

            if configuration['VADER_STREAMS_PASSWORD'] and not \
                    VaderStreamsValidations.is_valid_password(configuration['VADER_STREAMS_PASSWORD']):
                errors['vaderStreamsPassword'] = 'Must not be an empty value'

            if configuration['VADER_STREAMS_PLAYLIST_PROTOCOL'] and not \
                    VaderStreamsValidations.is_valid_playlist_protocol(
                        configuration['VADER_STREAMS_PLAYLIST_PROTOCOL']):
                errors['vaderStreamsPlaylistProtocol'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(service) for service in VALID_VADER_STREAMS_PLAYLIST_PROTOCOL_VALUES]))

            if configuration['VADER_STREAMS_PLAYLIST_TYPE'] and not \
                    VaderStreamsValidations.is_valid_playlist_type(configuration['VADER_STREAMS_PLAYLIST_TYPE']):
                errors['vaderStreamsPlaylistType'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(service) for service in VALID_VADER_STREAMS_PLAYLIST_TYPE_VALUES]))
