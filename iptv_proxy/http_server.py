import base64
import binascii
import email.utils
import http.client
import json
import logging
import pprint
import re
import ssl
import sys
import traceback
import urllib.parse
import uuid
import zlib
from datetime import datetime
from datetime import timedelta
from gzip import GzipFile
from http.cookies import CookieError
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from io import BytesIO
from socketserver import ThreadingMixIn
from threading import Thread

import pytz
import requests
import tzlocal

from .cache import IPTVProxyCacheManager
from .configuration import IPTVProxyConfiguration
from .constants import DEFAULT_STREAMING_PROTOCOL
from .db import IPTVProxyDatabase
from .db import IPTVProxySQL
from .enums import IPTVProxyCacheResponseType
from .enums import IPTVProxyIPAddressType
from .epg import IPTVProxyEPG
from .html_template_engine import IPTVProxyHTMLTemplateEngine
from .json_api import IPTVProxyConfigurationJSONAPI
from .json_api import IPTVProxyRecordingsJSONAPI
from .providers.smooth_streams.api import SmoothStreams
from .providers.vader_streams.api import VaderStreams
from .proxy import IPTVProxy
from .recorder import IPTVProxyPVR
from .security import IPTVProxySecurityManager
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class IPTVProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    _allow_insecure_lan_connections = True
    _allow_insecure_wan_connections = False
    _lan_connections_require_credentials = False
    _wan_connections_require_credentials = True

    @classmethod
    def initialize(cls):
        deleted_http_sessions_log_message = []
        loaded_http_sessions_log_message = []

        do_commit_transaction = False

        db = IPTVProxyDatabase()
        http_session_records = IPTVProxySQL.query_http_sessions(db)

        for http_session_record in http_session_records:
            current_date_time_in_utc = datetime.now(pytz.utc)

            if current_date_time_in_utc >= datetime.strptime(http_session_record['expiry_date_time_in_utc'],
                                                             '%Y-%m-%d %H:%M:%S%z'):
                IPTVProxySQL.delete_http_session_by_id(db, http_session_record['id'])
                do_commit_transaction = True

                deleted_http_sessions_log_message.append(
                    'Session ID         => {0}\n'
                    'Client IP address  => {1}\n'
                    'Browser user agent => {2}\n'
                    'Expired on         => {3}\n'.format(http_session_record['id'],
                                                         http_session_record['client_ip_address'],
                                                         http_session_record['user_agent'],
                                                         datetime.strptime(
                                                             http_session_record['expiry_date_time_in_utc'],
                                                             '%Y-%m-%d %H:%M:%S%z').astimezone(
                                                             tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z')))
            else:
                loaded_http_sessions_log_message.append(
                    'Session ID         => {0}\n'
                    'Client IP address  => {1}\n'
                    'Browser user agent => {2}\n'
                    'Expires on         => {3}\n'.format(http_session_record['id'],
                                                         http_session_record['client_ip_address'],
                                                         http_session_record['user_agent'],
                                                         datetime.strptime(
                                                             http_session_record['expiry_date_time_in_utc'],
                                                             '%Y-%m-%d %H:%M:%S%z').astimezone(
                                                             tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z')))

        if do_commit_transaction:
            db.commit()
        db.close_connection()

        if deleted_http_sessions_log_message:
            deleted_http_sessions_log_message.insert(0, 'Deleted HTTP server session{0}\n'.format(
                's' if len(deleted_http_sessions_log_message) > 1 else ''))

            logger.debug('\n'.join(deleted_http_sessions_log_message).strip())

        if loaded_http_sessions_log_message:
            loaded_http_sessions_log_message.insert(0, 'Loaded HTTP server session{0}\n'.format(
                's' if len(loaded_http_sessions_log_message) > 1 else ''))

            logger.debug('\n'.join(loaded_http_sessions_log_message).strip())

    @classmethod
    def purge_http_sessions(cls):
        db = IPTVProxyDatabase()
        IPTVProxySQL.delete_http_sessions(db)
        db.commit()
        db.close_connection()

    @classmethod
    def set_allow_insecure_lan_connections(cls, allow_insecure_lan_connections):
        cls._allow_insecure_lan_connections = allow_insecure_lan_connections

    @classmethod
    def set_allow_insecure_wan_connections(cls, allow_insecure_wan_connections):
        cls._allow_insecure_wan_connections = allow_insecure_wan_connections

    @classmethod
    def set_lan_connections_require_credentials(cls, lan_connections_require_credentials):
        cls._lan_connections_require_credentials = lan_connections_require_credentials

    @classmethod
    def set_wan_connections_require_credentials(cls, wan_connections_require_credentials):
        cls._wan_connections_require_credentials = wan_connections_require_credentials

    def _authenticate(self, password_to_authenticate):
        server_password = IPTVProxyConfiguration.get_configuration_parameter('SERVER_PASSWORD')

        if server_password != password_to_authenticate:
            self._send_http_error(requests.codes.UNAUTHORIZED, 'Invalid password provided.')

            return False

        return True

    def _authorization_required(self):
        if self._client_ip_address_type == IPTVProxyIPAddressType.PUBLIC and not \
                IPTVProxyHTTPRequestHandler._wan_connections_require_credentials:
            return False
        elif self._client_ip_address_type != IPTVProxyIPAddressType.PUBLIC and not \
                IPTVProxyHTTPRequestHandler._lan_connections_require_credentials:
            return False

        return True

    def _create_response_headers(self):
        if self.command == 'OPTIONS':
            self._response_headers['Access-Control-Allow-Methods'] = ['DELETE, GET, OPTIONS, PATCH, POST']

        self._response_headers['Access-Control-Allow-Origin'] = ['*']

        if self._response_content_encoding:
            self._response_headers['Content-Encoding'] = [self._response_content_encoding]

        if self._response_content:
            if type(self._response_content) != bytes:
                self._response_headers['Content-Length'] = ['{0}'.format(len(self._response_content.encode()))]
            else:
                self._response_headers['Content-Length'] = ['{0}'.format(len(self._response_content))]
            self._response_headers['Content-Type'] = [self._response_content_type]
        elif self._response_content_generator:
            self._response_headers['Content-Type'] = [self._response_content_type]
            self._response_headers['Transfer-Encoding'] = ['chunked']

        if self._response_status_code == requests.codes.FOUND:
            self._response_headers['Location'] = ['/index.html']

        if self._cookies:
            self._response_headers['Set-Cookie'] = []

            for cookie in sorted(self._cookies):
                if self._cookies[cookie]['expires']:
                    self._response_headers['Set-Cookie'].append(self._cookies[cookie].output(header='').strip())

    def _create_http_session_cookie(self, iptv_proxy_http_session):
        http_session_id_cookie_expires = email.utils.format_datetime(iptv_proxy_http_session.expiry_date_time_in_utc)

        self._cookies['http_session_id'] = iptv_proxy_http_session.id
        self._cookies['http_session_id']['expires'] = http_session_id_cookie_expires
        self._cookies['http_session_id']['httponly'] = True
        self._cookies['http_session_id']['path'] = '/index.html'

    def _create_settings_cookies(self):
        settings_cookie_expires = self._cookies.get('settings_cookie_expires')

        if settings_cookie_expires is None:
            current_date_time_in_utc = datetime.now(pytz.utc)
            settings_cookie_expiry_date_time_in_utc = (current_date_time_in_utc + timedelta(days=366)).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0)
            settings_cookie_expires = email.utils.format_datetime(settings_cookie_expiry_date_time_in_utc)

            self._cookies['settings_cookie_expires'] = settings_cookie_expires
            self._cookies['settings_cookie_expires']['expires'] = settings_cookie_expires
            self._cookies['settings_cookie_expires']['path'] = '/index.html'

        if self._cookies.get('guide_number_of_days') is None:
            self._cookies['guide_number_of_days'] = '1'
        self._cookies['guide_number_of_days']['expires'] = settings_cookie_expires
        self._cookies['guide_number_of_days']['path'] = '/index.html'

        if self._cookies.get('guide_provider') is None:
            if self._providers:
                self._cookies['guide_provider'] = self._providers[sorted(
                    self._providers)[0]]['api']().__class__.__name__

        if self._cookies.get('guide_provider') is not None:
            self._cookies['guide_provider']['expires'] = settings_cookie_expires
            self._cookies['guide_provider']['path'] = '/index.html'

            if self._cookies.get('guide_group') is None:
                provider = self._providers[self._cookies.get('guide_provider').value.lower()]
                groups = provider['epg'].get_groups()

                if groups:
                    self._cookies['guide_group'] = sorted(groups)[0]

        if self._cookies.get('guide_group') is not None:
            self._cookies['guide_group']['expires'] = settings_cookie_expires
            self._cookies['guide_group']['path'] = '/index.html'

        if self._cookies.get('streaming_protocol') is None:
            self._cookies['streaming_protocol'] = DEFAULT_STREAMING_PROTOCOL
        self._cookies['streaming_protocol']['expires'] = settings_cookie_expires
        self._cookies['streaming_protocol']['path'] = '/index.html'

    def _get_json_request_password(self):
        authorization = self.headers.get('Authorization')

        if authorization:
            match = re.match(r'\ABasic '
                             r'((?:[A-Za-z0-9+/]{4}){2,}'
                             r'(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==))\Z',
                             authorization)

            if match:
                try:
                    return base64.b64decode(match.group(1)).decode()[1:]
                except binascii.Error:
                    pass

        return None

    def _handle_internal_server_error(self):
        (status, value_, traceback_) = sys.exc_info()

        logger.error('HTTP error {0} encountered requesting {1} for {2}/{3}\n'
                     '{4}'.format(requests.codes.INTERNAL_SERVER_ERROR,
                                  self._requested_path_with_query_string,
                                  self._client_ip_address,
                                  self._client_uuid,
                                  '\n'.join(traceback.format_exception(status, value_, traceback_))))

        self._send_http_error(requests.codes.INTERNAL_SERVER_ERROR,
                              'The server encountered an unexpected error and could not complete the request.')

    def _handle_invalid_query_string(self):
        logger.error('{0} requested from {1}/{2} has an invalid query string'.format(
            self._requested_path_with_query_string,
            self._client_ip_address,
            self._client_uuid))

        self._send_http_error(requests.codes.BAD_REQUEST, 'The server could not understand the request.')

    def _handle_not_found_error(self):
        logger.error('HTTP error {0} encountered requesting {1} for {2}/{3}'.format(
            requests.codes.NOT_FOUND,
            self._requested_path_with_query_string,
            self._client_ip_address,
            self._client_uuid))

        self._send_http_error(requests.codes.NOT_FOUND,
                              'The requested URL /{0} was not found on this server.'.format(
                                  '/'.join(self._requested_path_tokens)))

    def _handle_service_unavailable_error(self, class_):
        logger.error('HTTP error {0} encountered requesting {1} for {2}/{3}'.format(
            requests.codes.SERVICE_UNAVAILABLE,
            self._requested_path_with_query_string,
            self._client_ip_address,
            self._client_uuid))

        self._send_http_error(requests.codes.SERVICE_UNAVAILABLE,
                              'The requested URL /{0} is unavailable.'
                              '            <br/>'
                              '            The server is not configured with a valid {1} provider.'.format(
                                  '/'.join(self._requested_path_tokens),
                                  class_.__name__))

    def _initialize(self):
        self._client_ip_address = self.client_address[0]
        self._client_port_number = self.client_address[1]
        self._client_ip_address_type = IPTVProxyUtility.determine_ip_address_type(self._client_ip_address)
        self._user_agent = self.headers.get('User-Agent')
        self._client_uuid = uuid.uuid3(uuid.NAMESPACE_OID, '{0}@{1}'.format(self._user_agent,
                                                                            self._client_ip_address))
        self._cookies = SimpleCookie()
        try:
            self._cookies.load(self.headers.get('Cookie'))
        except (AttributeError, CookieError):
            pass

        self._do_gzip_response_content = 'gzip' in self.headers.get('Accept-Encoding', '')

        self._requested_path_with_query_string = urllib.parse.unquote(self.path)
        self._requested_url_components = urllib.parse.urlparse(self.path)
        self._requested_query_string_parameters = dict(urllib.parse.parse_qsl(self._requested_url_components.query))
        self._requested_path_tokens = [requested_path_token
                                       for requested_path_token in self._requested_url_components.path[1:].split('/')]
        self._requested_path_tokens_length = len(self._requested_path_tokens)

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            self._request_body = self.rfile.read(content_length).decode()
        else:
            self._request_body = None

        self._response_status_code = None
        self._response_headers = {}
        self._response_content = None
        self._response_content_generator = None
        self._response_content_type = None
        self._response_content_encoding = None

        self._providers = IPTVProxyConfiguration.get_providers()

        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug('{0}{1} requested from {2}/{3}\n'
                         'Request type => {4}'.format(self.headers.get('Host'),
                                                      self._requested_path_with_query_string,
                                                      self._client_ip_address,
                                                      self._client_uuid,
                                                      self.command))

    def _is_logged_in(self):
        if self._authorization_required():
            http_session_id_cookie = self._cookies.get('http_session_id')

            if http_session_id_cookie is None:
                logged_in = False
            else:
                http_session_id = http_session_id_cookie.value

                do_commit_transaction = False

                db = IPTVProxyDatabase()
                http_session_records = IPTVProxySQL.query_http_session_by_id(db, http_session_id)

                if not http_session_records:
                    logged_in = False
                else:
                    iptv_proxy_http_session = IPTVProxyHTTPSession.createFromHTTPSessionRecord(http_session_records[0])

                    if datetime.now(pytz.utc) > iptv_proxy_http_session.expiry_date_time_in_utc or \
                            self._client_ip_address != iptv_proxy_http_session.client_ip_address or \
                            self._user_agent != iptv_proxy_http_session.user_agent:
                        logged_in = False

                        IPTVProxySQL.delete_http_session_by_id(db, iptv_proxy_http_session.id)
                        do_commit_transaction = True
                    else:
                        logged_in = True

                        iptv_proxy_http_session.last_access_date_time_in_utc = datetime.now(pytz.utc)

                if do_commit_transaction:
                    db.commit()
                db.close_connection()
        else:
            logged_in = True

        return logged_in

    def _log_request(self):
        if self.headers:
            header_to_log = \
                '[Header]\n' \
                '========\n{0}\n\n'.format('\n'.join(
                    ['{0:32} => {1!s}'.format(header, self.headers[header])
                     for header in sorted(self.headers)]))
        else:
            header_to_log = ''

        if self._requested_query_string_parameters:
            query_parameters_to_log = \
                '[Query Parameters]\n' \
                '==================\n{0}\n'.format('\n'.join(
                    ['{0:32} => {1!s}'.format(parameter, self._requested_query_string_parameters[parameter])
                     for parameter in sorted(self._requested_query_string_parameters)]))
        else:
            query_parameters_to_log = ''

        if self._request_body:
            try:
                content_to_log = '[Content]\n' \
                                 '=========\n{0}'.format(pprint.pformat(json.loads(self._request_body)))
            except (json.JSONDecodeError, TypeError):
                content_to_log = '[Content]\n' \
                                 '=========\n{0}'.format(self._request_body)
        else:
            content_to_log = ''

        # noinspection PyUnresolvedReferences
        logger.trace(
            'Request\n'
            '[Source]\n'
            '========\n{0}\n\n'
            '[Method]\n'
            '[======]\n{1}\n\n'
            '[URL]\n'
            '=====\n{2}\n\n'
            '{3}{4}{5}'.format(self._client_ip_address,
                               self.command,
                               'http{0}://{1}{2}'.format('s' if self.server.is_secure else '',
                                                         self.headers.get('Host'),
                                                         self.path),
                               header_to_log,
                               query_parameters_to_log,
                               content_to_log))

    def _screen_request(self, password_to_authenticate):
        if self._secure_transport_satisfied():
            if self._authorization_required():
                return self._authenticate(password_to_authenticate)
            else:
                return True
        else:
            return False

    def _secure_transport_satisfied(self):
        secure_transport_satisfied = True

        if self._client_ip_address_type == IPTVProxyIPAddressType.PUBLIC:
            if not IPTVProxyHTTPRequestHandler._allow_insecure_wan_connections and not self.server.is_secure:
                secure_transport_satisfied = False
        else:
            if not IPTVProxyHTTPRequestHandler._allow_insecure_lan_connections and not self.server.is_secure:
                secure_transport_satisfied = False

        if not secure_transport_satisfied:
            self._send_http_error(requests.codes.FORBIDDEN,
                                  'The requested resource can only be processed over a secure channel (HTTPS).'
                                  '            <br/>'
                                  '            <a href={0}>{0}</a>'.format('https://{0}:{1}{2}'.format(
                                      self.headers.get('Host').split(':')[0],
                                      IPTVProxyConfiguration.get_configuration_parameter('SERVER_HTTPS_PORT'),
                                      self.path)))

        return secure_transport_satisfied

    def _send_http_error(self, http_error_code, http_error_details):
        self._response_content = IPTVProxyHTMLTemplateEngine.render_errors_template(
            http_error_code,
            http.client.responses[http_error_code],
            http_error_details)
        self._response_status_code = http_error_code
        self._response_content_type = 'text/html; charset=utf-8'
        self._send_http_response(do_log_response_content=False)

    def _send_http_response(self, do_log_response_content=True):
        self.send_response(self._response_status_code)

        response_content_to_log = self._response_content

        if self._do_gzip_response_content:
            self._response_content_encoding = 'gzip'

            if self._response_content:
                in_memory_bytes_buffer = BytesIO()

                with GzipFile(fileobj=in_memory_bytes_buffer, mode='w') as gzip_file:
                    if type(self._response_content) != bytes:
                        # noinspection PyUnresolvedReferences
                        gzip_file.write(self._response_content.encode())
                    else:
                        gzip_file.write(self._response_content)

                self._response_content = in_memory_bytes_buffer.getvalue()

        self._create_response_headers()

        headers = []
        if self._response_headers:
            for header_key in sorted(self._response_headers):
                for header_value in self._response_headers[header_key]:
                    self.send_header(header_key, header_value)
                    headers.append('{0:32} => {1!s}'.format(header_key, header_value))
        self.end_headers()

        # noinspection PyUnresolvedReferences
        logger.trace(
            'Response\n'
            '[Destination]\n'
            '=============\n'
            '{0}{1}\n\n'
            '[Method]\n'
            '[======]\n'
            '{2}\n\n'
            '[URL]\n'
            '=====\n'
            '{3}\n\n'
            '[Status Code]\n'
            '=============\n'
            '{4}\n\n'
            '{5}'
            '{6}'.format(self._client_ip_address,
                         '/{0}'.format(self._client_uuid) if self._client_uuid else '',
                         self.command,
                         'http{0}://{1}{2}'.format('s' if self.server.is_secure else '',
                                                   self.headers.get('Host'),
                                                   self._requested_path_with_query_string),
                         self._response_status_code,
                         '[Header]\n'
                         '========\n'
                         '{0}\n\n'.format('\n'.join(sorted(headers))) if headers else '',
                         '[Content]\n'
                         '=========\n'
                         '{0}\n'.format(
                             response_content_to_log) if do_log_response_content and response_content_to_log else ''))

        if self._response_content:
            if type(self._response_content) != bytes:
                # noinspection PyUnresolvedReferences
                self.wfile.write(self._response_content.encode())
            else:
                self.wfile.write(self._response_content)
        elif self._response_content_generator:
            if self._do_gzip_response_content:
                gzip_compressor = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS + 16, zlib.DEF_MEM_LEVEL, 0)

                for generated_response_content in self._response_content_generator():
                    gzipped_data = gzip_compressor.compress(generated_response_content.encode())

                    if gzipped_data:
                        self.wfile.write('{0:X}\r\n'.format(len(gzipped_data)).encode())
                        self.wfile.write(gzipped_data)
                        self.wfile.write('\r\n'.encode())

                gzipped_data = gzip_compressor.flush()
                self.wfile.write('{0:X}\r\n'.format(len(gzipped_data)).encode())
                self.wfile.write(gzipped_data)
                self.wfile.write('\r\n'.encode())

                self.wfile.write('0\r\n\r\n'.encode())
            else:
                for generated_response_content in self._response_content_generator():
                    if type(generated_response_content) != bytes:
                        generated_response_content = generated_response_content.encode()

                    self.wfile.write('{0:X}\r\n'.format(len(generated_response_content)).encode())
                    self.wfile.write(generated_response_content)
                    self.wfile.write('\r\n'.encode())

                self.wfile.write('0\r\n\r\n'.encode())

    # noinspection PyPep8Naming
    def do_DELETE(self):
        self._initialize()
        self._log_request()

        requested_path_not_found = False

        # noinspection PyBroadException
        try:
            if self._requested_path_tokens_length == 2 and \
                    self._requested_path_tokens[0].lower() == 'recordings' and \
                    re.match(r'\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z',
                             self._requested_path_tokens[1].lower()):
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = IPTVProxyRecordingsJSONAPI(self).process_delete_request()
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            else:
                requested_path_not_found = True

            if requested_path_not_found:
                self._handle_not_found_error()
        except Exception:
            self._handle_internal_server_error()

    # noinspection PyPep8Naming
    def do_GET(self):
        self._initialize()
        self._log_request()

        invalid_query_string = False
        requested_path_not_found = False

        # noinspection PyBroadException
        try:
            if re.match(r'\A(index.htm)?\Z', self._requested_path_tokens[0].lower()) and \
                    self._requested_path_tokens_length == 1:
                self._response_status_code = requests.codes.FOUND
                self._send_http_response()
            if re.match(r'\A(index.html)\Z', self._requested_path_tokens[0].lower()) and \
                    self._requested_path_tokens_length == 1:
                refresh_epg_parameter_value = self._requested_query_string_parameters.get('refresh_epg')

                if self._secure_transport_satisfied():
                    if self._is_logged_in():
                        if not set(self._requested_query_string_parameters) - {'refresh_epg'}:
                            self._create_settings_cookies()

                            guide_number_of_days_cookie_value = self._cookies.get('guide_number_of_days').value
                            guide_provider_cookie_value = urllib.parse.unquote(
                                self._cookies.get('guide_provider').value)
                            guide_group_cookie_value = urllib.parse.unquote(self._cookies.get('guide_group').value)

                            if refresh_epg_parameter_value:
                                self._response_content = IPTVProxyHTMLTemplateEngine.render_guide_div_template(
                                    self.server.is_secure,
                                    self._authorization_required(),
                                    self._client_ip_address,
                                    self._client_uuid,
                                    guide_number_of_days_cookie_value,
                                    guide_provider_cookie_value,
                                    guide_group_cookie_value,
                                    self._providers)
                            else:
                                streaming_protocol_cookie_value = self._cookies.get('streaming_protocol').value

                                self._response_content = IPTVProxyHTMLTemplateEngine.render_index_template(
                                    self.server.is_secure,
                                    self._authorization_required(),
                                    self._client_ip_address,
                                    self._client_uuid,
                                    guide_number_of_days_cookie_value,
                                    guide_provider_cookie_value,
                                    guide_group_cookie_value,
                                    streaming_protocol_cookie_value,
                                    self._providers)

                            self._response_status_code = requests.codes.OK
                            self._response_content_type = 'text/html; charset=utf-8'
                            self._send_http_response(do_log_response_content=False)
                        else:
                            invalid_query_string = True
                    else:
                        if not set(self._requested_query_string_parameters) - {'refresh_epg'}:
                            self._response_content = IPTVProxyHTMLTemplateEngine.render_login_template()

                            self._response_status_code = requests.codes.OK
                            self._response_content_type = 'text/html; charset=utf-8'
                            self._send_http_response(do_log_response_content=False)
                        else:
                            invalid_query_string = True
            elif re.match(r'\A(.+)\.png\Z', self._requested_path_tokens[0].lower()) \
                    and self._requested_path_tokens_length == 1:
                http_token_parameter_value = self._requested_query_string_parameters.get('http_token')

                if self._screen_request(http_token_parameter_value):
                    if not set(self._requested_query_string_parameters) - {'http_token'}:
                        self._do_gzip_response_content = False

                        try:
                            self._response_content = IPTVProxyUtility.read_png_file(self._requested_path_tokens[0],
                                                                                    in_base_64=False)
                            self._response_status_code = requests.codes.OK
                            self._response_content_type = 'image/png'
                            self._send_http_response(do_log_response_content=False)
                        except OSError:
                            requested_path_not_found = True
                    else:
                        invalid_query_string = True
            elif self._requested_path_tokens[0].lower() == 'configuration' and self._requested_path_tokens_length == 1:
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = IPTVProxyConfigurationJSONAPI(self).process_get_request()
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            elif self._requested_path_tokens[0].lower() == 'live' and self._requested_path_tokens_length == 2:
                http_token_parameter_value = self._requested_query_string_parameters.get('http_token')

                if self._requested_path_tokens[1].lower() == 'epg.xml':
                    if self._screen_request(http_token_parameter_value):
                        if not set(self._requested_query_string_parameters) - {'http_token',
                                                                               'number_of_days'}:
                            self._do_gzip_response_content = False

                            number_of_days_parameter_value = self._requested_query_string_parameters.get(
                                'number_of_days',
                                1)

                            try:
                                self._response_content_generator = IPTVProxyEPG.generate_epg_xml_file(
                                    self.server.is_secure,
                                    self._authorization_required(),
                                    self._client_ip_address,
                                    self._providers,
                                    number_of_days_parameter_value)
                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'application/xml; charset=utf-8'
                                self._send_http_response(do_log_response_content=False)
                            except requests.exceptions.HTTPError as e:
                                self._send_http_error(e.response.status_code, '')
                        else:
                            invalid_query_string = True
                elif self._requested_path_tokens[1].lower() == 'playlist.m3u8':
                    if self._screen_request(http_token_parameter_value):
                        providers_query_string_parameters = set()

                        for query_string_parameter in self._requested_query_string_parameters:
                            if query_string_parameter.endswith('_protocol') or query_string_parameter.endswith('_type'):
                                providers_query_string_parameters.add(query_string_parameter)

                        if not set(self._requested_query_string_parameters) - ({'client_uuid',
                                                                                'http_token',
                                                                                'protocol',
                                                                                'type'} |
                                                                               providers_query_string_parameters):
                            try:
                                self._response_content = IPTVProxy.generate_playlist_m3u8(
                                    self.server.is_secure,
                                    self._client_ip_address,
                                    self._client_uuid,
                                    self._requested_query_string_parameters,
                                    self._providers)
                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'application/vnd.apple.mpegurl'
                                self._send_http_response()
                            except requests.exceptions.HTTPError as e:
                                self._send_http_error(e.response.status_code, '')
                        else:
                            invalid_query_string = True
                else:
                    requested_path_not_found = True
            elif self._requested_path_tokens[0].lower() == 'live' and self._requested_path_tokens_length == 3:
                if self._requested_path_tokens[1].lower() in self._providers:
                    provider = self._providers[self._requested_path_tokens[1].lower()]

                    channel_number_parameter_value = self._requested_query_string_parameters.get('channel_number')
                    client_uuid_parameter_value = self._requested_query_string_parameters.get('client_uuid')
                    http_token_parameter_value = self._requested_query_string_parameters.get('http_token')

                    if client_uuid_parameter_value:
                        self._client_uuid = client_uuid_parameter_value

                    if self._requested_path_tokens[2].lower().endswith('.ts'):
                        if self._screen_request(http_token_parameter_value):
                            self._do_gzip_response_content = False

                            try:
                                do_download_file = True

                                if IPTVProxyCacheManager.get_do_cache_downloaded_segments():
                                    cache_response = IPTVProxyCacheManager.query_cache(
                                        channel_number_parameter_value,
                                        self._requested_path_tokens[2].lower())

                                    if cache_response.response_type == IPTVProxyCacheResponseType.HARD_HIT:
                                        do_download_file = False

                                        self._response_content = cache_response.entry.segment_file_content
                                    elif cache_response.response_type == IPTVProxyCacheResponseType.SOFT_HIT:
                                        cache_response.entry.primed_event.wait(5)

                                        cache_response = IPTVProxyCacheManager.query_cache(
                                            channel_number_parameter_value,
                                            self._requested_path_tokens[2].lower())

                                        if cache_response.response_type == IPTVProxyCacheResponseType.HARD_HIT:
                                            do_download_file = False

                                            self._response_content = cache_response.entry.segment_file_content
                                        else:
                                            do_download_file = True
                                    else:
                                        do_download_file = True

                                if do_download_file:
                                    self._response_content = provider['api'].download_ts_file(
                                        self._client_ip_address,
                                        self._client_uuid,
                                        self._requested_url_components.path,
                                        self._requested_query_string_parameters)

                                    if IPTVProxyCacheManager.get_do_cache_downloaded_segments():
                                        IPTVProxyCacheManager.update_cache(channel_number_parameter_value,
                                                                           self._requested_path_tokens[2].lower(),
                                                                           self._response_content)

                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'video/m2ts'
                                self._send_http_response(do_log_response_content=False)
                            except requests.exceptions.HTTPError as e:
                                self._send_http_error(e.response.status_code, '')
                    elif self._requested_path_tokens[2].lower() == 'chunks.m3u8':
                        if self._screen_request(http_token_parameter_value):
                            try:
                                self._response_content = provider['api'].download_chunks_m3u8(
                                    self._client_ip_address,
                                    self._client_uuid,
                                    self._requested_url_components.path,
                                    self._requested_query_string_parameters)
                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'application/vnd.apple.mpegurl'
                                self._send_http_response()
                            except requests.exceptions.HTTPError as e:
                                self._send_http_error(e.response.status_code, '')
                    elif self._requested_path_tokens[2].lower() == 'epg.xml':
                        if self._screen_request(http_token_parameter_value):
                            if not set(self._requested_query_string_parameters) - {'http_token',
                                                                                   'number_of_days'}:
                                self._do_gzip_response_content = False

                                number_of_days_parameter_value = self._requested_query_string_parameters.get(
                                    'number_of_days',
                                    1)

                                try:
                                    self._response_content_generator = provider['epg'].generate_epg_xml_file(
                                        self.server.is_secure,
                                        self._authorization_required(),
                                        self._client_ip_address,
                                        number_of_days_parameter_value)
                                    self._response_status_code = requests.codes.OK
                                    self._response_content_type = 'application/xml; charset=utf-8'
                                    self._send_http_response(do_log_response_content=False)
                                except requests.exceptions.HTTPError as e:
                                    self._send_http_error(e.response.status_code, '')
                            else:
                                invalid_query_string = True
                    elif self._requested_path_tokens[2].lower() == 'playlist.m3u8':
                        if self._screen_request(http_token_parameter_value):
                            do_generate_playlist_m3u8 = False

                            if self._requested_query_string_parameters:
                                if channel_number_parameter_value:
                                    if not set(self._requested_query_string_parameters) - {'channel_number',
                                                                                           'client_uuid',
                                                                                           'http_token',
                                                                                           'protocol'}:
                                        logger.info('{0} requested from {1}/{2}'.format(
                                            provider['epg'].get_channel_name(int(channel_number_parameter_value)),
                                            self._client_ip_address,
                                            self._client_uuid))

                                        try:
                                            self._response_content = provider['api'].download_playlist_m3u8(
                                                self._client_ip_address,
                                                self._client_uuid,
                                                self._requested_url_components.path,
                                                self._requested_query_string_parameters)
                                            self._response_status_code = requests.codes.OK
                                            self._response_content_type = 'application/vnd.apple.mpegurl'
                                            self._send_http_response()
                                        except requests.exceptions.HTTPError as e:
                                            self._send_http_error(e.response.status_code, '')
                                    else:
                                        invalid_query_string = True
                                elif not set(self._requested_query_string_parameters) - {'client_uuid',
                                                                                         'http_token',
                                                                                         'protocol',
                                                                                         'type'}:
                                    do_generate_playlist_m3u8 = True
                                else:
                                    invalid_query_string = True
                            else:
                                do_generate_playlist_m3u8 = True

                            if do_generate_playlist_m3u8:
                                try:
                                    self._response_content = provider['api'].generate_playlist_m3u8(
                                        self.server.is_secure,
                                        self._client_ip_address,
                                        self._client_uuid,
                                        self._requested_query_string_parameters)
                                    self._response_status_code = requests.codes.OK
                                    self._response_content_type = 'application/vnd.apple.mpegurl'
                                    self._send_http_response()
                                except requests.exceptions.HTTPError as e:
                                    self._send_http_error(e.response.status_code, '')
                    else:
                        requested_path_not_found = True
                else:
                    if self._requested_path_tokens[1].lower() == 'smoothstreams':
                        self._handle_service_unavailable_error(SmoothStreams)
                    elif self._requested_path_tokens[1].lower() == 'vaderstreams':
                        self._handle_service_unavailable_error(VaderStreams)
                    else:
                        requested_path_not_found = True
            elif self._requested_path_tokens[0].lower() == 'recordings':
                if self._requested_path_tokens_length == 1:
                    if self._screen_request(self._get_json_request_password()):
                        (self._response_content,
                         self._response_status_code) = IPTVProxyRecordingsJSONAPI(self).process_get_request()
                elif re.match(r'\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z',
                              self._requested_path_tokens[1].lower()) and self._requested_path_tokens_length == 2:
                    if self._screen_request(self._get_json_request_password()):
                        (self._response_content,
                         self._response_status_code) = IPTVProxyRecordingsJSONAPI(self).process_get_request(
                            self._requested_path_tokens[1].lower())
                else:
                    requested_path_not_found = True

                if not requested_path_not_found:
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            elif self._requested_path_tokens[0].lower() == 'vod' and self._requested_path_tokens_length == 2:
                client_uuid_parameter_value = self._requested_query_string_parameters.get('client_uuid')
                http_token_parameter_value = self._requested_query_string_parameters.get('http_token')
                program_title = self._requested_query_string_parameters.get('program_title')

                if client_uuid_parameter_value:
                    self._client_uuid = client_uuid_parameter_value

                if self._requested_path_tokens[1].lower().endswith('.ts'):
                    if self._screen_request(http_token_parameter_value):
                        if not set(self._requested_query_string_parameters) - {'client_uuid',
                                                                               'http_token',
                                                                               'program_title'}:
                            self._do_gzip_response_content = False

                            try:
                                self._response_content = IPTVProxyPVR.read_ts_file(
                                    self._requested_path_with_query_string,
                                    program_title)
                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'video/m2ts'
                                self._send_http_response(do_log_response_content=False)
                            except OSError:
                                requested_path_not_found = True
                        else:
                            invalid_query_string = True
                elif self._requested_path_tokens[1].lower() == 'playlist.m3u8':
                    if self._screen_request(http_token_parameter_value):
                        if program_title:
                            if not set(self._requested_query_string_parameters) - {'client_uuid',
                                                                                   'http_token',
                                                                                   'program_title'}:
                                logger.info('{0} requested from {1}/{2}'.format(
                                    base64.urlsafe_b64decode(program_title.encode()).decode(),
                                    self._client_ip_address,
                                    self._client_uuid))

                                try:
                                    self._response_content = IPTVProxyPVR.read_vod_playlist_m3u8(
                                        self._client_uuid,
                                        program_title,
                                        http_token_parameter_value)
                                    self._response_status_code = requests.codes.OK
                                    self._response_content_type = 'application/vnd.apple.mpegurl'
                                    self._send_http_response()
                                except OSError:
                                    requested_path_not_found = True
                            else:
                                invalid_query_string = True
                        else:
                            if not set(self._requested_query_string_parameters) - {'client_uuid',
                                                                                   'http_token'}:
                                self._response_content = IPTVProxyPVR.generate_vod_playlist_m3u8(
                                    self.server.is_secure,
                                    self._client_ip_address,
                                    self._client_uuid,
                                    http_token_parameter_value)
                                if self._response_content:
                                    self._response_status_code = requests.codes.OK
                                    self._response_content_type = 'application/vnd.apple.mpegurl'
                                    self._send_http_response()
                                else:
                                    requested_path_not_found = True
                            else:
                                invalid_query_string = True
                else:
                    requested_path_not_found = True
            else:
                requested_path_not_found = True

            if invalid_query_string:
                self._handle_invalid_query_string()
            elif requested_path_not_found:
                self._handle_not_found_error()
        except Exception:
            self._handle_internal_server_error()

    # noinspection PyPep8Naming
    def do_OPTIONS(self):
        self._initialize()
        self._log_request()

        self._response_status_code = requests.codes.OK
        self._send_http_response()

    # noinspection PyPep8Naming
    def do_PATCH(self):
        self._initialize()
        self._log_request()

        requested_path_not_found = False

        # noinspection PyBroadException
        try:
            if self._requested_path_tokens_length == 1 and self._requested_path_tokens[0].lower() == 'configuration':
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = IPTVProxyConfigurationJSONAPI(self).process_patch_request()
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            else:
                requested_path_not_found = True

            if requested_path_not_found:
                self._handle_not_found_error()
        except Exception:
            self._handle_internal_server_error()

    # noinspection PyPep8Naming
    def do_POST(self):
        self._initialize()
        self._log_request()

        requested_path_not_found = False

        # noinspection PyBroadException
        try:
            if re.match(r'\A(index.html)\Z', self._requested_path_tokens[0].lower()) and \
                    self._requested_path_tokens_length == 1:
                bad_post_index_html_request = False

                if self._request_body:
                    match = re.match(r'\ApasswordInput=(.*)\Z', self._request_body)

                    if match:
                        password = urllib.parse.unquote(match.group(1))

                        if self._authenticate(password):
                            iptv_proxy_http_session = IPTVProxyHTTPSession.create(self._client_ip_address,
                                                                                  self._user_agent)
                            self._create_http_session_cookie(iptv_proxy_http_session)

                            db = IPTVProxyDatabase()
                            IPTVProxySQL.insert_http_session(db, iptv_proxy_http_session)
                            db.commit()
                            db.close_connection()

                            self._response_status_code = requests.codes.FOUND
                            self._send_http_response()
                    else:
                        bad_post_index_html_request = True
                else:
                    bad_post_index_html_request = True

                if bad_post_index_html_request:
                    self._send_http_error(requests.codes.BAD_REQUEST, 'The server could not understand the request.')
            elif self._requested_path_tokens_length == 1 and self._requested_path_tokens[0].lower() == 'recordings':
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = IPTVProxyRecordingsJSONAPI(self).process_post_request()
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            else:
                requested_path_not_found = True

            if requested_path_not_found:
                self._handle_not_found_error()
        except Exception:
            self._handle_internal_server_error()

    def log_message(self, format_, *args):
        return

    @property
    def client_ip_address(self):
        return self._client_ip_address

    @property
    def client_ip_address_type(self):
        return self._client_ip_address_type

    @property
    def request_body(self):
        return self._request_body

    @property
    def requested_path_with_query_string(self):
        return self._requested_path_with_query_string

    @property
    def requested_query_string_parameters(self):
        return self._requested_query_string_parameters

    @property
    def requested_url_components(self):
        return self._requested_url_components


class IPTVProxyHTTPSession(object):
    __slots__ = ['_client_ip_address', '_expiry_date_time_in_utc', '_id', '_last_access_date_time_in_utc',
                 '_user_agent']

    @classmethod
    def create(cls, client_ip_address, user_agent):
        current_date_time_in_utc = datetime.now(pytz.utc)

        return cls('{0}'.format(uuid.uuid4()),
                   client_ip_address,
                   user_agent,
                   current_date_time_in_utc,
                   current_date_time_in_utc + timedelta(days=7))

    @classmethod
    def createFromHTTPSessionRecord(cls, http_session_record):
        return cls(http_session_record['id'],
                   http_session_record['client_ip_address'],
                   http_session_record['user_agent'],
                   datetime.strptime(http_session_record['last_access_date_time_in_utc'], '%Y-%m-%d %H:%M:%S%z'),
                   datetime.strptime(http_session_record['expiry_date_time_in_utc'], '%Y-%m-%d %H:%M:%S%z'))

    def __init__(self, id_, client_ip_address, user_agent, last_access_date_time_in_utc, expiry_date_time_in_utc):
        self._id = id_
        self._client_ip_address = client_ip_address
        self._user_agent = user_agent
        self._last_access_date_time_in_utc = last_access_date_time_in_utc
        self._expiry_date_time_in_utc = expiry_date_time_in_utc

    @property
    def client_ip_address(self):
        return self._client_ip_address

    @property
    def expiry_date_time_in_utc(self):
        return self._expiry_date_time_in_utc

    @property
    def id(self):
        return self._id

    @property
    def last_access_date_time_in_utc(self):
        return self._last_access_date_time_in_utc

    @last_access_date_time_in_utc.setter
    def last_access_date_time_in_utc(self, last_access_date_time_in_utc):
        self._last_access_date_time_in_utc = last_access_date_time_in_utc

    @property
    def user_agent(self):
        return self._user_agent


class IPTVProxyHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, request_handler_class, is_secure):
        ThreadingMixIn.__init__(self)
        HTTPServer.__init__(self, server_address, request_handler_class)

        self._is_secure = is_secure

    @property
    def is_secure(self):
        return self._is_secure


class IPTVProxyHTTPServerThread(Thread):
    def __init__(self, server_address, is_secure):
        Thread.__init__(self)

        self._is_secure = is_secure
        self._server_address = server_address
        self._iptv_proxy_http_server = IPTVProxyHTTPServer(self._server_address,
                                                           IPTVProxyHTTPRequestHandler,
                                                           is_secure)

        if is_secure:
            self._iptv_proxy_http_server.socket = ssl.wrap_socket(
                self._iptv_proxy_http_server.socket,
                certfile=IPTVProxySecurityManager.get_certificate_file_path(),
                keyfile=IPTVProxySecurityManager.get_key_file_path(),
                server_side=True)

        self.daemon = True

    def run(self):
        server_hostname_loopback = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HOSTNAME_LOOPBACK')
        server_hostname_private = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HOSTNAME_PRIVATE')
        server_hostname_public = IPTVProxyConfiguration.get_configuration_parameter(
            'SERVER_HOSTNAME_PUBLIC')
        server_http_port = IPTVProxyConfiguration.get_configuration_parameter('SERVER_HTTP_PORT')
        server_https_port = IPTVProxyConfiguration.get_configuration_parameter('SERVER_HTTPS_PORT')

        protocol_suffix = ''
        server_port = server_http_port

        if self._is_secure:
            protocol_suffix = 's'
            server_port = server_https_port

        logger.info(
            'Starting HTTP{0} Server\n'
            'Listening port => {1}\n\n'
            'Loopback Live Playlist URL => {2}\n'
            'Loopback VOD Playlist URL  => {3}\n'
            'Loopback EPG URL           => {4}\n\n'
            'Private Live Playlist URL  => {5}\n'
            'Private VOD Playlist URL   => {6}\n'
            'Private EPG URL            => {7}\n\n'
            'Public Live Playlist URL   => {8}\n'
            'Public VOD Playlist URL    => {9}\n'
            'Public EPG URL             => {10}'.format(
                protocol_suffix.upper(),
                server_port,
                'http{0}://{1}:{2}/live/playlist.m3u8'.format(protocol_suffix,
                                                              server_hostname_loopback,
                                                              server_port),
                'http{0}://{1}:{2}/vod/playlist.m3u8'.format(protocol_suffix,
                                                             server_hostname_loopback,
                                                             server_port),
                'http{0}://{1}:{2}/live/epg.xml'.format(protocol_suffix,
                                                        server_hostname_loopback,
                                                        server_port),
                'http{0}://{1}:{2}/live/playlist.m3u8'.format(protocol_suffix,
                                                              server_hostname_private,
                                                              server_port) if server_hostname_private else 'N/A',
                'http{0}://{1}:{2}/vod/playlist.m3u8'.format(protocol_suffix,
                                                             server_hostname_private,
                                                             server_port) if server_hostname_private else 'N/A',
                'http{0}://{1}:{2}/live/epg.xml'.format(protocol_suffix,
                                                        server_hostname_private,
                                                        server_port) if server_hostname_private else 'N/A',
                'http{0}://{1}:{2}/live/playlist.m3u8'.format(protocol_suffix,
                                                              server_hostname_public,
                                                              server_port) if server_hostname_public else 'N/A',
                'http{0}://{1}:{2}/vod/playlist.m3u8'.format(protocol_suffix,
                                                             server_hostname_public,
                                                             server_port) if server_hostname_public else 'N/A',
                'http{0}://{1}:{2}/live/epg.xml'.format(protocol_suffix,
                                                        server_hostname_public,
                                                        server_port) if server_hostname_public else 'N/A'))

        self._iptv_proxy_http_server.serve_forever()
        self._iptv_proxy_http_server.server_close()

        logger.info('Shutdown HTTP{0} Server\n'
                    'Listening port => {1}').format('S' if self._iptv_proxy_http_server.is_secure else '',
                                                    self._server_address[1])

    def stop(self):
        self._iptv_proxy_http_server.shutdown()
