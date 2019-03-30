import logging

import requests

from .constants import DEFAULT_SMOOTH_STREAMS_EPG_SOURCE
from .constants import DEFAULT_SMOOTH_STREAMS_PLAYLIST_PROTOCOL
from .constants import DEFAULT_SMOOTH_STREAMS_PLAYLIST_TYPE
from .constants import VALID_SMOOTH_STREAMS_EPG_SOURCE_VALUES
from .constants import VALID_SMOOTH_STREAMS_PLAYLIST_PROTOCOL_VALUES
from .constants import VALID_SMOOTH_STREAMS_PLAYLIST_TYPE_VALUES
from .constants import VALID_SMOOTH_STREAMS_SERVER_VALUES
from .constants import VALID_SMOOTH_STREAMS_SERVICE_VALUES
from .validations import SmoothStreamsValidations

logger = logging.getLogger(__name__)


class SmoothStreamsConfiguration(object):
    __slots__ = []

    @classmethod
    def create_section(cls, configuration):
        configuration_section = None

        if configuration['SMOOTH_STREAMS_SERVICE'] and configuration['SMOOTH_STREAMS_SERVER'] and \
                configuration['SMOOTH_STREAMS_USERNAME'] and configuration['SMOOTH_STREAMS_PASSWORD'] and \
                configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL'] and \
                configuration['SMOOTH_STREAMS_PLAYLIST_TYPE'] and configuration['SMOOTH_STREAMS_EPG_SOURCE'] and \
                (configuration['SMOOTH_STREAMS_EPG_SOURCE'] != 'other' or configuration['SMOOTH_STREAMS_EPG_URL']):
            configuration_section = {
                'service': configuration['SMOOTH_STREAMS_SERVICE'],
                'server': configuration['SMOOTH_STREAMS_SERVER'],
                'username': configuration['SMOOTH_STREAMS_USERNAME'],
                'password': configuration['SMOOTH_STREAMS_PASSWORD'],
                'Playlist': {
                    'protocol': configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL'],
                    'type': configuration['SMOOTH_STREAMS_PLAYLIST_TYPE']
                },
                'EPG': {
                    'source': configuration['SMOOTH_STREAMS_EPG_SOURCE'],
                    'url': configuration['SMOOTH_STREAMS_EPG_URL']
                }
            }

        return configuration_section

    @classmethod
    def process_configuration_file_updates(cls, configuration, previous_configuration):
        refresh_session = False
        reset_epg = False

        # <editor-fold desc="Detect and handle updates to the SMOOTH_STREAMS_SERVICE option">
        if configuration['SMOOTH_STREAMS_SERVICE'] != previous_configuration['SMOOTH_STREAMS_SERVICE']:
            refresh_session = True

            logger.debug('Detected a change in the service option within the [SmoothStreams] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Refreshing the authorization hash'
                         ''.format(previous_configuration['SMOOTH_STREAMS_SERVICE'],
                                   configuration['SMOOTH_STREAMS_SERVICE']))
        # </editor-fold>

        # <editor-fold desc="Detect and handle updates to the SMOOTH_STREAMS_PASSWORD option">
        if configuration['SMOOTH_STREAMS_PASSWORD'] != previous_configuration['SMOOTH_STREAMS_PASSWORD']:
            # Disable the configuration file watchdog to avoid processing of the event that results from scrubbing the
            # password in the configuration file
            from ...configuration import IPTVProxyConfiguration
            from ...security import IPTVProxySecurityManager

            IPTVProxyConfiguration.stop_configuration_file_watchdog_observer()
            encrypted_password = IPTVProxySecurityManager.scrub_password('SmoothStreams',
                                                                         configuration['SMOOTH_STREAMS_PASSWORD'])

            if configuration['SMOOTH_STREAMS_PASSWORD'] != encrypted_password:
                IPTVProxyConfiguration.update_configuration_file('SmoothStreams', 'password', encrypted_password)
                IPTVProxyConfiguration.set_configuration_parameter('SMOOTH_STREAMS_PASSWORD', encrypted_password)

            IPTVProxyConfiguration.start_configuration_file_watchdog_observer()

            refresh_session = True

            logger.debug('Detected a change in the password option within the [SmoothStreams] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Refreshing the authorization hash'
                         ''.format(previous_configuration['SMOOTH_STREAMS_PASSWORD'],
                                   configuration['SMOOTH_STREAMS_PASSWORD']))
        # </editor-fold>

        # <editor-fold desc="Detect and handle updates to the SMOOTH_STREAMS_USERNAME option">
        if configuration['SMOOTH_STREAMS_USERNAME'] != previous_configuration['SMOOTH_STREAMS_USERNAME']:
            refresh_session = True

            logger.debug('Detected a change in the username option within the [SmoothStreams] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Refreshing the authorization hash'
                         ''.format(previous_configuration['SMOOTH_STREAMS_USERNAME'],
                                   configuration['SMOOTH_STREAMS_USERNAME']))
        # </editor-fold>

        if refresh_session:
            from .api import SmoothStreams

            try:
                SmoothStreams.refresh_session(force_refresh=True)
            except requests.exceptions.HTTPError:
                pass

        # <editor-fold desc="Detect and handle updates to the SMOOTH_STREAMS_EPG_SOURCE option">
        if configuration['SMOOTH_STREAMS_EPG_SOURCE'] != previous_configuration['SMOOTH_STREAMS_EPG_SOURCE']:
            reset_epg = True

            logger.debug('Detected a change in the source option within the [EPG] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Resetting the EPG'.format(previous_configuration['SMOOTH_STREAMS_EPG_SOURCE'],
                                                    configuration['SMOOTH_STREAMS_EPG_SOURCE']))
        # </editor-fold>

        # <editor-fold desc="Detect and handle updates to the SMOOTH_STREAMS_EPG_URL option">
        if configuration['SMOOTH_STREAMS_EPG_URL'] != previous_configuration['SMOOTH_STREAMS_EPG_URL']:
            reset_epg = True

            logger.debug('Detected a change in the url option within the [EPG] section\n'
                         'Old value => {0}\n'
                         'New value => {1}\n\n'
                         'Resetting the EPG'.format(previous_configuration['SMOOTH_STREAMS_EPG_URL'],
                                                    configuration['SMOOTH_STREAMS_EPG_URL']))
        # </editor-fold>

        if reset_epg:
            from .epg import SmoothStreamsEPG

            SmoothStreamsEPG.reset_epg()

    @classmethod
    def read_configuration_file(cls, configuration_object, error_messages):
        is_valid_section = True
        section_found = True

        last_error_message_index = len(error_messages)

        service = None
        server = None
        username = None
        password = None
        playlist_protocol = DEFAULT_SMOOTH_STREAMS_PLAYLIST_PROTOCOL
        playlist_type = DEFAULT_SMOOTH_STREAMS_PLAYLIST_TYPE
        epg_source = DEFAULT_SMOOTH_STREAMS_EPG_SOURCE
        epg_url = ''

        try:
            smooth_streams_section = configuration_object['SmoothStreams']

            try:
                service = smooth_streams_section['service'].lower()
                if not SmoothStreamsValidations.is_valid_service(service):
                    is_valid_section = False

                    error_messages.append(
                        'The service option within the [SmoothStreams] section must be one of\n'
                        '{0}\n'.format('\n'.join(['\u2022 {0}'.format(service)
                                                  for service in VALID_SMOOTH_STREAMS_SERVICE_VALUES])))
            except KeyError:
                is_valid_section = False

                error_messages.append(
                    'Could not find a service option within the [SmoothStreams] section\n'
                    'The service option within the [SmoothStreams] section must be one of\n'
                    '{0}\n'.format('\n'.join(['\u2022 {0}'.format(service)
                                              for service in VALID_SMOOTH_STREAMS_SERVICE_VALUES])))

            try:
                server = smooth_streams_section['server'].lower()
                if not SmoothStreamsValidations.is_valid_server(server):
                    is_valid_section = False

                    error_messages.append(
                        'The server option within the [SmoothStreams] section must be one of\n'
                        '{0}\n'.format('\n'.join(['\u2022 {0}'.format(server)
                                                  for server in VALID_SMOOTH_STREAMS_SERVER_VALUES])))
            except KeyError:
                is_valid_section = False

                error_messages.append(
                    'Could not find a server option within the [SmoothStreams] section\n'
                    'The server option within the [SmoothStreams] section must be one of\n{0}\n'.format(
                        '\n'.join(['\u2022 {0}'.format(server) for server in VALID_SMOOTH_STREAMS_SERVER_VALUES])))

            try:
                username = smooth_streams_section['username']
            except KeyError:
                is_valid_section = False

                error_messages.append('Could not find a username option within the [SmoothStreams] section\n')

            try:
                password = smooth_streams_section['password']
            except KeyError:
                is_valid_section = False

                error_messages.append('Could not find a password option within the [SmoothStreams] section\n')

            try:
                playlist_section = smooth_streams_section['Playlist']

                try:
                    playlist_protocol = playlist_section['protocol'].lower()
                    if not SmoothStreamsValidations.is_valid_playlist_protocol(playlist_protocol):
                        playlist_protocol = DEFAULT_SMOOTH_STREAMS_PLAYLIST_PROTOCOL

                        error_messages.append(
                            'The protocol option within the [Playlist] section must be one of\n'
                            '{0}Defaulting to {1}\n'.format(
                                '\n'.join(['\u2022 {0}'.format(protocol)
                                           for protocol in VALID_SMOOTH_STREAMS_PLAYLIST_PROTOCOL_VALUES]),
                                playlist_protocol))
                except KeyError:
                    error_messages.append(
                        'Could not find a protocol option within the [Playlist] section\n'
                        'The protocol option within the [Playlist] section must be one of\n{0}\n'
                        'Defaulting to {1}\n'.format(
                            '\n'.join(['\u2022 {0}'.format(protocol)
                                       for protocol in VALID_SMOOTH_STREAMS_PLAYLIST_PROTOCOL_VALUES]),
                            playlist_protocol))

                try:
                    playlist_type = playlist_section['type'].lower()
                    if not SmoothStreamsValidations.is_valid_playlist_type(playlist_type):
                        playlist_type = DEFAULT_SMOOTH_STREAMS_PLAYLIST_TYPE

                        error_messages.append(
                            'The type option within the [Playlist] section must be one of\n'
                            '{0}Defaulting to {1}\n'.format(
                                '\n'.join(['\u2022 {0}'.format(type_)
                                           for type_ in VALID_SMOOTH_STREAMS_PLAYLIST_TYPE_VALUES]),
                                playlist_type))
                except KeyError:
                    error_messages.append(
                        'Could not find a type option within the [Playlist] section\n'
                        'The type option within the [Playlist] section must be one of\n{0}\n'
                        'Defaulting to {1}\n'.format(
                            '\n'.join(['\u2022 {0}'.format(type_)
                                       for type_ in VALID_SMOOTH_STREAMS_PLAYLIST_TYPE_VALUES]),
                            playlist_type))
            except KeyError:
                error_messages.append('Could not find a [Playlist] section\n'
                                      'Defaulting the protocol option to {0}\n'
                                      'Defaulting the type option to {1}\n'.format(playlist_protocol,
                                                                                   playlist_type))

            try:
                epg_section = smooth_streams_section['EPG']

                try:
                    epg_source = epg_section['source'].lower()
                    if not SmoothStreamsValidations.is_valid_epg_source(epg_source):
                        epg_source = DEFAULT_SMOOTH_STREAMS_EPG_SOURCE

                        error_messages.append(
                            'The source option within the [EPG] section must be one of\n'
                            '{0}\n'
                            'Defaulting to {1}\n'.format(
                                '\n'.join(['\u2022 {0}'.format(source)
                                           for source in VALID_SMOOTH_STREAMS_EPG_SOURCE_VALUES]),
                                epg_source))
                except KeyError:
                    error_messages.append(
                        'Could not find a source option within the [EPG] section\n'
                        'The source option within the [EPG] section must be one of\n'
                        '{0}\n'
                        'Defaulting to {1}\n'.format('\n'.join(['\u2022 {0}'.format(source)
                                                                for source in VALID_SMOOTH_STREAMS_EPG_SOURCE_VALUES]),
                                                     epg_source))

                if epg_source == 'other':
                    try:
                        epg_url = epg_section['url'].lower()
                        if not SmoothStreamsValidations.is_valid_epg_url(epg_url):
                            error_messages.append(
                                'Could not find a url option within the [EPG] section\n'
                                'The url option within the [EPG] section must be a valid url to a XMLTV file')
                    except KeyError:
                        error_messages.append(
                            'Could not find a url option within the [EPG] section\n'
                            'The url option within the [EPG] section must be a valid url to a XMLTV file')
            except KeyError:
                error_messages.append('Could not find an [EPG] section\n'
                                      'Defaulting the source option to {0}\n'.format(epg_source))
        except KeyError:
            is_valid_section = False
            section_found = False

            error_messages.append('Could not find a [SmoothStreams] section\n')

        if not is_valid_section and section_found:
            error_messages.insert(last_error_message_index,
                                  'Ignoring the [SmoothStreams] section due to invalid values\n')

        return (is_valid_section,
                service,
                server,
                username,
                password,
                playlist_protocol,
                playlist_type,
                epg_source,
                epg_url)

    @classmethod
    def validate_update_configuration_request(cls, configuration, errors):
        if configuration['SMOOTH_STREAMS_SERVICE'] or configuration['SMOOTH_STREAMS_SERVER'] or \
                configuration['SMOOTH_STREAMS_USERNAME'] or configuration['SMOOTH_STREAMS_PASSWORD'] or \
                configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL'] or configuration['SMOOTH_STREAMS_PLAYLIST_TYPE'] or \
                configuration['SMOOTH_STREAMS_EPG_SOURCE'] or configuration['SMOOTH_STREAMS_EPG_URL']:
            if configuration['SMOOTH_STREAMS_SERVICE'] and not \
                    SmoothStreamsValidations.is_valid_service(configuration['SMOOTH_STREAMS_SERVICE']):
                errors['smoothStreamsService'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(service) for service in VALID_SMOOTH_STREAMS_SERVICE_VALUES]))

            if configuration['SMOOTH_STREAMS_SERVER'] and not \
                    SmoothStreamsValidations.is_valid_server(configuration['SMOOTH_STREAMS_SERVER']):
                errors['smoothStreamsServer'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(server) for server in VALID_SMOOTH_STREAMS_SERVER_VALUES]))

            if configuration['SMOOTH_STREAMS_USERNAME'] and not \
                    SmoothStreamsValidations.is_valid_username(configuration['SMOOTH_STREAMS_USERNAME']):
                errors['smoothStreamsUsername'] = 'Must not be an empty value'

            if configuration['SMOOTH_STREAMS_PASSWORD'] and not \
                    SmoothStreamsValidations.is_valid_password(configuration['SMOOTH_STREAMS_PASSWORD']):
                errors['smoothStreamsPassword'] = 'Must not be an empty value'

            if configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL'] and not \
                    SmoothStreamsValidations.is_valid_playlist_protocol(
                        configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL']):
                errors['smoothStreamsPlaylistProtocol'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(service) for service in VALID_SMOOTH_STREAMS_PLAYLIST_PROTOCOL_VALUES]))

            if configuration['SMOOTH_STREAMS_PLAYLIST_TYPE'] and not \
                    SmoothStreamsValidations.is_valid_playlist_type(configuration['SMOOTH_STREAMS_PLAYLIST_TYPE']):
                errors['smoothStreamsPlaylistType'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(service) for service in VALID_SMOOTH_STREAMS_PLAYLIST_TYPE_VALUES]))

            if configuration['SMOOTH_STREAMS_EPG_SOURCE'] and not \
                    SmoothStreamsValidations.is_valid_epg_source(configuration['SMOOTH_STREAMS_EPG_SOURCE']):
                errors['smoothStreamsEpgSource'] = 'Must be one of [{0}]'.format(
                    ', '.join(['\'{0}\''.format(service) for service in VALID_SMOOTH_STREAMS_EPG_SOURCE_VALUES]))

            if configuration['SMOOTH_STREAMS_EPG_SOURCE'] and \
                    configuration['SMOOTH_STREAMS_EPG_SOURCE'] == 'other' and not \
                    SmoothStreamsValidations.is_valid_epg_url(configuration['SMOOTH_STREAMS_EPG_URL']):
                errors['smoothStreamsEpgUrl'] = 'Must be a valid url to a XMLTV file'
