import html
import json
import logging
import pprint
import re
import uuid
from datetime import datetime

import pytz
import requests
import tzlocal

from .configuration import IPTVProxyConfiguration
from .constants import VERSION
from .enums import IPTVProxyRecordingStatus
from .exceptions import IPTVProxyDuplicateRecordingError
from .exceptions import IPTVProxyRecordingNotFoundError
from .recorder import IPTVProxyPVR
from .recorder import IPTVProxyRecording
from .validators import IPTVProxyCerberusValidator

logger = logging.getLogger(__name__)


class IPTVProxyJSONAPI(object):
    __slots__ = ['_http_request', '_json_api_response', '_type']

    def __init__(self, http_request, type_):
        self._http_request = http_request
        self._json_api_response = IPTVProxyJSONAPIResponse()
        self._type = type_

    def _validate_is_request_body_empty(self):
        is_request_body_empty = True

        if self._http_request.request_body:
            is_request_body_empty = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => {0}\n'
                'Requested path => {1}\n'
                'Error Title    => Unsupported request body\n'
                'Error Message  => {2} {3} does not support a request body'.format(
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string,
                    self._http_request.command,
                    self._type))

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Unsupported request body',
                        'field': None,
                        'developer_message': '{0} {1} does not support a request body'.format(
                            self._http_request.command,
                            self._type),
                        'user_message': 'The request is badly formatted'
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_request_body_empty

    def _validate_is_query_string_empty(self):
        is_query_string_empty = True

        query_string_parameters_schema = {}
        query_string_parameters_validator = IPTVProxyCerberusValidator(query_string_parameters_schema)

        if not query_string_parameters_validator.validate(self._http_request.requested_query_string_parameters):
            is_query_string_empty = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => {0}\n'
                'Requested path => {1}\n'
                'Error Title    => Unsupported query parameter{2}\n'
                'Error Message  => {3} {4} does not support [\'{5}\'] query parameter{2}'.format(
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string,
                    's' if len(query_string_parameters_validator.errors) > 1 else '',
                    self._http_request.command,
                    self._type,
                    ', '.join(query_string_parameters_validator.errors)))

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Unsupported query parameter{0}'.format(
                            's' if len(query_string_parameters_validator.errors) > 1 else ''),
                        'field': list(sorted(query_string_parameters_validator.errors)),
                        'developer_message': '{0} {1} does not support [\'{2}\'] query parameter'
                                             '{3}'.format(
                            self._http_request.command,
                            self._type,
                            ', '.join(query_string_parameters_validator.errors),
                            's' if len(query_string_parameters_validator.errors) > 1 else ''),
                        'user_message': 'The request is badly formatted'
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_query_string_empty


class IPTVProxyJSONAPIResponse(object):
    __slots__ = ['_content', '_status_code']

    def __init__(self):
        self._content = None
        self._status_code = -1

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        self._content = content

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, status_code):
        self._status_code = status_code


class IPTVProxyConfigurationJSONAPI(IPTVProxyJSONAPI):
    def __init__(self, http_request):
        IPTVProxyJSONAPI.__init__(self, http_request, 'configuration')

    def _validate_patch_request_body(self):
        is_valid_patch_request_body = True

        try:
            request_body = json.loads(self._http_request.request_body)
            request_body_schema = {
                'data': {
                    'required': True,
                    'schema': {
                        'type': {
                            'allowed': ['configuration'],
                            'required': True,
                        },
                        'attributes': {
                            'required': True,
                            'schema': {
                                'logging_level': {
                                    'required': True
                                },
                                'server_hostname_loopback': {
                                    'required': True
                                },
                                'server_hostname_private': {
                                    'required': True
                                },
                                'server_hostname_public': {
                                    'required': True
                                },
                                'server_http_port': {
                                    'required': True
                                },
                                'server_https_port': {
                                    'required': True
                                },
                                'server_password': {
                                    'required': True
                                },
                                'smooth_streams_epg_source': {
                                    'required': True
                                },
                                'smooth_streams_epg_url': {
                                    'required': True
                                },
                                'smooth_streams_password': {
                                    'required': True
                                },
                                'smooth_streams_playlist_protocol': {
                                    'required': True
                                },
                                'smooth_streams_playlist_type': {
                                    'required': True
                                },
                                'smooth_streams_server': {
                                    'required': True
                                },
                                'smooth_streams_service': {
                                    'required': True
                                },
                                'smooth_streams_username': {
                                    'required': True
                                },
                                'vader_streams_password': {
                                    'required': True
                                },
                                'vader_streams_playlist_protocol': {
                                    'required': True
                                },
                                'vader_streams_playlist_type': {
                                    'required': True
                                },
                                'vader_streams_server': {
                                    'required': True
                                },
                                'vader_streams_username': {
                                    'required': True
                                }
                            },
                            'type': 'dict'
                        }
                    },
                    'type': 'dict'
                }
            }
            request_body_validator = IPTVProxyCerberusValidator(request_body_schema)

            if not request_body_validator.validate(request_body):
                is_valid_patch_request_body = False

                missing_required_fields = [match.group().replace('\'', '')
                                           for match in re.finditer(r'(\'[^{,\[]+\')(?=: \[\'required field\'\])',
                                                                    '{0}'.format(request_body_validator.errors))]

                included_unknown_fields = [match.group().replace('\'', '')
                                           for match in re.finditer(r'(\'[^{,\[]+\')(?=: \[\'unknown field\'\])',
                                                                    '{0}'.format(request_body_validator.errors))]

                invalid_type_value = [match.group().replace('\'', '')
                                      for match in re.finditer(r'(\'[^{,\[]+\')(?=: \[\'unallowed value .*\'\])',
                                                               '{0}'.format(request_body_validator.errors))]

                if missing_required_fields or included_unknown_fields:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Post Data      => {2}\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Request body {3}'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            pprint.pformat(request_body, indent=4),
                            'is missing mandatory field{0} {1}'.format(
                                's' if len(missing_required_fields) > 1 else '',
                                missing_required_fields) if missing_required_fields else
                            'includes unknown field{0} {1}'.format(
                                's' if len(included_unknown_fields) > 1 else '',
                                included_unknown_fields)))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.BAD_REQUEST),
                                'title': 'Invalid resource creation request',
                                'field': '{0}'.format(missing_required_fields if missing_required_fields
                                                      else included_unknown_fields),
                                'developer_message': 'Request body {0}'.format(
                                    'is missing mandatory field{0} {1}'.format(
                                        's' if len(missing_required_fields) > 1 else '',
                                        missing_required_fields) if missing_required_fields else
                                    'includes unknown field{0} {1}'.format(
                                        's' if len(included_unknown_fields) > 1 else '',
                                        included_unknown_fields)),
                                'user_message': 'The request is badly formatted'
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.BAD_REQUEST
                elif invalid_type_value:
                    field = invalid_type_value
                    developer_message = '[\'type\'] must be configuration'
                    user_message = 'The request is badly formatted'

                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Post Data      => {2}\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => {3}'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            pprint.pformat(request_body, indent=4),
                            developer_message))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                                'title': 'Invalid resource creation request',
                                'field': field,
                                'developer_message': '{0}'.format(developer_message),
                                'user_message': '{0}'.format(user_message)
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.UNPROCESSABLE_ENTITY
                else:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Post Data      => {2}\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Unexpected error'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            pprint.pformat(request_body, indent=4)))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                                'title': 'Invalid resource creation request',
                                'field': None,
                                'developer_message': 'Unexpected error',
                                'user_message': 'The request is badly formatted'
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.UNPROCESSABLE_ENTITY
        except (json.JSONDecodeError, TypeError):
            is_valid_patch_request_body = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => {0}\n'
                'Requested path => {1}\n'
                'Error Title    => Invalid request body\n'
                'Error Message  => Request body is not a valid JSON document'.format(
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string))

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Invalid request body',
                        'field': None,
                        'developer_message': 'Request body is not a valid JSON document',
                        'user_message': 'The request is badly formatted'
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_valid_patch_request_body

    def process_get_request(self):
        if self._validate_is_request_body_empty() and self._validate_is_query_string_empty():
            configuration = IPTVProxyConfiguration.get_configuration_copy()

            self._json_api_response.content = {
                'meta': {
                    'application': 'IPTVProxy',
                    'version': VERSION
                },
                'data': {
                    'type': 'configuration',
                    'id': None,
                    'attributes': {
                        'logging_level': configuration['LOGGING_LEVEL'],
                        'server_hostname_loopback': configuration['SERVER_HOSTNAME_LOOPBACK'],
                        'server_hostname_private': configuration['SERVER_HOSTNAME_PRIVATE'],
                        'server_hostname_public': configuration['SERVER_HOSTNAME_PUBLIC'],
                        'server_http_port': configuration['SERVER_HTTP_PORT'],
                        'server_https_port': configuration['SERVER_HTTPS_PORT'],
                        'server_password': configuration['SERVER_PASSWORD'],
                        'smooth_streams_epg_source': configuration['SMOOTH_STREAMS_EPG_SOURCE'],
                        'smooth_streams_epg_url': configuration['SMOOTH_STREAMS_EPG_URL']
                        if configuration['SMOOTH_STREAMS_EPG_URL'] else '',
                        'smooth_streams_password': configuration['SMOOTH_STREAMS_PASSWORD'],
                        'smooth_streams_playlist_protocol': configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL'],
                        'smooth_streams_playlist_type': configuration['SMOOTH_STREAMS_PLAYLIST_TYPE'],
                        'smooth_streams_server': configuration['SMOOTH_STREAMS_SERVER'],
                        'smooth_streams_service': configuration['SMOOTH_STREAMS_SERVICE'],
                        'smooth_streams_username': configuration['SMOOTH_STREAMS_USERNAME'],
                        'vader_streams_password': configuration['VADER_STREAMS_PASSWORD'],
                        'vader_streams_playlist_protocol': configuration['VADER_STREAMS_PLAYLIST_PROTOCOL'],
                        'vader_streams_playlist_type': configuration['VADER_STREAMS_PLAYLIST_TYPE'],
                        'vader_streams_server': configuration['VADER_STREAMS_SERVER'],
                        'vader_streams_username': configuration['VADER_STREAMS_USERNAME']
                    }
                }
            }
            self._json_api_response.status_code = requests.codes.OK

        return (json.dumps(self._json_api_response.content, indent=4), self._json_api_response.status_code)

    def process_patch_request(self):
        if self._validate_patch_request_body() and self._validate_is_query_string_empty():
            request_body = json.loads(self._http_request.request_body)

            update_configuration_request = {
                'LOGGING_LEVEL': request_body['data']['attributes']['logging_level'].upper(),
                'SERVER_HOSTNAME_LOOPBACK': request_body['data']['attributes']['server_hostname_loopback'],
                'SERVER_HOSTNAME_PRIVATE': request_body['data']['attributes']['server_hostname_private'],
                'SERVER_HOSTNAME_PUBLIC': request_body['data']['attributes']['server_hostname_public'],
                'SERVER_HTTPS_PORT': request_body['data']['attributes']['server_https_port'],
                'SERVER_HTTP_PORT': request_body['data']['attributes']['server_http_port'],
                'SERVER_PASSWORD': request_body['data']['attributes']['server_password'],
                'SMOOTH_STREAMS_EPG_SOURCE': request_body['data']['attributes']['smooth_streams_epg_source'].lower(),
                'SMOOTH_STREAMS_EPG_URL': request_body['data']['attributes']['smooth_streams_epg_url'].lower(),
                'SMOOTH_STREAMS_PASSWORD': request_body['data']['attributes']['smooth_streams_password'],
                'SMOOTH_STREAMS_PLAYLIST_PROTOCOL': request_body['data']['attributes'][
                    'smooth_streams_playlist_protocol'].lower(),
                'SMOOTH_STREAMS_PLAYLIST_TYPE': request_body['data']['attributes'][
                    'smooth_streams_playlist_type'].lower(),
                'SMOOTH_STREAMS_SERVER': request_body['data']['attributes']['smooth_streams_server'].lower(),
                'SMOOTH_STREAMS_SERVICE': request_body['data']['attributes']['smooth_streams_service'].lower(),
                'SMOOTH_STREAMS_USERNAME': request_body['data']['attributes']['smooth_streams_username'],
                'VADER_STREAMS_PASSWORD': request_body['data']['attributes']['vader_streams_password'],
                'VADER_STREAMS_PLAYLIST_PROTOCOL': request_body['data']['attributes'][
                    'vader_streams_playlist_protocol'].lower(),
                'VADER_STREAMS_PLAYLIST_TYPE': request_body['data']['attributes'][
                    'vader_streams_playlist_type'].lower(),
                'VADER_STREAMS_SERVER': request_body['data']['attributes']['vader_streams_server'].lower(),
                'VADER_STREAMS_USERNAME': request_body['data']['attributes']['vader_streams_username']
            }

            update_configuration_request_errors = IPTVProxyConfiguration.validate_update_configuration_request(
                update_configuration_request)

            if update_configuration_request_errors:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => {0}\n'
                    'Requested path => {1}\n'
                    'Error Title    => Invalid values specified\n'
                    'Error Message  => Invalid values specified'.format(
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string))

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                            'title': 'Invalid value specified',
                            'field': update_configuration_request_error_field_name,
                            'developer_message': '{0}'.format(
                                update_configuration_request_errors[
                                    update_configuration_request_error_field_name]),
                            'user_message': '{0}'.format(
                                update_configuration_request_errors[
                                    update_configuration_request_error_field_name])
                        }
                        for update_configuration_request_error_field_name in
                        update_configuration_request_errors]
                }
                self._json_api_response.status_code = requests.codes.UNPROCESSABLE_ENTITY
            else:
                try:
                    IPTVProxyConfiguration.write_configuration_file(update_configuration_request)

                    self._json_api_response.content = {
                        'meta': {
                            'application': 'IPTVProxy',
                            'version': VERSION
                        }
                    }
                    self._json_api_response.status_code = requests.codes.OK
                except OSError:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Error Title    => Internal processing error\n'
                        'Error Message  => Failed to write configuration to file'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.INTERNAL_SERVER_ERROR),
                                'title': 'Internal processing error',
                                'field': None,
                                'developer_message': 'Failed to write configuration to file',
                                'user_message': 'Failed to write configuration to file'
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.INTERNAL_SERVER_ERROR

        return (json.dumps(self._json_api_response.content, indent=4), self._json_api_response.status_code)


class IPTVProxyRecordingsJSONAPI(IPTVProxyJSONAPI):
    def __init__(self, http_request):
        IPTVProxyJSONAPI.__init__(self, http_request, 'recordings')

    def _validate_get_request_query_string(self):
        is_valid_get_request_query_string = True

        query_string_parameters_schema = {
            'status': {
                'allowed': [IPTVProxyRecordingStatus.LIVE.value,
                            IPTVProxyRecordingStatus.PERSISTED.value,
                            IPTVProxyRecordingStatus.SCHEDULED.value],
                'type': 'string'
            }
        }
        query_string_parameters_validator = IPTVProxyCerberusValidator(query_string_parameters_schema)

        if not query_string_parameters_validator.validate(self._http_request.requested_query_string_parameters):
            is_valid_get_request_query_string = False

            if [key for key in query_string_parameters_validator.errors if key != 'status']:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => {0}\n'
                    'Requested path => {1}\n'
                    'Error Title    => Unsupported query parameter{2}\n'
                    'Error Message  => {3} recordings does not support [\'{4}\'] query parameter{2}'
                    ''.format(self._http_request.client_ip_address,
                              self._http_request.requested_path_with_query_string,
                              's' if len([error_key
                                          for error_key in query_string_parameters_validator.errors
                                          if error_key != 'status']) > 1 else '',
                              self._http_request.command,
                              ', '.join([error_key
                                         for error_key in query_string_parameters_validator.errors
                                         if error_key != 'status'])))

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.BAD_REQUEST),
                            'title': 'Unsupported query parameter{0}'.format(
                                's' if len(query_string_parameters_validator.errors) > 1 else ''),
                            'field': list(sorted(query_string_parameters_validator.errors)),
                            'developer_message': '{0} recordings does not support [\'{1}\'] query parameter'
                                                 '{2}'.format(
                                self._http_request.command,
                                ', '.join([error_key
                                           for error_key in query_string_parameters_validator.errors
                                           if error_key != 'status']),
                                's' if len([error_key
                                            for error_key in query_string_parameters_validator.errors
                                            if error_key != 'status']) > 1 else ''),
                            'user_message': 'The request is badly formatted'
                        }
                    ]
                }
                self._json_api_response.status_code = requests.codes.BAD_REQUEST
            else:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => {0}\n'
                    'Requested path => {1}\n'
                    'Error Title    => Invalid query parameter value\n'
                    'Error Message  => {2} recordings query parameter [\'status\'] value \'{3}\' '
                    'is not supported'.format(self._http_request.client_ip_address,
                                              self._http_request.requested_path_with_query_string,
                                              self._http_request.command,
                                              self._http_request.requested_query_string_parameters['status']))

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                            'title': 'Invalid query parameter value',
                            'field': ['status'],
                            'developer_message': '{0} recordings query parameter [\'status\'] value '
                                                 '\'{1}\' is not supported'.format(
                                self._http_request.command,
                                self._http_request.requested_query_string_parameters['status']),
                            'user_message': 'The request is badly formatted'
                        }
                    ]
                }
                self._json_api_response.status_code = requests.codes.UNPROCESSABLE_ENTITY

        return is_valid_get_request_query_string

    def _validate_post_request_body(self):
        is_valid_post_request_body = True

        try:
            request_body = json.loads(self._http_request.request_body)
            request_body_schema = {
                'data': {
                    'required': True,
                    'schema': {
                        'type': {
                            'allowed': ['recordings'],
                            'required': True,
                            'type': 'string'
                        },
                        'attributes': {
                            'required': True,
                            'schema': {
                                'channel_number': {
                                    'is_channel_number_valid': 'provider',
                                    'required': True,
                                    'type': 'string'
                                },
                                'end_date_time_in_utc': {
                                    'is_end_date_time_after_start_date_time': 'start_date_time_in_utc',
                                    'is_end_date_time_in_the_future': True,
                                    'required': True,
                                    'type': 'datetime_string'
                                },
                                'program_title': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'provider': {
                                    'is_provider_valid': True,
                                    'required': True,
                                    'type': 'string'
                                },
                                'start_date_time_in_utc': {
                                    'required': True,
                                    'type': 'datetime_string'
                                }
                            },
                            'type': 'dict'
                        }
                    },
                    'type': 'dict'
                }
            }
            request_body_validator = IPTVProxyCerberusValidator(request_body_schema)

            if not request_body_validator.validate(request_body):
                is_valid_post_request_body = False

                pattern = r'(\'[^{,\[]+\')(?=: \[\'required field\'\])'
                missing_required_fields = [match.group().replace('\'', '')
                                           for match in re.finditer(pattern,
                                                                    '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'unknown field\'\])'
                included_unknown_fields = [match.group().replace('\'', '')
                                           for match in re.finditer(pattern,
                                                                    '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be of (datetime_string|string) type\'\])'
                incorrect_type_fields = [match.group().replace('\'', '')
                                         for match in re.finditer(pattern,
                                                                  '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'unallowed value .*\'\])'
                invalid_type_value = [match.group().replace('\'', '')
                                      for match in re.finditer(pattern,
                                                               '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be between [0-9]{2,5} and [0-9]{2,5}\'\])'
                invalid_channel_number = [match.group().replace('\'', '')
                                          for match in re.finditer(pattern,
                                                                   '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be a valid provider\'\])'
                invalid_provider = [match.group().replace('\'', '')
                                    for match in re.finditer(pattern,
                                                             '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be later than now\'\])'
                end_date_time_in_the_future = [match.group().replace('\'', '')
                                               for match in re.finditer(pattern,
                                                                        '{0}'.format(request_body_validator.errors))]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be later than start_date_time_in_utc\'\])'
                end_date_time_after_start_date_time = [match.group().replace('\'', '')
                                                       for match in re.finditer(pattern,
                                                                                '{0}'.format(
                                                                                    request_body_validator.errors))]

                if missing_required_fields or included_unknown_fields:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Post Data      => {2}\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Request body {3}'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            pprint.pformat(request_body, indent=4),
                            'is missing mandatory field{0} {1}'.format(
                                's' if len(missing_required_fields) > 1 else '',
                                missing_required_fields) if missing_required_fields else
                            'includes unknown field{0} {1}'.format(
                                's' if len(included_unknown_fields) > 1 else '',
                                included_unknown_fields)))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.BAD_REQUEST),
                                'title': 'Invalid resource creation request',
                                'field': '{0}'.format(missing_required_fields if missing_required_fields
                                                      else included_unknown_fields),
                                'developer_message': 'Request body {0}'.format(
                                    'is missing mandatory field{0} {1}'.format(
                                        's' if len(missing_required_fields) > 1 else '',
                                        missing_required_fields) if missing_required_fields else
                                    'includes unknown field{0} {1}'.format(
                                        's' if len(included_unknown_fields) > 1 else '',
                                        included_unknown_fields)),
                                'user_message': 'The request is badly formatted'
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.BAD_REQUEST
                elif incorrect_type_fields or invalid_type_value or invalid_channel_number or invalid_provider or \
                        end_date_time_in_the_future or end_date_time_after_start_date_time:
                    field = None
                    developer_message = None
                    user_message = None

                    if incorrect_type_fields:
                        field = incorrect_type_fields
                        developer_message = 'Request body includes field{0} with invalid type {1}'.format(
                            's' if len(incorrect_type_fields) > 1 else '',
                            incorrect_type_fields)
                        user_message = 'The request is badly formatted'
                    elif invalid_type_value == ['type']:
                        field = invalid_type_value
                        developer_message = '[\'type\'] must be recordings'
                        user_message = 'The request is badly formatted'
                    elif invalid_channel_number == ['channel_number']:
                        field = invalid_channel_number
                        developer_message = '[\'channel_number\'] {0}'.format(
                            request_body_validator.errors['data'][0]['attributes'][0]['channel_number'][0])
                        user_message = 'The requested channel does not exist'
                    elif invalid_provider == ['provider']:
                        field = invalid_provider
                        developer_message = '[\'provider\'] {0}'.format(
                            request_body_validator.errors['data'][0]['attributes'][0]['provider'][0])
                        user_message = 'The requested provider does not exist'
                    elif end_date_time_in_the_future == ['end_date_time_in_utc']:
                        field = end_date_time_in_the_future
                        developer_message = '[\'end_date_time_in_utc\'] must be later than now'
                        user_message = 'The requested recording is in the past'
                    elif end_date_time_after_start_date_time == ['end_date_time_in_utc']:
                        field = end_date_time_after_start_date_time
                        developer_message = '[\'end_date_time_in_utc\'] must be later than ' \
                                            '[\'start_date_time_in_utc\']'
                        user_message = 'The request is badly formatted'

                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Post Data      => {2}\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => {3}'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            pprint.pformat(request_body, indent=4),
                            developer_message))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                                'title': 'Invalid resource creation request',
                                'field': field,
                                'developer_message': '{0}'.format(developer_message),
                                'user_message': '{0}'.format(user_message)
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.UNPROCESSABLE_ENTITY
                else:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => {0}\n'
                        'Requested path => {1}\n'
                        'Post Data      => {2}\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Unexpected error'.format(
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            pprint.pformat(request_body, indent=4)))

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                                'title': 'Invalid resource creation request',
                                'field': None,
                                'developer_message': 'Unexpected error',
                                'user_message': 'The request is badly formatted'
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.UNPROCESSABLE_ENTITY
        except (json.JSONDecodeError, TypeError):
            is_valid_post_request_body = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => {0}\n'
                'Requested path => {1}\n'
                'Error Title    => Invalid request body\n'
                'Error Message  => Request body is not a valid JSON document'.format(
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string))

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Invalid request body',
                        'field': None,
                        'developer_message': 'Request body is not a valid JSON document',
                        'user_message': 'The request is badly formatted'
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_valid_post_request_body

    def process_delete_request(self):
        if self._validate_is_request_body_empty() and self._validate_is_query_string_empty():
            recording_id = self._http_request.requested_url_components.path[len('/recordings/'):]

            try:
                recording = IPTVProxyPVR.get_recording(recording_id)

                logger.debug(
                    'Attempting to {0} {1} recording\n'
                    'Provider          => {2}\n'
                    'Channel name      => {3}\n'
                    'Channel number    => {4}\n'
                    'Program title     => {5}\n'
                    'Start date & time => {6}\n'
                    'End date & time   => {7}'.format(
                        'stop' if recording.status == IPTVProxyRecordingStatus.LIVE.value else 'delete',
                        recording.status,
                        recording.provider,
                        recording.channel_name,
                        recording.channel_number,
                        recording.program_title,
                        recording.provider,
                        recording.start_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                        recording.end_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))

                if recording.status == IPTVProxyRecordingStatus.LIVE.value:
                    try:
                        IPTVProxyPVR.stop_live_recording(recording)
                    except KeyError:
                        raise IPTVProxyRecordingNotFoundError
                elif recording.status == IPTVProxyRecordingStatus.PERSISTED.value:
                    try:
                        IPTVProxyPVR.delete_persisted_recording(recording)
                    except OSError:
                        raise IPTVProxyRecordingNotFoundError
                elif recording.status == IPTVProxyRecordingStatus.SCHEDULED.value:
                    try:
                        IPTVProxyPVR.delete_scheduled_recording(recording)
                    except ValueError:
                        raise IPTVProxyRecordingNotFoundError

                logger.info(
                    '{0} {1} recording\n'
                    'Provider          => {2}\n'
                    'Channel name      => {3}\n'
                    'Channel number    => {4}\n'
                    'Program title     => {5}\n'
                    'Start date & time => {6}\n'
                    'End date & time   => {7}'.format(
                        'Stopped' if recording.status == IPTVProxyRecordingStatus.LIVE.value else 'Deleted',
                        recording.status,
                        recording.provider,
                        recording.channel_name,
                        recording.channel_number,
                        recording.program_title,
                        recording.start_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                        recording.end_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')))

                self._json_api_response.content = {
                    'meta': {
                        'application': 'IPTVProxy',
                        'version': VERSION
                    }
                }
                self._json_api_response.status_code = requests.codes.OK
            except IPTVProxyRecordingNotFoundError:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => {0}\n'
                    'Requested path => {1}\n'
                    'Error Title    => Resource not found\n'
                    'Error Message  => Recording with ID {2} does not exist'.format(
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        recording_id))

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.NOT_FOUND),
                            'title': 'Resource not found',
                            'field': None,
                            'developer_message': 'Recording with ID {0} does not exist'.format(
                                recording_id),
                            'user_message': 'Requested recording no longer exists'
                        }
                    ]
                }
                self._json_api_response.status_code = requests.codes.NOT_FOUND

        return (json.dumps(self._json_api_response.content, indent=4), self._json_api_response.status_code)

    def process_get_request(self, recording_id=None):
        if self._validate_is_request_body_empty():
            if recording_id:
                if self._validate_is_query_string_empty():
                    try:
                        recording = IPTVProxyPVR.get_recording(recording_id)

                        server_hostname = IPTVProxyConfiguration.get_configuration_parameter(
                            'SERVER_HOSTNAME_{0}'.format(self._http_request.client_ip_address_type.value))
                        server_port = IPTVProxyConfiguration.get_configuration_parameter(
                            'SERVER_HTTP{0}_PORT'.format('S' if self._http_request.server.is_secure else ''))

                        playlist_url = None
                        if recording.status == IPTVProxyRecordingStatus.PERSISTED.value:
                            playlist_url = IPTVProxyPVR.generate_recording_playlist_url(
                                self._http_request.server.is_secure,
                                server_hostname,
                                server_port,
                                '{0}'.format(uuid.uuid4()),
                                recording.base_recording_directory,
                                IPTVProxyConfiguration.get_configuration_parameter('SERVER_PASSWORD'))

                        self._json_api_response.content = {
                            'meta': {
                                'application': 'IPTVProxy',
                                'version': VERSION
                            },
                            'data': {
                                'type': 'recordings',
                                'id': recording.id,
                                'attributes': {
                                    'channel_name': recording.channel_name,
                                    'channel_number': recording.channel_number,
                                    'end_date_time_in_utc': '{0}'.format(recording.end_date_time_in_utc),
                                    'playlist_url': playlist_url,
                                    'program_title': recording.program_title,
                                    'provider': recording.provider,
                                    'start_date_time_in_utc': '{0}'.format(recording.start_date_time_in_utc),
                                    'status': recording.status
                                }
                            }
                        }
                        self._json_api_response.status_code = requests.codes.OK
                    except IPTVProxyRecordingNotFoundError:
                        logger.error(
                            'Error encountered processing request\n'
                            'Source IP      => {0}\n'
                            'Requested path => {1}\n'
                            'Error Title    => Resource not found\n'
                            'Error Message  => Recording with ID {2} does not exist'.format(
                                self._http_request.client_ip_address,
                                self._http_request.requested_path_with_query_string,
                                recording_id))

                        self._json_api_response.content = {
                            'errors': [
                                {
                                    'status': '{0}'.format(requests.codes.NOT_FOUND),
                                    'title': 'Resource not found',
                                    'field': None,
                                    'developer_message': 'Recording with ID {0} does not exist'.format(
                                        recording_id),
                                    'user_message': 'Requested recording does not exist'
                                }
                            ]
                        }
                        self._json_api_response.status_code = requests.codes.NOT_FOUND
            else:
                if self._validate_get_request_query_string():
                    server_hostname = IPTVProxyConfiguration.get_configuration_parameter(
                        'SERVER_HOSTNAME_{0}'.format(self._http_request.client_ip_address_type.value))
                    server_port = IPTVProxyConfiguration.get_configuration_parameter(
                        'SERVER_HTTP{0}_PORT'.format('S' if self._http_request.server.is_secure else ''))

                    self._json_api_response.content = {
                        'meta': {
                            'application': 'IPTVProxy',
                            'version': VERSION
                        },
                        'data': []
                    }

                    status = self._http_request.requested_query_string_parameters.get('status')

                    for recording in [recording for recording in IPTVProxyPVR.get_recordings()
                                      if status is None or status == recording.status]:
                        playlist_url = None
                        if recording.status == IPTVProxyRecordingStatus.PERSISTED.value:
                            playlist_url = IPTVProxyPVR.generate_recording_playlist_url(
                                self._http_request.server.is_secure,
                                server_hostname,
                                server_port,
                                '{0}'.format(uuid.uuid4()),
                                recording.base_recording_directory,
                                IPTVProxyConfiguration.get_configuration_parameter('SERVER_PASSWORD'))

                        self._json_api_response.content['data'].append({
                            'type': 'recordings',
                            'id': recording.id,
                            'attributes': {
                                'channel_name': recording.channel_name,
                                'channel_number': recording.channel_number,
                                'end_date_time_in_utc': '{0}'.format(recording.end_date_time_in_utc),
                                'playlist_url': playlist_url,
                                'program_title': recording.program_title,
                                'provider': recording.provider,
                                'start_date_time_in_utc': '{0}'.format(recording.start_date_time_in_utc),
                                'status': recording.status
                            }
                        })

                    self._json_api_response.status_code = requests.codes.OK

        return (json.dumps(self._json_api_response.content, indent=4), self._json_api_response.status_code)

    def process_post_request(self):
        if self._validate_post_request_body() and self._validate_is_query_string_empty():
            request_body = json.loads(self._http_request.request_body)

            channel_name = IPTVProxyConfiguration.get_provider(
                html.unescape(request_body['data']['attributes']['provider']).lower())['epg'].get_channel_name(
                int(request_body['data']['attributes']['channel_number']))
            channel_number = request_body['data']['attributes']['channel_number']
            end_date_time_in_utc = datetime.strptime(request_body['data']['attributes']['end_date_time_in_utc'],
                                                     '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)
            id_ = '{0}'.format(uuid.uuid4())
            program_title = html.unescape(request_body['data']['attributes']['program_title'])
            provider = html.unescape(request_body['data']['attributes']['provider'])
            start_date_time_in_utc = datetime.strptime(request_body['data']['attributes']['start_date_time_in_utc'],
                                                       '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc)

            recording = IPTVProxyRecording(channel_name,
                                           channel_number,
                                           end_date_time_in_utc,
                                           id_,
                                           program_title,
                                           provider,
                                           start_date_time_in_utc,
                                           IPTVProxyRecordingStatus.SCHEDULED.value)

            try:
                IPTVProxyPVR.add_scheduled_recording(recording)

                logger.info(
                    'Scheduled recording\n'
                    'Provider          => {0}\n'
                    'Channel name      => {1}\n'
                    'Channel number    => {2}\n'
                    'Program title     => {3}\n'
                    'Start date & time => {4}\n'
                    'End date & time   => {5}'.format(provider,
                                                      channel_name,
                                                      channel_number,
                                                      program_title,
                                                      start_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime(
                                                          '%Y-%m-%d %H:%M:%S'),
                                                      end_date_time_in_utc.astimezone(
                                                          tzlocal.get_localzone()).strftime(
                                                          '%Y-%m-%d %H:%M:%S')))

                self._json_api_response.content = {
                    'meta': {
                        'application': 'IPTVProxy',
                        'version': VERSION
                    },
                    'data': {
                        'type': 'recordings',
                        'id': id_,
                        'attributes': {
                            'channel_name': channel_name,
                            'channel_number': channel_number,
                            'end_date_time_in_utc': '{0}'.format(end_date_time_in_utc),
                            'program_title': program_title,
                            'provider': provider,
                            'start_date_time_in_utc': '{0}'.format(start_date_time_in_utc),
                            'status': 'scheduled'
                        }
                    }
                }
                self._json_api_response.status_code = requests.codes.CREATED
            except IPTVProxyDuplicateRecordingError:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => {0}\n'
                    'Requested path => {1}\n'
                    'Post Data      => {2}\n'
                    'Error Title    => Duplicate resource\n'
                    'Error Message  => Recording already scheduled'.format(
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4)))

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.CONFLICT),
                            'field': None,
                            'title': 'Duplicate resource',
                            'developer_message': 'Recording already scheduled',
                            'user_message': 'The recording is already scheduled'
                        }
                    ]
                }
                self._json_api_response.status_code = requests.codes.CONFLICT

        return (json.dumps(self._json_api_response.content, indent=4), self._json_api_response.status_code)
