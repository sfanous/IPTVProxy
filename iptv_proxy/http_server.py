import base64
import binascii
import email.utils
import functools
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
from http.cookies import CookieError
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer as HTTPServer_
from io import BytesIO
from json import JSONDecodeError
from socketserver import ThreadingMixIn
from threading import Thread

import pytz
import requests
import tzlocal
from rwlock import RWLock

from iptv_proxy.cache import CacheManager
from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.constants import DEFAULT_STREAMING_PROTOCOL
from iptv_proxy.constants import HTTP_CHUNK_SIZE
from iptv_proxy.data_access import DatabaseAccess
from iptv_proxy.data_model import HTTPSession
from iptv_proxy.db import Database
from iptv_proxy.enums import EPGStyle
from iptv_proxy.enums import IPAddressType
from iptv_proxy.epg import EPG
from iptv_proxy.exceptions import SegmentNotFoundError
from iptv_proxy.html_template_engine import HTMLTemplateEngine
from iptv_proxy.json_api import ConfigurationJSONAPI
from iptv_proxy.json_api import RecordingsJSONAPI
from iptv_proxy.providers import ProvidersController
from iptv_proxy.proxy import IPTVProxy
from iptv_proxy.recorder import PVR
from iptv_proxy.security import SecurityManager
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class HTTPRequestHandler(BaseHTTPRequestHandler):
    _allow_insecure_lan_connections = True
    _allow_insecure_lan_connections_lock = RWLock()
    _allow_insecure_wan_connections = False
    _allow_insecure_wan_connections_lock = RWLock()
    _lan_connections_require_credentials = False
    _lan_connections_require_credentials_lock = RWLock()
    _wan_connections_require_credentials = True
    _wan_connections_require_credentials_lock = RWLock()

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_allow_insecure_lan_connections(
                OptionalSettings.get_optional_settings_parameter('allow_insecure_lan_connections'))
        except KeyError:
            pass

        try:
            cls.set_allow_insecure_wan_connections(
                OptionalSettings.get_optional_settings_parameter('allow_insecure_wan_connections'))
        except KeyError:
            pass

        try:
            cls.set_lan_connections_require_credentials(
                OptionalSettings.get_optional_settings_parameter('lan_connections_require_credentials'))
        except KeyError:
            pass

        try:
            cls.set_wan_connections_require_credentials(
                OptionalSettings.get_optional_settings_parameter('wan_connections_require_credentials'))
        except KeyError:
            pass

    @classmethod
    def _initialize_http_sessions(cls, db_session):
        deleted_http_sessions_log_message = []
        loaded_http_sessions_log_message = []

        unformatted_message_to_log = 'Session ID         => {0}\n' \
                                     'Client IP address  => {1}\n' \
                                     'Browser user agent => {2}\n' \
                                     'Expiry date & time => {3}\n'

        for http_session_row in DatabaseAccess.query_http_sessions(db_session):
            current_date_time_in_utc = datetime.now(pytz.utc)

            formatted_message_to_log = unformatted_message_to_log.format(
                http_session_row.id,
                http_session_row.client_ip_address,
                http_session_row.user_agent,
                http_session_row.expiry_date_time_in_utc.astimezone(tzlocal.get_localzone()).strftime(
                    '%Y-%m-%d %H:%M:%S%z'))

            if current_date_time_in_utc >= http_session_row.expiry_date_time_in_utc:
                DatabaseAccess.delete_http_session(db_session, http_session_row.id)

                deleted_http_sessions_log_message.append(formatted_message_to_log)
            else:
                loaded_http_sessions_log_message.append(formatted_message_to_log)

        if deleted_http_sessions_log_message:
            deleted_http_sessions_log_message.insert(0, 'Deleted HTTP server session{0}\n'.format(
                's' if len(deleted_http_sessions_log_message) > 1
                else ''))

            logger.debug('\n'.join(deleted_http_sessions_log_message).strip())

        if loaded_http_sessions_log_message:
            loaded_http_sessions_log_message.insert(0, 'Loaded HTTP server session{0}\n'.format(
                's' if len(loaded_http_sessions_log_message) > 1
                else ''))

            logger.debug('\n'.join(loaded_http_sessions_log_message).strip())

    @classmethod
    def initialize(cls):
        cls._initialize_class_variables()

        with Database.get_write_lock():
            db_session = Database.create_session()

            try:
                cls._initialize_http_sessions(db_session)
                db_session.commit()
            except Exception:
                (type_, value_, traceback_) = sys.exc_info()
                logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                db_session.rollback()
            finally:
                db_session.close()

    @classmethod
    def purge_http_sessions(cls, db_session):
        DatabaseAccess.delete_http_sessions(db_session)

    @classmethod
    def set_allow_insecure_lan_connections(cls, allow_insecure_lan_connections):
        with cls._allow_insecure_lan_connections_lock.writer_lock:
            cls._allow_insecure_lan_connections = allow_insecure_lan_connections

    @classmethod
    def set_allow_insecure_wan_connections(cls, allow_insecure_wan_connections):
        with cls._allow_insecure_wan_connections_lock.writer_lock:
            cls._allow_insecure_wan_connections = allow_insecure_wan_connections

    @classmethod
    def set_lan_connections_require_credentials(cls, lan_connections_require_credentials):
        with cls._lan_connections_require_credentials_lock.writer_lock:
            cls._lan_connections_require_credentials = lan_connections_require_credentials

    @classmethod
    def set_wan_connections_require_credentials(cls, wan_connections_require_credentials):
        with cls._wan_connections_require_credentials_lock.writer_lock:
            cls._wan_connections_require_credentials = wan_connections_require_credentials

    def _authenticate(self, password_to_authenticate):
        server_password = Configuration.get_configuration_parameter('SERVER_PASSWORD')

        if server_password != password_to_authenticate:
            self._send_http_error(requests.codes.UNAUTHORIZED, 'Invalid password provided.')

            return False

        return True

    def _authorization_required(self):
        with HTTPRequestHandler._wan_connections_require_credentials_lock.reader_lock, \
             HTTPRequestHandler._lan_connections_require_credentials_lock.reader_lock:
            if self._client_ip_address_type == IPAddressType.PUBLIC and not \
                    HTTPRequestHandler._wan_connections_require_credentials:
                return False
            elif self._client_ip_address_type != IPAddressType.PUBLIC and not \
                    HTTPRequestHandler._lan_connections_require_credentials:
                return False

            return True

    def _create_http_session_cookie(self, http_session):
        http_session_id_cookie_expires = email.utils.format_datetime(http_session.expiry_date_time_in_utc)

        self._cookies['http_session_id'] = http_session.id
        self._cookies['http_session_id']['expires'] = http_session_id_cookie_expires
        self._cookies['http_session_id']['httponly'] = True
        self._cookies['http_session_id']['path'] = '/index.html'

    def _create_settings_cookies(self):
        settings_cookie_expires = self._cookies.get('settings_cookie_expires')

        if settings_cookie_expires is None:
            settings_cookie_expires_value = email.utils.format_datetime(
                (datetime.now(pytz.utc) + timedelta(days=366)).replace(hour=0,
                                                                       minute=0,
                                                                       second=0,
                                                                       microsecond=0))

            self._cookies['settings_cookie_expires'] = settings_cookie_expires_value

        if self._cookies.get('guide_number_of_days') is None:
            self._cookies['guide_number_of_days'] = '1'

        if self._cookies.get('guide_provider') is None or \
                self._cookies.get('guide_provider').value.lower() not in self._active_providers_map_class:
            if self._active_providers_map_class:
                self._cookies['guide_provider'] = self._active_providers_map_class[sorted(
                    self._active_providers_map_class)[0]].api_class().__name__
                del self._cookies['guide_group']

        if self._cookies.get('guide_provider') is not None:
            if self._cookies.get('guide_group') is None:
                provider_map_class = self._active_providers_map_class[self._cookies.get('guide_provider').value.lower()]
                groups = provider_map_class.epg_class().get_m3u8_groups()

                if groups:
                    self._cookies['guide_group'] = sorted(groups)[0]

        if self._cookies.get('streaming_protocol') is None:
            self._cookies['streaming_protocol'] = DEFAULT_STREAMING_PROTOCOL

        for cookie_name in ['settings_cookie_expires', 'guide_number_of_days', 'guide_provider', 'guide_group',
                            'streaming_protocol']:
            if self._cookies.get(cookie_name) is not None:
                self._cookies[cookie_name]['expires'] = self._cookies.get('settings_cookie_expires').value
                self._cookies[cookie_name]['path'] = '/index.html'

    def _generate_http_response_chunks(self, response_content):
        start_index = 0
        response_content_length = len(response_content)

        while response_content_length:
            number_of_bytes_written = self._response_content_buffer.write(
                response_content[start_index:start_index + HTTP_CHUNK_SIZE - self._response_content_buffer_size])

            self._response_content_buffer_size += number_of_bytes_written

            start_index += number_of_bytes_written
            response_content_length -= number_of_bytes_written

            if self._response_content_buffer_size == HTTP_CHUNK_SIZE:
                self._response_content_buffer.seek(0)
                yield True

                self._response_content_buffer.seek(0)
                self._response_content_buffer.truncate()
                self._response_content_buffer_size = 0

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
        self.protocol_version = 'HTTP/1.1'

        self._client_ip_address = self.client_address[0]
        self._client_port_number = self.client_address[1]
        self._client_ip_address_type = Utility.determine_ip_address_type(self._client_ip_address)
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
        self._response_content_generator_method = None
        self._response_content_buffer = BytesIO()
        self._response_content_buffer_size = 0
        self._response_content_to_log = None
        self._response_content_type = None
        self._response_content_encoding = None
        self._do_log_response_content = True

        self._active_providers_map_class = ProvidersController.get_active_providers_map_class()

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

                with Database.get_write_lock():
                    db_session = Database.create_session()

                    try:
                        http_session = DatabaseAccess.query_http_session(db_session, http_session_id)

                        if http_session is None:
                            logged_in = False
                        else:
                            if datetime.now(pytz.utc) > http_session.expiry_date_time_in_utc or \
                                    self._client_ip_address != http_session.client_ip_address or \
                                    self._user_agent != http_session.user_agent:
                                logged_in = False

                                DatabaseAccess.delete_http_session(db_session, http_session.id)
                                db_session.commit()
                            else:
                                logged_in = True

                                http_session.last_access_date_time_in_utc = datetime.now(pytz.utc)
                    except Exception:
                        (type_, value_, traceback_) = sys.exc_info()
                        logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                        db_session.rollback()

                        logged_in = False
                    finally:
                        db_session.close()
        else:
            logged_in = True

        return logged_in

    def _log_request(self):
        if logger.getEffectiveLevel() == logging.TRACE:
            if self.headers:
                request_headers_to_log = \
                    '[Header]\n' \
                    '========\n' \
                    '{0}\n\n'.format('\n'.join(['{0:32} => {1!s}'.format(header, self.headers[header])
                                                for header in sorted(self.headers)]))
            else:
                request_headers_to_log = ''

            if self._requested_query_string_parameters:
                request_query_parameters_to_log = \
                    '[Query Parameters]\n' \
                    '==================\n' \
                    '{0}\n'.format('\n'.join(
                        ['{0:32} => {1!s}'.format(parameter, self._requested_query_string_parameters[parameter])
                         for parameter in sorted(self._requested_query_string_parameters)]))
            else:
                request_query_parameters_to_log = ''

            if self._request_body:
                try:
                    request_content_to_log = '[Content]\n' \
                                             '=========\n{0}'.format(pprint.pformat(json.loads(self._request_body)))
                except (JSONDecodeError, TypeError):
                    request_content_to_log = '[Content]\n' \
                                             '=========\n{0}'.format(self._request_body)
            else:
                request_content_to_log = ''

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
                                   'http{0}://{1}{2}'.format('s' if self.server.is_secure
                                                             else '',
                                                             self.headers.get('Host'),
                                                             self.path),
                                   request_headers_to_log,
                                   request_query_parameters_to_log,
                                   request_content_to_log))

    def _log_response(self):
        if logger.getEffectiveLevel() == logging.TRACE:
            response_url_to_log = 'http{0}://{1}{2}'.format('s' if self.server.is_secure
                                                            else '',
                                                            self.headers.get('Host'),
                                                            self._requested_path_with_query_string)

            if self._response_headers:
                response_headers_to_log = \
                    '[Header]\n' \
                    '========\n' \
                    '{0}\n\n'.format('\n'.join(['{0:32} => {1!s}'.format(header, self._response_headers[header])
                                                for header in sorted(self._response_headers)]))
            else:
                response_headers_to_log = ''

            if self._do_log_response_content and self._response_content_to_log:
                response_content_to_log = '[Content]\n' \
                                          '=========\n' \
                                          '{0}\n'.format(self._response_content_to_log)
            else:
                response_content_to_log = ''

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
                '{6}'.format(
                    self._client_ip_address,
                    '/{0}'.format(self._client_uuid) if self._client_uuid
                    else '',
                    self.command,
                    response_url_to_log,
                    self._response_status_code,
                    response_headers_to_log,
                    response_content_to_log))

    def _screen_request(self, password_to_authenticate):
        if self._transport_layer_requirements_satisfied():
            if self._authorization_required():
                return self._authenticate(password_to_authenticate)
            else:
                return True
        else:
            return False

    def _send_http_error(self, http_error_code, http_error_details):
        self._response_content = HTMLTemplateEngine.render_errors_template(http_error_code,
                                                                           http.client.responses[http_error_code],
                                                                           http_error_details)
        self._response_status_code = http_error_code
        self._response_content_type = 'text/html; charset=utf-8'
        self._do_log_response_content = False
        self._send_http_response()

    def _send_http_response(self):
        self.send_response(self._response_status_code)

        if self._do_log_response_content:
            self._response_content_to_log = self._response_content

        if self._do_gzip_response_content:
            self._response_content_encoding = 'gzip'

            if self._response_content:
                self._response_content = Utility.gzip(self._response_content)

        self._send_http_response_headers()

        self._log_response()

        if self._response_content:
            if type(self._response_content) != bytes:
                self._response_content = self._response_content.encode()
            self.wfile.write(self._response_content)
        elif self._response_content_generator_method:
            self._send_http_response_chunked()

    def _send_http_response_chunked(self):
        if self._do_gzip_response_content:
            gzip_compressor = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16, zlib.DEF_MEM_LEVEL, 0)

            for response_content in self._response_content_generator_method():
                gzipped_response_content = gzip_compressor.compress(response_content.encode())

                if gzipped_response_content:
                    for _ in self._generate_http_response_chunks(gzipped_response_content):
                        self.wfile.write('{0:X}\r\n'.format(HTTP_CHUNK_SIZE).encode())
                        self.wfile.write(self._response_content_buffer.read())
                        self.wfile.write('\r\n'.encode())

            gzipped_response_content = gzip_compressor.flush()

            if gzipped_response_content:
                for _ in self._generate_http_response_chunks(gzipped_response_content):
                    self.wfile.write('{0:X}\r\n'.format(HTTP_CHUNK_SIZE).encode())
                    self.wfile.write(self._response_content_buffer.read())
                    self.wfile.write('\r\n'.encode())

            if self._response_content_buffer_size:
                self._response_content_buffer.seek(0)

                self.wfile.write('{0:X}\r\n'.format(self._response_content_buffer_size).encode())
                self.wfile.write(self._response_content_buffer.read())
                self.wfile.write('\r\n'.encode())

            self.wfile.write('0\r\n\r\n'.encode())
        else:
            for response_content in self._response_content_generator_method():
                if type(response_content) != bytes:
                    response_content = response_content.encode()

                for _ in self._generate_http_response_chunks(response_content):
                    self.wfile.write('{0:X}\r\n'.format(HTTP_CHUNK_SIZE).encode())
                    self.wfile.write(self._response_content_buffer.read())
                    self.wfile.write('\r\n'.encode())

            if self._response_content_buffer_size:
                self._response_content_buffer.seek(0)

                self.wfile.write('{0:X}\r\n'.format(self._response_content_buffer_size).encode())
                self.wfile.write(self._response_content_buffer.read())
                self.wfile.write('\r\n'.encode())

            self.wfile.write('0\r\n\r\n'.encode())

    def _send_http_response_headers(self):
        if self.command == 'OPTIONS':
            self._response_headers['Access-Control-Allow-Methods'] = ['DELETE, GET, OPTIONS, PATCH, POST']

        self._response_headers['Access-Control-Allow-Origin'] = ['*']

        if self._response_content_type == 'image/png':
            self._response_headers['Cache-Control'] = ['Cache-Control: public, max-age=604800']

        if self._response_content_encoding:
            self._response_headers['Content-Encoding'] = [self._response_content_encoding]

        if self._response_content:
            if type(self._response_content) == bytes:
                self._response_headers['Content-Length'] = ['{0}'.format(len(self._response_content))]
            else:
                self._response_headers['Content-Length'] = ['{0}'.format(len(self._response_content.encode()))]

            self._response_headers['Content-Type'] = [self._response_content_type]
        elif self._response_content_generator_method:
            self._response_headers['Content-Type'] = [self._response_content_type]
            self._response_headers['Transfer-Encoding'] = ['chunked']

        if self._response_status_code == requests.codes.FOUND:
            self._response_headers['Location'] = ['/index.html']

        if self._cookies:
            self._response_headers['Set-Cookie'] = []

            for cookie in sorted(self._cookies):
                if self._cookies[cookie]['expires']:
                    self._response_headers['Set-Cookie'].append(self._cookies[cookie].output(header='').strip())

        if self._response_headers:
            for header_key in sorted(self._response_headers):
                for header_value in self._response_headers[header_key]:
                    self.send_header(header_key, header_value)
        self.end_headers()

    def _transport_layer_requirements_satisfied(self):
        with HTTPRequestHandler._allow_insecure_wan_connections_lock.reader_lock, \
             HTTPRequestHandler._allow_insecure_lan_connections_lock.reader_lock:
            transport_layer_requirements_satisfied = True

            if self._client_ip_address_type == IPAddressType.PUBLIC:
                if not HTTPRequestHandler._allow_insecure_wan_connections and not self.server.is_secure:
                    transport_layer_requirements_satisfied = False
            else:
                if not HTTPRequestHandler._allow_insecure_lan_connections and not self.server.is_secure:
                    transport_layer_requirements_satisfied = False

            if not transport_layer_requirements_satisfied:
                self._send_http_error(requests.codes.FORBIDDEN,
                                      'The requested resource can only be processed over a secure channel (HTTPS).'
                                      '            <br/>'
                                      '            <a href={0}>{0}</a>'.format('https://{0}:{1}{2}'.format(
                                          self.headers.get('Host').split(':')[0],
                                          Configuration.get_configuration_parameter('SERVER_HTTPS_PORT'),
                                          self.path)))

            return transport_layer_requirements_satisfied

    # noinspection PyPep8Naming
    def do_DELETE(self):
        self._initialize()
        self._log_request()

        requested_path_not_found = False

        try:
            if self._requested_path_tokens_length == 2 and \
                    self._requested_path_tokens[0].lower() == 'recordings' and \
                    re.match(r'\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z',
                             self._requested_path_tokens[1].lower()):
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = RecordingsJSONAPI(self).process_delete_request()
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

        try:
            if re.match(r'\A(index.htm)?\Z', self._requested_path_tokens[0].lower()) and \
                    self._requested_path_tokens_length == 1:
                self._response_status_code = requests.codes.FOUND
                self._send_http_response()
            elif re.match(r'\A(index.html)\Z', self._requested_path_tokens[0].lower()) and \
                    self._requested_path_tokens_length == 1:
                refresh_epg_parameter_value = self._requested_query_string_parameters.get('refresh_epg')

                if self._transport_layer_requirements_satisfied():
                    if self._is_logged_in():
                        if not set(self._requested_query_string_parameters) - {'refresh_epg'}:
                            request_guide_provider_cookie_value = urllib.parse.unquote(
                                self._cookies.get('guide_provider').value)

                            self._create_settings_cookies()

                            guide_number_of_days_cookie_value = self._cookies.get('guide_number_of_days').value
                            guide_provider_cookie_value = urllib.parse.unquote(
                                self._cookies.get('guide_provider').value)
                            guide_group_cookie_value = urllib.parse.unquote(self._cookies.get('guide_group').value)

                            if request_guide_provider_cookie_value is not None and \
                                    request_guide_provider_cookie_value.lower() in self._active_providers_map_class:
                                if refresh_epg_parameter_value:
                                    self._response_content_generator_method = functools.partial(
                                        HTMLTemplateEngine().render_guide_div_template,
                                        self.server.is_secure,
                                        self._authorization_required(),
                                        self._client_ip_address,
                                        self._client_uuid,
                                        guide_number_of_days_cookie_value,
                                        guide_provider_cookie_value,
                                        guide_group_cookie_value,
                                        self._active_providers_map_class)
                                else:
                                    streaming_protocol_cookie_value = self._cookies.get('streaming_protocol').value

                                    self._response_content_generator_method = functools.partial(
                                        HTMLTemplateEngine().render_index_template,
                                        self.server.is_secure,
                                        self._authorization_required(),
                                        self._client_ip_address,
                                        self._client_uuid,
                                        guide_number_of_days_cookie_value,
                                        guide_provider_cookie_value,
                                        guide_group_cookie_value,
                                        streaming_protocol_cookie_value,
                                        self._active_providers_map_class)

                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'text/html; charset=utf-8'
                                self._do_log_response_content = False
                                self._send_http_response()
                            else:
                                if request_guide_provider_cookie_value.lower() in \
                                        ProvidersController.get_providers_map_class():
                                    self._handle_service_unavailable_error(ProvidersController.get_provider_map_class(
                                        request_guide_provider_cookie_value.lower()).api_class())
                                else:
                                    requested_path_not_found = True
                        else:
                            invalid_query_string = True
                    else:
                        if not set(self._requested_query_string_parameters) - {'refresh_epg'}:
                            self._response_content = HTMLTemplateEngine.render_login_template()

                            self._response_status_code = requests.codes.OK
                            self._response_content_type = 'text/html; charset=utf-8'
                            self._do_log_response_content = False
                            self._send_http_response()
                        else:
                            invalid_query_string = True
            elif re.match(r'\A(.+)\.png\Z', self._requested_path_tokens[0].lower()) \
                    and self._requested_path_tokens_length == 1:
                http_token_parameter_value = self._requested_query_string_parameters.get('http_token')

                if self._screen_request(http_token_parameter_value):
                    if not set(self._requested_query_string_parameters) - {'http_token'}:
                        self._do_gzip_response_content = False

                        try:
                            self._response_content = Utility.read_png_file(self._requested_path_tokens[0],
                                                                           in_base_64=False)
                            self._response_status_code = requests.codes.OK
                            self._response_content_type = 'image/png'
                            self._do_log_response_content = False
                            self._send_http_response()
                        except OSError:
                            requested_path_not_found = True
                    else:
                        invalid_query_string = True
            elif self._requested_path_tokens[0].lower() == 'configuration' and self._requested_path_tokens_length == 1:
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = ConfigurationJSONAPI(self).process_get_request()
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            elif self._requested_path_tokens[0].lower() == 'live' and self._requested_path_tokens_length == 2:
                http_token_parameter_value = self._requested_query_string_parameters.get('http_token')

                if self._requested_path_tokens[1].lower() == 'epg.xml':
                    if self._screen_request(http_token_parameter_value):
                        if not set(self._requested_query_string_parameters) - {'http_token',
                                                                               'number_of_days',
                                                                               'style'}:
                            number_of_days_parameter_value = self._requested_query_string_parameters.get(
                                'number_of_days',
                                1)

                            style_parameter_value = self._requested_query_string_parameters.get(
                                'style',
                                EPGStyle.MINIMAL.value)

                            try:
                                self._response_content_generator_method = functools.partial(
                                    EPG.generate_xmltv,
                                    self.server.is_secure,
                                    self._authorization_required(),
                                    self._client_ip_address,
                                    self._active_providers_map_class,
                                    number_of_days_parameter_value,
                                    style_parameter_value)
                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'application/xml; charset=utf-8'
                                self._do_log_response_content = False
                                self._send_http_response()
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
                                    self._active_providers_map_class)
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
                if self._requested_path_tokens[1].lower() in self._active_providers_map_class:
                    provider_map_class = ProvidersController.get_provider_map_class(
                        self._requested_path_tokens[1].lower())

                    channel_number_parameter_value = self._requested_query_string_parameters.get('channel_number')
                    client_uuid_parameter_value = self._requested_query_string_parameters.get('client_uuid')
                    http_token_parameter_value = self._requested_query_string_parameters.get('http_token')

                    if client_uuid_parameter_value:
                        self._client_uuid = client_uuid_parameter_value

                    if self._requested_path_tokens[2].lower().endswith('.ts'):
                        if self._screen_request(http_token_parameter_value):
                            self._do_gzip_response_content = False

                            self._response_content = CacheManager.query_cache(
                                channel_number_parameter_value,
                                self._requested_path_tokens[2].lower())

                            if self._response_content is None:
                                try:
                                    self._response_content = provider_map_class.api_class().download_ts_file(
                                        self._client_ip_address,
                                        self._client_uuid,
                                        self._requested_url_components.path,
                                        self._requested_query_string_parameters)

                                    CacheManager.update_cache(channel_number_parameter_value,
                                                              self._requested_path_tokens[2].lower(),
                                                              self._response_content)

                                    self._response_status_code = requests.codes.OK
                                    self._response_content_type = 'video/m2ts'
                                    self._do_log_response_content = False
                                    self._send_http_response()
                                except requests.exceptions.HTTPError as e:
                                    self._send_http_error(e.response.status_code, '')
                    elif self._requested_path_tokens[2].lower() == 'chunks.m3u8':
                        if self._screen_request(http_token_parameter_value):
                            try:
                                self._response_content = provider_map_class.api_class().download_chunks_m3u8(
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
                                                                                   'number_of_days',
                                                                                   'style'}:
                                number_of_days_parameter_value = self._requested_query_string_parameters.get(
                                    'number_of_days',
                                    1)

                                style_parameter_value = self._requested_query_string_parameters.get(
                                    'style',
                                    EPGStyle.MINIMAL.value)

                                try:
                                    self._response_content_generator_method = functools.partial(
                                        provider_map_class.epg_class().generate_xmltv,
                                        self.server.is_secure,
                                        self._authorization_required(),
                                        self._client_ip_address,
                                        number_of_days_parameter_value,
                                        style_parameter_value)
                                    self._response_status_code = requests.codes.OK
                                    self._response_content_type = 'application/xml; charset=utf-8'
                                    self._do_log_response_content = False
                                    self._send_http_response()
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
                                            provider_map_class.epg_class().get_channel_name(
                                                int(channel_number_parameter_value)),
                                            self._client_ip_address,
                                            self._client_uuid))

                                        try:
                                            self._response_content = \
                                                provider_map_class.api_class().download_playlist_m3u8(
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
                                    self._response_content = provider_map_class.api_class().generate_playlist_m3u8(
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
                    if self._requested_path_tokens[1].lower() in ProvidersController.get_providers_map_class():
                        self._handle_service_unavailable_error(ProvidersController.get_provider_map_class(
                            self._requested_path_tokens[1].lower()).api_class())
                    else:
                        requested_path_not_found = True
            elif self._requested_path_tokens[0].lower() == 'recordings':
                if self._requested_path_tokens_length == 1:
                    if self._screen_request(self._get_json_request_password()):
                        (self._response_content,
                         self._response_status_code) = RecordingsJSONAPI(self).process_get_request()
                elif re.match(r'\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z',
                              self._requested_path_tokens[1].lower()) and self._requested_path_tokens_length == 2:
                    if self._screen_request(self._get_json_request_password()):
                        (self._response_content,
                         self._response_status_code) = RecordingsJSONAPI(self).process_get_request(
                            self._requested_path_tokens[1].lower())
                else:
                    requested_path_not_found = True

                if not requested_path_not_found:
                    self._response_content_type = 'application/vnd.api+json'
                    self._send_http_response()
            elif self._requested_path_tokens[0].lower() == 'vod' and self._requested_path_tokens_length == 2:
                client_uuid_parameter_value = self._requested_query_string_parameters.get('client_uuid')
                http_token_parameter_value = self._requested_query_string_parameters.get('http_token')
                recording_id = self._requested_query_string_parameters.get('recording_id')

                if client_uuid_parameter_value:
                    self._client_uuid = client_uuid_parameter_value

                if self._requested_path_tokens[1].lower().endswith('.ts'):
                    if self._screen_request(http_token_parameter_value):
                        if not set(self._requested_query_string_parameters) - {'client_uuid',
                                                                               'http_token',
                                                                               'recording_id'}:
                            self._do_gzip_response_content = False

                            try:
                                self._response_content = PVR.load_ts_file(
                                    re.sub(r'/vod/(.*)\?.*', r'\1', self._requested_path_with_query_string),
                                    recording_id)
                                self._response_status_code = requests.codes.OK
                                self._response_content_type = 'video/m2ts'
                                self._do_log_response_content = False
                                self._send_http_response()
                            except (OSError, SegmentNotFoundError):
                                requested_path_not_found = True
                        else:
                            invalid_query_string = True
                elif self._requested_path_tokens[1].lower() == 'playlist.m3u8':
                    if self._screen_request(http_token_parameter_value):
                        if recording_id:
                            if not set(self._requested_query_string_parameters) - {'client_uuid',
                                                                                   'http_token',
                                                                                   'recording_id'}:
                                logger.info('{0} requested from {1}/{2}'.format(
                                    PVR.get_recording_program_title(recording_id),
                                    self._client_ip_address,
                                    self._client_uuid))

                                try:
                                    self._response_content = PVR.generate_vod_recording_playlist_m3u8(
                                        self._client_uuid,
                                        recording_id,
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
                                self._response_content = PVR.generate_vod_index_playlist_m3u8(
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

        try:
            if self._requested_path_tokens_length == 1 and self._requested_path_tokens[0].lower() == 'configuration':
                if self._screen_request(self._get_json_request_password()):
                    (self._response_content,
                     self._response_status_code) = ConfigurationJSONAPI(self).process_patch_request()
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

        try:
            if re.match(r'\A(index.html)\Z', self._requested_path_tokens[0].lower()) and \
                    self._requested_path_tokens_length == 1:
                bad_post_index_html_request = False

                if self._request_body:
                    match = re.match(r'\ApasswordInput=(.*)\Z', self._request_body)

                    if match:
                        password = urllib.parse.unquote(match.group(1))

                        if self._authenticate(password):
                            http_session = HTTPSession(self._client_ip_address,
                                                       self._user_agent)
                            self._create_http_session_cookie(http_session)

                            with Database.get_write_lock():
                                db_session = Database.create_session()

                                try:
                                    db_session.add(http_session)
                                    db_session.commit()
                                except Exception:
                                    (type_, value_, traceback_) = sys.exc_info()
                                    logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                                    db_session.rollback()
                                finally:
                                    db_session.close()

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
                     self._response_status_code) = RecordingsJSONAPI(self).process_post_request()
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


class HTTPServer(ThreadingMixIn, HTTPServer_):
    def __init__(self, server_address, request_handler_class, is_secure):
        ThreadingMixIn.__init__(self)
        HTTPServer_.__init__(self, server_address, request_handler_class)

        self._is_secure = is_secure

    @property
    def is_secure(self):
        return self._is_secure


class HTTPServerThread(Thread):
    def __init__(self, server_address, is_secure):
        Thread.__init__(self)

        self._is_secure = is_secure
        self._server_address = server_address
        self._iptv_proxy_http_server = HTTPServer(self._server_address,
                                                  HTTPRequestHandler,
                                                  is_secure)

        if is_secure:
            self._iptv_proxy_http_server.socket = ssl.wrap_socket(
                self._iptv_proxy_http_server.socket,
                certfile=SecurityManager.get_certificate_file_path(),
                keyfile=SecurityManager.get_key_file_path(),
                server_side=True)

        self.daemon = True

    def run(self):
        server_hostname_loopback = Configuration.get_configuration_parameter(
            'SERVER_HOSTNAME_LOOPBACK')
        server_hostname_private = Configuration.get_configuration_parameter(
            'SERVER_HOSTNAME_PRIVATE')
        server_hostname_public = Configuration.get_configuration_parameter(
            'SERVER_HOSTNAME_PUBLIC')
        server_http_port = Configuration.get_configuration_parameter('SERVER_HTTP_PORT')
        server_https_port = Configuration.get_configuration_parameter('SERVER_HTTPS_PORT')

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
                                                              server_port) if server_hostname_private
                else 'N/A',
                'http{0}://{1}:{2}/vod/playlist.m3u8'.format(protocol_suffix,
                                                             server_hostname_private,
                                                             server_port) if server_hostname_private
                else 'N/A',
                'http{0}://{1}:{2}/live/epg.xml'.format(protocol_suffix,
                                                        server_hostname_private,
                                                        server_port) if server_hostname_private
                else 'N/A',
                'http{0}://{1}:{2}/live/playlist.m3u8'.format(protocol_suffix,
                                                              server_hostname_public,
                                                              server_port) if server_hostname_public
                else 'N/A',
                'http{0}://{1}:{2}/vod/playlist.m3u8'.format(protocol_suffix,
                                                             server_hostname_public,
                                                             server_port) if server_hostname_public
                else 'N/A',
                'http{0}://{1}:{2}/live/epg.xml'.format(protocol_suffix,
                                                        server_hostname_public,
                                                        server_port) if server_hostname_public
                else 'N/A'))

        self._iptv_proxy_http_server.serve_forever()
        self._iptv_proxy_http_server.server_close()

        logger.info('Shutdown HTTP{0} Server\n'
                    'Listening port => {1}'.format('S' if self._iptv_proxy_http_server.is_secure
                                                   else '',
                                                   self._server_address[1]))

    def stop(self):
        self._iptv_proxy_http_server.shutdown()
