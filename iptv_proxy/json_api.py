import html
import json
import logging
import pprint
import re
import sys
import traceback
import uuid
import warnings
from datetime import datetime
from json import JSONDecodeError

import pytz
import requests
import tzlocal
from cerberus import Validator

from iptv_proxy.configuration import Configuration
from iptv_proxy.constants import VERSION
from iptv_proxy.data_model import Recording
from iptv_proxy.db import Database
from iptv_proxy.enums import RecordingStatus
from iptv_proxy.exceptions import DuplicateRecordingError
from iptv_proxy.exceptions import RecordingNotFoundError
from iptv_proxy.providers import ProvidersController
from iptv_proxy.recorder import PVR

logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class JSONAPI(object):
    __slots__ = ['_http_request', '_json_api_response', '_type']

    def __init__(self, http_request, type_):
        self._http_request = http_request
        self._json_api_response = JSONAPIResponse()
        self._type = type_

    def _validate_is_request_body_empty(self):
        is_request_body_empty = True

        if self._http_request.request_body:
            is_request_body_empty = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => %s\n'
                'Requested path => %s\n'
                'Error Title    => Unsupported request body\n'
                'Error Message  => %s %s does not support a request body',
                self._http_request.client_ip_address,
                self._http_request.requested_path_with_query_string,
                self._http_request.command,
                self._type,
            )

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Unsupported request body',
                        'field': None,
                        'developer_message': '{0} {1} does not support a request body'.format(
                            self._http_request.command, self._type
                        ),
                        'user_message': 'The request is badly formatted',
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_request_body_empty

    def _validate_is_query_string_empty(self):
        is_query_string_empty = True

        query_string_parameters_schema = {}
        query_string_parameters_validator = JSONAPIValidator(
            query_string_parameters_schema
        )

        if not query_string_parameters_validator.validate(
            self._http_request.requested_query_string_parameters
        ):
            is_query_string_empty = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => %s\n'
                'Requested path => %s\n'
                'Error Title    => Unsupported query parameter%s\n'
                'Error Message  => %s %s does not support [\'%s\'] query parameter%s',
                self._http_request.client_ip_address,
                self._http_request.requested_path_with_query_string,
                's' if len(query_string_parameters_validator.errors) > 1 else '',
                self._http_request.command,
                self._type,
                ', '.join(query_string_parameters_validator.errors),
                's' if len(query_string_parameters_validator.errors) > 1 else '',
            )

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Unsupported query parameter{0}'.format(
                            's'
                            if len(query_string_parameters_validator.errors) > 1
                            else ''
                        ),
                        'field': list(sorted(query_string_parameters_validator.errors)),
                        'developer_message': '{0} {1} does not support [\'{2}\'] query parameter'
                        '{3}'.format(
                            self._http_request.command,
                            self._type,
                            ', '.join(query_string_parameters_validator.errors),
                            's'
                            if len(query_string_parameters_validator.errors) > 1
                            else '',
                        ),
                        'user_message': 'The request is badly formatted',
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_query_string_empty


class JSONAPIResponse(object):
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


class JSONAPIValidator(Validator):
    def _validate_is_channel_number_valid(self, other, field, value):
        if other not in self.document:
            return False

        try:
            provider_map_class = ProvidersController.get_provider_map_class(
                self.document[other].lower()
            )
            if not provider_map_class.epg_class().is_channel_number_in_epg(value):
                self._error(
                    field,
                    'must be between {0:02} and {1:02}'.format(
                        *provider_map_class.epg_class().get_channel_numbers_range()
                    ),
                )
        except KeyError:
            return False

    def _validate_is_end_date_time_after_start_date_time(self, other, field, value):
        if other not in self.document:
            return False

        end_date_time_in_utc = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(
            tzinfo=pytz.utc
        )
        start_date_time_in_utc = datetime.strptime(
            self.document[other], '%Y-%m-%d %H:%M:%S'
        ).replace(tzinfo=pytz.utc)
        if end_date_time_in_utc <= start_date_time_in_utc:
            self._error(field, 'must be later than start_date_time_in_utc')

    def _validate_is_end_date_time_in_the_future(
        self, is_end_date_time_in_the_future, field, value
    ):
        end_date_time_in_utc = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(
            tzinfo=pytz.utc
        )
        if (
            is_end_date_time_in_the_future
            and datetime.now(pytz.utc) > end_date_time_in_utc
        ):
            self._error(field, 'must be later than now')

    def _validate_is_provider_valid(self, is_provider_valid, field, value):
        if is_provider_valid:
            try:
                ProvidersController.get_provider_map_class(value.lower())
            except KeyError:
                self._error(field, 'must be a valid provider')

    def _validate_type_datetime_string(self, value):
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

            return True
        except (TypeError, ValueError):
            return False


class ConfigurationJSONAPI(JSONAPI):
    def __init__(self, http_request):
        JSONAPI.__init__(self, http_request, 'configuration')

    @classmethod
    def create_get_request_response_content(cls):
        configuration = Configuration.get_configuration_copy()

        json_api_response_content = {
            'meta': {'application': 'IPTVProxy', 'version': VERSION},
            'data': {
                'type': 'configuration',
                'id': None,
                'attributes': {
                    'server_hostname_loopback': configuration[
                        'SERVER_HOSTNAME_LOOPBACK'
                    ],
                    'server_hostname_private': configuration['SERVER_HOSTNAME_PRIVATE'],
                    'server_hostname_public': configuration['SERVER_HOSTNAME_PUBLIC'],
                    'server_http_port': configuration['SERVER_HTTP_PORT'],
                    'server_https_port': configuration['SERVER_HTTPS_PORT'],
                    'server_password': configuration['SERVER_PASSWORD'],
                },
            },
        }

        for provider_name in sorted(ProvidersController.get_providers_map_class()):
            json_api_response_content['data']['attributes'].update(
                ProvidersController.get_provider_map_class(provider_name)
                .configuration_json_api_class()
                .create_get_request_response_content(configuration)
            )

        return json_api_response_content

    @classmethod
    def create_patch_request_update_configuration_request(cls, request_body):
        update_configuration_request = {
            'SERVER_HOSTNAME_LOOPBACK': request_body['data']['attributes'][
                'server_hostname_loopback'
            ],
            'SERVER_HOSTNAME_PRIVATE': request_body['data']['attributes'][
                'server_hostname_private'
            ],
            'SERVER_HOSTNAME_PUBLIC': request_body['data']['attributes'][
                'server_hostname_public'
            ],
            'SERVER_HTTPS_PORT': request_body['data']['attributes'][
                'server_https_port'
            ],
            'SERVER_HTTP_PORT': request_body['data']['attributes']['server_http_port'],
            'SERVER_PASSWORD': request_body['data']['attributes']['server_password'],
        }

        for provider_name in sorted(ProvidersController.get_providers_map_class()):
            update_configuration_request.update(
                ProvidersController.get_provider_map_class(provider_name)
                .configuration_json_api_class()
                .create_patch_request_update_configuration_request(request_body)
            )

        return update_configuration_request

    @classmethod
    def _create_validate_patch_request_body_schema(cls):
        request_body_schema = {
            'data': {
                'required': True,
                'schema': {
                    'type': {'allowed': ['configuration'], 'required': True,},
                    'attributes': {
                        'required': True,
                        'schema': {
                            'server_hostname_loopback': {'required': True},
                            'server_hostname_private': {'required': True},
                            'server_hostname_public': {'required': True},
                            'server_http_port': {'required': True},
                            'server_https_port': {'required': True},
                            'server_password': {'required': True},
                        },
                        'type': 'dict',
                    },
                },
                'type': 'dict',
            }
        }

        for provider_name in sorted(ProvidersController.get_providers_map_class()):
            request_body_schema['data']['schema']['attributes']['schema'].update(
                ProvidersController.get_provider_map_class(provider_name)
                .configuration_json_api_class()
                .create_validate_patch_request_body_schema()
            )

        return request_body_schema

    def _validate_patch_request_body(self):
        is_valid_patch_request_body = True

        try:
            request_body = json.loads(self._http_request.request_body)
            request_body_schema = (
                ConfigurationJSONAPI._create_validate_patch_request_body_schema()
            )
            request_body_validator = JSONAPIValidator(request_body_schema)

            if not request_body_validator.validate(request_body):
                is_valid_patch_request_body = False

                missing_required_fields = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        r'(\'[^{,\[]+\')(?=: \[\'required field\'\])',
                        '{0}'.format(request_body_validator.errors),
                    )
                ]

                included_unknown_fields = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        r'(\'[^{,\[]+\')(?=: \[\'unknown field\'\])',
                        '{0}'.format(request_body_validator.errors),
                    )
                ]

                invalid_type_value = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        r'(\'[^{,\[]+\')(?=: \[\'unallowed value .*\'\])',
                        '{0}'.format(request_body_validator.errors),
                    )
                ]

                if missing_required_fields or included_unknown_fields:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Request body %s',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                        'is missing mandatory field{0} {1}'.format(
                            's' if len(missing_required_fields) > 1 else '',
                            missing_required_fields,
                        )
                        if missing_required_fields
                        else 'includes unknown field{0} {1}'.format(
                            's' if len(included_unknown_fields) > 1 else '',
                            included_unknown_fields,
                        ),
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.BAD_REQUEST),
                                'title': 'Invalid resource creation request',
                                'field': '{0}'.format(
                                    missing_required_fields
                                    if missing_required_fields
                                    else included_unknown_fields
                                ),
                                'developer_message': 'Request body {0}'.format(
                                    'is missing mandatory field{0} {1}'.format(
                                        's' if len(missing_required_fields) > 1 else '',
                                        missing_required_fields,
                                    )
                                    if missing_required_fields
                                    else 'includes unknown field{0} {1}'.format(
                                        's' if len(included_unknown_fields) > 1 else '',
                                        included_unknown_fields,
                                    )
                                ),
                                'user_message': 'The request is badly formatted',
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
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => %s',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                        developer_message,
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(
                                    requests.codes.UNPROCESSABLE_ENTITY
                                ),
                                'title': 'Invalid resource creation request',
                                'field': field,
                                'developer_message': '{0}'.format(developer_message),
                                'user_message': '{0}'.format(user_message),
                            }
                        ]
                    }
                    self._json_api_response.status_code = (
                        requests.codes.UNPROCESSABLE_ENTITY
                    )
                else:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Unexpected error',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(
                                    requests.codes.UNPROCESSABLE_ENTITY
                                ),
                                'title': 'Invalid resource creation request',
                                'field': None,
                                'developer_message': 'Unexpected error',
                                'user_message': 'The request is badly formatted',
                            }
                        ]
                    }
                    self._json_api_response.status_code = (
                        requests.codes.UNPROCESSABLE_ENTITY
                    )
        except (JSONDecodeError, TypeError):
            is_valid_patch_request_body = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => %s\n'
                'Requested path => %s\n'
                'Error Title    => Invalid request body\n'
                'Error Message  => Request body is not a valid JSON document',
                self._http_request.client_ip_address,
                self._http_request.requested_path_with_query_string,
            )

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Invalid request body',
                        'field': None,
                        'developer_message': 'Request body is not a valid JSON document',
                        'user_message': 'The request is badly formatted',
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_valid_patch_request_body

    def process_get_request(self):
        if (
            self._validate_is_request_body_empty()
            and self._validate_is_query_string_empty()
        ):
            self._json_api_response.content = (
                ConfigurationJSONAPI.create_get_request_response_content()
            )
            self._json_api_response.status_code = requests.codes.OK

        return (
            json.dumps(self._json_api_response.content, indent=4),
            self._json_api_response.status_code,
        )

    def process_patch_request(self):
        if (
            self._validate_patch_request_body()
            and self._validate_is_query_string_empty()
        ):
            request_body = json.loads(self._http_request.request_body)

            update_configuration_request = ConfigurationJSONAPI.create_patch_request_update_configuration_request(
                request_body
            )

            update_configuration_request_errors = Configuration.validate_update_configuration_request(
                update_configuration_request
            )

            if update_configuration_request_errors:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => %s\n'
                    'Requested path => %s\n'
                    'Error Title    => Invalid values specified\n'
                    'Error Message  => Invalid values specified',
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string,
                )

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                            'title': 'Invalid value specified',
                            'field': update_configuration_request_error_field_name,
                            'developer_message': '{0}'.format(
                                update_configuration_request_errors[
                                    update_configuration_request_error_field_name
                                ]
                            ),
                            'user_message': '{0}'.format(
                                update_configuration_request_errors[
                                    update_configuration_request_error_field_name
                                ]
                            ),
                        }
                        for update_configuration_request_error_field_name in update_configuration_request_errors
                    ]
                }
                self._json_api_response.status_code = (
                    requests.codes.UNPROCESSABLE_ENTITY
                )
            else:
                try:
                    Configuration.write_configuration_file(update_configuration_request)

                    self._json_api_response.content = {
                        'meta': {'application': 'IPTVProxy', 'version': VERSION}
                    }
                    self._json_api_response.status_code = requests.codes.OK
                except OSError:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Error Title    => Internal processing error\n'
                        'Error Message  => Failed to write configuration to file',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(
                                    requests.codes.INTERNAL_SERVER_ERROR
                                ),
                                'title': 'Internal processing error',
                                'field': None,
                                'developer_message': 'Failed to write configuration to file',
                                'user_message': 'Failed to write configuration to file',
                            }
                        ]
                    }
                    self._json_api_response.status_code = (
                        requests.codes.INTERNAL_SERVER_ERROR
                    )

        return (
            json.dumps(self._json_api_response.content, indent=4),
            self._json_api_response.status_code,
        )


class RecordingsJSONAPI(JSONAPI):
    def __init__(self, http_request):
        JSONAPI.__init__(self, http_request, 'recordings')

    def _validate_get_request_query_string(self):
        is_valid_get_request_query_string = True

        query_string_parameters_schema = {
            'status': {
                'allowed': [
                    RecordingStatus.LIVE.value,
                    RecordingStatus.PERSISTED.value,
                    RecordingStatus.SCHEDULED.value,
                ],
                'type': 'string',
            }
        }
        query_string_parameters_validator = JSONAPIValidator(
            query_string_parameters_schema
        )

        if not query_string_parameters_validator.validate(
            self._http_request.requested_query_string_parameters
        ):
            is_valid_get_request_query_string = False

            if [
                key
                for key in query_string_parameters_validator.errors
                if key != 'status'
            ]:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => %s\n'
                    'Requested path => %s\n'
                    'Error Title    => Unsupported query parameter%s\n'
                    'Error Message  => %s recordings does not support [\'%s\'] query parameter%s',
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string,
                    's'
                    if len(
                        [
                            error_key
                            for error_key in query_string_parameters_validator.errors
                            if error_key != 'status'
                        ]
                    )
                    > 1
                    else '',
                    self._http_request.command,
                    ', '.join(
                        [
                            error_key
                            for error_key in query_string_parameters_validator.errors
                            if error_key != 'status'
                        ]
                    ),
                    's'
                    if len(
                        [
                            error_key
                            for error_key in query_string_parameters_validator.errors
                            if error_key != 'status'
                        ]
                    )
                    > 1
                    else '',
                )

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.BAD_REQUEST),
                            'title': 'Unsupported query parameter{0}'.format(
                                's'
                                if len(query_string_parameters_validator.errors) > 1
                                else ''
                            ),
                            'field': list(
                                sorted(query_string_parameters_validator.errors)
                            ),
                            'developer_message': '{0} recordings does not support [\'{1}\'] query parameter {2}'.format(
                                self._http_request.command,
                                ', '.join(
                                    [
                                        error_key
                                        for error_key in query_string_parameters_validator.errors
                                        if error_key != 'status'
                                    ]
                                ),
                                's'
                                if len(
                                    [
                                        error_key
                                        for error_key in query_string_parameters_validator.errors
                                        if error_key != 'status'
                                    ]
                                )
                                > 1
                                else '',
                            ),
                            'user_message': 'The request is badly formatted',
                        }
                    ]
                }
                self._json_api_response.status_code = requests.codes.BAD_REQUEST
            else:
                logger.error(
                    'Error encountered processing request\n'
                    'Source IP      => %s\n'
                    'Requested path => %s\n'
                    'Error Title    => Invalid query parameter value\n'
                    'Error Message  => %s recordings query parameter [\'status\'] '
                    'value \'%s\' is not supported',
                    self._http_request.client_ip_address,
                    self._http_request.requested_path_with_query_string,
                    self._http_request.command,
                    self._http_request.requested_query_string_parameters['status'],
                )

                self._json_api_response.content = {
                    'errors': [
                        {
                            'status': '{0}'.format(requests.codes.UNPROCESSABLE_ENTITY),
                            'title': 'Invalid query parameter value',
                            'field': ['status'],
                            'developer_message': '{0} recordings query parameter [\'status\'] value '
                            '\'{1}\' is not supported'.format(
                                self._http_request.command,
                                self._http_request.requested_query_string_parameters[
                                    'status'
                                ],
                            ),
                            'user_message': 'The request is badly formatted',
                        }
                    ]
                }
                self._json_api_response.status_code = (
                    requests.codes.UNPROCESSABLE_ENTITY
                )

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
                            'type': 'string',
                        },
                        'attributes': {
                            'required': True,
                            'schema': {
                                'channel_number': {
                                    'is_channel_number_valid': 'provider',
                                    'required': True,
                                    'type': 'string',
                                },
                                'end_date_time_in_utc': {
                                    'is_end_date_time_after_start_date_time': 'start_date_time_in_utc',
                                    'is_end_date_time_in_the_future': True,
                                    'required': True,
                                    'type': 'datetime_string',
                                },
                                'program_title': {'required': True, 'type': 'string'},
                                'provider': {
                                    'is_provider_valid': True,
                                    'required': True,
                                    'type': 'string',
                                },
                                'start_date_time_in_utc': {
                                    'required': True,
                                    'type': 'datetime_string',
                                },
                            },
                            'type': 'dict',
                        },
                    },
                    'type': 'dict',
                }
            }
            request_body_validator = JSONAPIValidator(request_body_schema)

            if not request_body_validator.validate(request_body):
                is_valid_post_request_body = False

                pattern = r'(\'[^{,\[]+\')(?=: \[\'required field\'\])'
                missing_required_fields = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'unknown field\'\])'
                included_unknown_fields = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be of (datetime_string|string) type\'\])'
                incorrect_type_fields = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'unallowed value .*\'\])'
                invalid_type_value = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be between [0-9]{2,5} and [0-9]{2,5}\'\])'
                invalid_channel_number = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be a valid provider\'\])'
                invalid_provider = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be later than now\'\])'
                end_date_time_in_the_future = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                pattern = r'(\'[^{,\[]+\')(?=: \[\'must be later than start_date_time_in_utc\'\])'
                end_date_time_after_start_date_time = [
                    match.group().replace('\'', '')
                    for match in re.finditer(
                        pattern, '{0}'.format(request_body_validator.errors)
                    )
                ]

                if missing_required_fields or included_unknown_fields:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Request body %s',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                        'is missing mandatory field{0} {1}'.format(
                            's' if len(missing_required_fields) > 1 else '',
                            missing_required_fields,
                        )
                        if missing_required_fields
                        else 'includes unknown field{0} {1}'.format(
                            's' if len(included_unknown_fields) > 1 else '',
                            included_unknown_fields,
                        ),
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.BAD_REQUEST),
                                'title': 'Invalid resource creation request',
                                'field': '{0}'.format(
                                    missing_required_fields
                                    if missing_required_fields
                                    else included_unknown_fields
                                ),
                                'developer_message': 'Request body {0}'.format(
                                    'is missing mandatory field{0} {1}'.format(
                                        's' if len(missing_required_fields) > 1 else '',
                                        missing_required_fields,
                                    )
                                    if missing_required_fields
                                    else 'includes unknown field{0} {1}'.format(
                                        's' if len(included_unknown_fields) > 1 else '',
                                        included_unknown_fields,
                                    )
                                ),
                                'user_message': 'The request is badly formatted',
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.BAD_REQUEST
                elif (
                    incorrect_type_fields
                    or invalid_type_value
                    or invalid_channel_number
                    or invalid_provider
                    or end_date_time_in_the_future
                    or end_date_time_after_start_date_time
                ):
                    field = None
                    developer_message = None
                    user_message = None

                    if incorrect_type_fields:
                        field = incorrect_type_fields
                        developer_message = 'Request body includes field{0} with invalid type {1}'.format(
                            's' if len(incorrect_type_fields) > 1 else '',
                            incorrect_type_fields,
                        )
                        user_message = 'The request is badly formatted'
                    elif invalid_type_value == ['type']:
                        field = invalid_type_value
                        developer_message = '[\'type\'] must be recordings'
                        user_message = 'The request is badly formatted'
                    elif invalid_channel_number == ['channel_number']:
                        field = invalid_channel_number
                        developer_message = '[\'channel_number\'] {0}'.format(
                            request_body_validator.errors['data'][0]['attributes'][0][
                                'channel_number'
                            ][0]
                        )
                        user_message = 'The requested channel does not exist'
                    elif invalid_provider == ['provider']:
                        field = invalid_provider
                        developer_message = '[\'provider\'] {0}'.format(
                            request_body_validator.errors['data'][0]['attributes'][0][
                                'provider'
                            ][0]
                        )
                        user_message = 'The requested provider does not exist'
                    elif end_date_time_in_the_future == ['end_date_time_in_utc']:
                        field = end_date_time_in_the_future
                        developer_message = (
                            '[\'end_date_time_in_utc\'] must be later than now'
                        )
                        user_message = 'The requested recording is in the past'
                    elif end_date_time_after_start_date_time == [
                        'end_date_time_in_utc'
                    ]:
                        field = end_date_time_after_start_date_time
                        developer_message = (
                            '[\'end_date_time_in_utc\'] must be later than '
                            '[\'start_date_time_in_utc\']'
                        )
                        user_message = 'The request is badly formatted'

                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => %s',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                        developer_message,
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(
                                    requests.codes.UNPROCESSABLE_ENTITY
                                ),
                                'title': 'Invalid resource creation request',
                                'field': field,
                                'developer_message': '{0}'.format(developer_message),
                                'user_message': '{0}'.format(user_message),
                            }
                        ]
                    }
                    self._json_api_response.status_code = (
                        requests.codes.UNPROCESSABLE_ENTITY
                    )
                else:
                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Invalid resource creation request\n'
                        'Error Message  => Unexpected error',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(
                                    requests.codes.UNPROCESSABLE_ENTITY
                                ),
                                'title': 'Invalid resource creation request',
                                'field': None,
                                'developer_message': 'Unexpected error',
                                'user_message': 'The request is badly formatted',
                            }
                        ]
                    }
                    self._json_api_response.status_code = (
                        requests.codes.UNPROCESSABLE_ENTITY
                    )
        except (JSONDecodeError, TypeError):
            is_valid_post_request_body = False

            logger.error(
                'Error encountered processing request\n'
                'Source IP      => %s\n'
                'Requested path => %s\n'
                'Error Title    => Invalid request body\n'
                'Error Message  => Request body is not a valid JSON document',
                self._http_request.client_ip_address,
                self._http_request.requested_path_with_query_string,
            )

            self._json_api_response.content = {
                'errors': [
                    {
                        'status': '{0}'.format(requests.codes.BAD_REQUEST),
                        'title': 'Invalid request body',
                        'field': None,
                        'developer_message': 'Request body is not a valid JSON document',
                        'user_message': 'The request is badly formatted',
                    }
                ]
            }
            self._json_api_response.status_code = requests.codes.BAD_REQUEST

        return is_valid_post_request_body

    def process_delete_request(self):
        if (
            self._validate_is_request_body_empty()
            and self._validate_is_query_string_empty()
        ):
            recording_id = self._http_request.requested_url_components.path[
                len('/recordings/') :
            ]

            with Database.get_write_lock():
                db_session = Database.create_session()

                try:
                    recording = PVR.get_recording(db_session, recording_id)

                    logger.debug(
                        'Attempting to %s %s recording\n'
                        'Provider          => %s\n'
                        'Channel number    => %s\n'
                        'Channel name      => %s\n'
                        'Program title     => %s\n'
                        'Start date & time => %s\n'
                        'End date & time   => %s',
                        'stop'
                        if recording.status == RecordingStatus.LIVE.value
                        else 'delete',
                        recording.status,
                        recording.provider,
                        recording.channel_number,
                        recording.channel_name,
                        recording.program_title,
                        recording.start_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        recording.end_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                    )

                    if recording.status == RecordingStatus.LIVE.value:
                        PVR.stop_live_recording(db_session, recording)
                    else:
                        PVR.delete_recording(db_session, recording)

                    db_session.commit()

                    logger.info(
                        '%s %s recording\n'
                        'Provider          => %s\n'
                        'Channel name      => %s\n'
                        'Channel number    => %s\n'
                        'Program title     => %s\n'
                        'Start date & time => %s\n'
                        'End date & time   => %s',
                        'Stopped'
                        if recording.status == RecordingStatus.LIVE.value
                        else 'Deleted',
                        recording.status,
                        recording.provider,
                        recording.channel_name,
                        recording.channel_number,
                        recording.program_title,
                        recording.start_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        recording.end_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                    )

                    self._json_api_response.content = {
                        'meta': {'application': 'IPTVProxy', 'version': VERSION}
                    }
                    self._json_api_response.status_code = requests.codes.OK
                except RecordingNotFoundError:
                    db_session.rollback()

                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Error Title    => Resource not found\n'
                        'Error Message  => Recording with ID %s does not exist',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        recording_id,
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.NOT_FOUND),
                                'title': 'Resource not found',
                                'field': None,
                                'developer_message': 'Recording with ID {0} does not exist'.format(
                                    recording_id
                                ),
                                'user_message': 'Requested recording no longer exists',
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.NOT_FOUND
                except Exception:
                    (type_, value_, traceback_) = sys.exc_info()
                    logger.error(
                        '\n'.join(traceback.format_exception(type_, value_, traceback_))
                    )

                    db_session.rollback()
                finally:
                    db_session.close()

        return (
            json.dumps(self._json_api_response.content, indent=4),
            self._json_api_response.status_code,
        )

    def process_get_request(self, recording_id=None):
        if self._validate_is_request_body_empty():
            if recording_id:
                if self._validate_is_query_string_empty():
                    db_session = Database.create_session()

                    try:
                        recording = PVR.get_recording(db_session, recording_id)

                        server_hostname = Configuration.get_configuration_parameter(
                            'SERVER_HOSTNAME_{0}'.format(
                                self._http_request.client_ip_address_type.value
                            )
                        )
                        server_port = Configuration.get_configuration_parameter(
                            'SERVER_HTTP{0}_PORT'.format(
                                'S' if self._http_request.server.is_secure else ''
                            )
                        )

                        playlist_url = None
                        if recording.status == RecordingStatus.PERSISTED.value:
                            playlist_url = PVR.generate_vod_recording_playlist_url(
                                self._http_request.server.is_secure,
                                server_hostname,
                                server_port,
                                '{0}'.format(uuid.uuid4()),
                                recording.id,
                                Configuration.get_configuration_parameter(
                                    'SERVER_PASSWORD'
                                ),
                            )

                        self._json_api_response.content = {
                            'meta': {'application': 'IPTVProxy', 'version': VERSION},
                            'data': {
                                'type': 'recordings',
                                'id': recording.id,
                                'attributes': {
                                    'channel_name': recording.channel_name,
                                    'channel_number': recording.channel_number,
                                    'end_date_time_in_utc': '{0}'.format(
                                        recording.end_date_time_in_utc
                                    ),
                                    'playlist_url': playlist_url,
                                    'program_title': recording.program_title,
                                    'provider': recording.provider,
                                    'start_date_time_in_utc': '{0}'.format(
                                        recording.start_date_time_in_utc
                                    ),
                                    'status': recording.status,
                                },
                            },
                        }
                        self._json_api_response.status_code = requests.codes.OK
                    except RecordingNotFoundError:
                        logger.error(
                            'Error encountered processing request\n'
                            'Source IP      => %s\n'
                            'Requested path => %s\n'
                            'Error Title    => Resource not found\n'
                            'Error Message  => Recording with ID %s does not exist',
                            self._http_request.client_ip_address,
                            self._http_request.requested_path_with_query_string,
                            recording_id,
                        )

                        self._json_api_response.content = {
                            'errors': [
                                {
                                    'status': '{0}'.format(requests.codes.NOT_FOUND),
                                    'title': 'Resource not found',
                                    'field': None,
                                    'developer_message': 'Recording with ID {0} does not exist'.format(
                                        recording_id
                                    ),
                                    'user_message': 'Requested recording does not exist',
                                }
                            ]
                        }
                        self._json_api_response.status_code = requests.codes.NOT_FOUND
                    finally:
                        db_session.close()
            else:
                if self._validate_get_request_query_string():
                    server_hostname = Configuration.get_configuration_parameter(
                        'SERVER_HOSTNAME_{0}'.format(
                            self._http_request.client_ip_address_type.value
                        )
                    )
                    server_port = Configuration.get_configuration_parameter(
                        'SERVER_HTTP{0}_PORT'.format(
                            'S' if self._http_request.server.is_secure else ''
                        )
                    )

                    self._json_api_response.content = {
                        'meta': {'application': 'IPTVProxy', 'version': VERSION},
                        'data': [],
                    }

                    status = self._http_request.requested_query_string_parameters.get(
                        'status'
                    )

                    for recording in [
                        recording
                        for recording in PVR.get_recordings()
                        if status is None or status == recording.status
                    ]:
                        playlist_url = None
                        if recording.status == RecordingStatus.PERSISTED.value:
                            playlist_url = PVR.generate_vod_recording_playlist_url(
                                self._http_request.server.is_secure,
                                server_hostname,
                                server_port,
                                '{0}'.format(uuid.uuid4()),
                                recording.id,
                                Configuration.get_configuration_parameter(
                                    'SERVER_PASSWORD'
                                ),
                            )

                        self._json_api_response.content['data'].append(
                            {
                                'type': 'recordings',
                                'id': recording.id,
                                'attributes': {
                                    'channel_name': recording.channel_name,
                                    'channel_number': recording.channel_number,
                                    'end_date_time_in_utc': '{0}'.format(
                                        recording.end_date_time_in_utc
                                    ),
                                    'playlist_url': playlist_url,
                                    'program_title': recording.program_title,
                                    'provider': recording.provider,
                                    'start_date_time_in_utc': '{0}'.format(
                                        recording.start_date_time_in_utc
                                    ),
                                    'status': recording.status,
                                },
                            }
                        )

                    self._json_api_response.status_code = requests.codes.OK

        return (
            json.dumps(self._json_api_response.content, indent=4),
            self._json_api_response.status_code,
        )

    def process_post_request(self):
        if (
            self._validate_post_request_body()
            and self._validate_is_query_string_empty()
        ):
            request_body = json.loads(self._http_request.request_body)

            channel_name = (
                ProvidersController.get_provider_map_class(
                    html.unescape(
                        request_body['data']['attributes']['provider']
                    ).lower()
                )
                .epg_class()
                .get_channel_name(
                    int(request_body['data']['attributes']['channel_number'])
                )
            )
            channel_number = request_body['data']['attributes']['channel_number']
            end_date_time_in_utc = datetime.strptime(
                request_body['data']['attributes']['end_date_time_in_utc'],
                '%Y-%m-%d %H:%M:%S',
            ).replace(tzinfo=pytz.utc)
            id_ = '{0}'.format(uuid.uuid4())
            program_title = html.unescape(
                request_body['data']['attributes']['program_title']
            )
            provider = html.unescape(request_body['data']['attributes']['provider'])
            start_date_time_in_utc = datetime.strptime(
                request_body['data']['attributes']['start_date_time_in_utc'],
                '%Y-%m-%d %H:%M:%S',
            ).replace(tzinfo=pytz.utc)

            recording = Recording(
                id_,
                provider,
                channel_number,
                channel_name,
                program_title,
                start_date_time_in_utc,
                end_date_time_in_utc,
                RecordingStatus.SCHEDULED.value,
            )

            with Database.get_write_lock():
                db_session = Database.create_session()

                try:
                    PVR.add_scheduled_recording(db_session, recording)
                    db_session.commit()

                    logger.info(
                        'Scheduled recording\n'
                        'Provider          => %s\n'
                        'Channel number    => %s\n'
                        'Channel name      => %s\n'
                        'Program title     => %s\n'
                        'Start date & time => %s\n'
                        'End date & time   => %s',
                        provider,
                        channel_number,
                        channel_name,
                        program_title,
                        start_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        end_date_time_in_utc.astimezone(
                            tzlocal.get_localzone()
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                    )

                    self._json_api_response.content = {
                        'meta': {'application': 'IPTVProxy', 'version': VERSION},
                        'data': {
                            'type': 'recordings',
                            'id': id_,
                            'attributes': {
                                'channel_name': channel_name,
                                'channel_number': channel_number,
                                'end_date_time_in_utc': '{0}'.format(
                                    end_date_time_in_utc
                                ),
                                'program_title': program_title,
                                'provider': provider,
                                'start_date_time_in_utc': '{0}'.format(
                                    start_date_time_in_utc
                                ),
                                'status': 'scheduled',
                            },
                        },
                    }
                    self._json_api_response.status_code = requests.codes.CREATED
                except DuplicateRecordingError:
                    db_session.rollback()

                    logger.error(
                        'Error encountered processing request\n'
                        'Source IP      => %s\n'
                        'Requested path => %s\n'
                        'Post Data      => %s\n'
                        'Error Title    => Duplicate resource\n'
                        'Error Message  => Recording already scheduled',
                        self._http_request.client_ip_address,
                        self._http_request.requested_path_with_query_string,
                        pprint.pformat(request_body, indent=4),
                    )

                    self._json_api_response.content = {
                        'errors': [
                            {
                                'status': '{0}'.format(requests.codes.CONFLICT),
                                'field': None,
                                'title': 'Duplicate resource',
                                'developer_message': 'Recording already scheduled',
                                'user_message': 'The recording is already scheduled',
                            }
                        ]
                    }
                    self._json_api_response.status_code = requests.codes.CONFLICT
                except Exception:
                    (type_, value_, traceback_) = sys.exc_info()
                    logger.error(
                        '\n'.join(traceback.format_exception(type_, value_, traceback_))
                    )

                    db_session.rollback()
                finally:
                    db_session.close()

        return (
            json.dumps(self._json_api_response.content, indent=4),
            self._json_api_response.status_code,
        )
