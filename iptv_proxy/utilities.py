import base64
import ipaddress
import json
import logging
import logging.handlers
import os
import re
import socket
import sys
import traceback
from argparse import ArgumentParser
from string import Template

import requests

from .constants import CHANNEL_ICONS_DIRECTORY_PATH
from .constants import DEFAULT_CONFIGURATION_FILE_PATH
from .constants import DEFAULT_DB_FILE_PATH
from .constants import DEFAULT_HOSTNAME_LOOPBACK
from .constants import DEFAULT_LOG_FILE_PATH
from .constants import DEFAULT_RECORDINGS_DIRECTORY_PATH
from .constants import DEFAULT_SSL_CERTIFICATE_FILE_PATH
from .constants import DEFAULT_SSL_KEY_FILE_PATH
from .constants import TEMPLATES_DIRECTORY_PATH
from .constants import TRACE
from .constants import VALID_LOGGING_LEVEL_VALUES
from .enums import IPTVProxyIPAddressType
from .formatters import IPTVProxyMultiLineFormatter

logger = logging.getLogger(__name__)


class IPTVProxyUtility():
    @classmethod
    def assemble_response_from_log_message(cls,
                                           response,
                                           is_content_binary=False,
                                           is_content_json=False,
                                           is_content_text=False,
                                           do_print_content=False):
        response_status_code = response.status_code
        if response_status_code == requests.codes.OK:
            response_headers = response.headers

            if is_content_binary:
                response_content = response.content
            elif is_content_json:
                response_content = json.dumps(response.json(), sort_keys=True, indent=2)
            elif is_content_text:
                response_content = response.text
            else:
                response_content = ''
                do_print_content = False

            return 'Response\n' \
                   '[Method]\n' \
                   '========\n{0}\n\n' \
                   '[URL]\n' \
                   '=====\n{1}\n\n' \
                   '[Status Code]\n' \
                   '=============\n{2}\n\n' \
                   '[Header]\n' \
                   '========\n{3}\n\n' \
                   '[Content]\n' \
                   '=========\n{4:{5}}\n'.format(response.request.method,
                                                 response.url,
                                                 response_status_code,
                                                 '\n'.join(['{0:32} => {1!s}'.format(key, response_headers[key])
                                                            for key in sorted(response_headers)]),
                                                 response_content if do_print_content else len(response_content),
                                                 '' if do_print_content else ',')
        else:
            return 'Response\n' \
                   '[Method]\n' \
                   '========\n{0}\n\n' \
                   '[URL]\n' \
                   '=====\n{1}\n\n' \
                   '[Status Code]\n' \
                   '=============\n{2}\n'.format(response.request.method, response.url, response_status_code)

    @classmethod
    def determine_ip_address_location(cls):
        ip_address_location = None

        try:
            response = requests.get('http://ip-api.com/json', headers={'Accept': 'application/json'})

            if response.status_code == requests.codes.OK:
                ip_address_location = response.json()
        except (json.JSONDecodeError, requests.exceptions.RequestException):
            logger.error('Failed to determine IP address location')

        return ip_address_location

    @classmethod
    def determine_ip_address_type(cls, ip_address):
        ip_address_object = ipaddress.ip_address(ip_address)

        if ip_address_object.is_loopback:
            return IPTVProxyIPAddressType.LOOPBACK
        elif ip_address_object in ipaddress.ip_network('10.0.0.0/8') or \
                ip_address_object in ipaddress.ip_network('172.16.0.0/12') or \
                ip_address_object in ipaddress.ip_network('192.168.0.0/16'):
            return IPTVProxyIPAddressType.PRIVATE
        elif ip_address_object.is_global:
            return IPTVProxyIPAddressType.PUBLIC

    @classmethod
    def determine_private_ip_address(cls):
        private_ip_address = None

        try:
            socket_object = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_object.connect(("8.8.8.8", 80))

            private_ip_address = socket_object.getsockname()[0]

            socket_object.close()
        except (IndexError, OSError):
            logger.error('Failed to determine private IP address')

        return private_ip_address

    @classmethod
    def determine_public_ip_address(cls):
        public_ip_address = None

        try:
            response = requests.get('https://httpbin.org/ip')

            if response.status_code == requests.codes.OK:
                public_ip_address = response.json()['origin']
        except (json.JSONDecodeError, requests.exceptions.RequestException):
            logger.error('Failed to determine public IP address')

        return public_ip_address

    @classmethod
    def initialize_logging(cls, log_file_path):
        logging.addLevelName(TRACE, 'TRACE')
        logging.TRACE = TRACE
        logging.trace = trace
        logging.Logger.trace = trace

        formatter = IPTVProxyMultiLineFormatter(
            '%(asctime)s %(name)-40s %(funcName)-40s %(levelname)-8s %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        rotating_file_handler = logging.handlers.RotatingFileHandler('{0}'.format(log_file_path),
                                                                     maxBytes=1024 * 1024 * 10,
                                                                     backupCount=10)
        rotating_file_handler.setFormatter(formatter)

        logging.getLogger('iptv_proxy').addHandler(console_handler)
        logging.getLogger('iptv_proxy').addHandler(rotating_file_handler)

        cls.set_logging_level(logging.INFO)

    @classmethod
    def is_valid_hostname(cls, hostname):
        if len(hostname) > 255:
            return False

        if hostname and hostname[-1] == ".":
            hostname = hostname[:-1]

        regular_expression = re.compile("(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)

        return all(regular_expression.match(label) for label in hostname.split("."))

    @classmethod
    def is_valid_logging_level(cls, logging_level):
        is_valid_logging_level = True

        if logging_level not in VALID_LOGGING_LEVEL_VALUES:
            is_valid_logging_level = False

        return is_valid_logging_level

    @classmethod
    def is_valid_loopback_hostname(cls, loopback_hostname):
        is_valid_loopback_hostname = True

        if loopback_hostname.lower() != DEFAULT_HOSTNAME_LOOPBACK:
            try:
                ip_address_object = ipaddress.ip_address(loopback_hostname)

                if not ip_address_object.is_loopback:
                    is_valid_loopback_hostname = False
            except ValueError:
                is_valid_loopback_hostname = False

        return is_valid_loopback_hostname

    @classmethod
    def is_valid_port_number(cls, port_number):
        is_valid_port_number = True

        try:
            port_number = int(port_number)

            if port_number < 0 or port_number > 65535:
                is_valid_port_number = False
        except ValueError:
            is_valid_port_number = False

        return is_valid_port_number

    @classmethod
    def is_valid_private_hostname(cls, hostname_private):
        is_valid_private_hostname = True

        try:
            ip_address_object = ipaddress.ip_address(hostname_private)

            if ip_address_object not in ipaddress.ip_network('10.0.0.0/8') and \
                    ip_address_object not in ipaddress.ip_network('172.16.0.0/12') and \
                    ip_address_object not in ipaddress.ip_network('192.168.0.0/16'):
                is_valid_private_hostname = False
        except ValueError:
            # This is a weak attempt to differentiate between a badly input IP address and a hostname.
            if re.match('\A[0-9]+\.[0-9]+.[0-9]+.[0-9]+\Z', hostname_private) or not \
                    IPTVProxyUtility.is_valid_hostname(hostname_private):
                is_valid_private_hostname = False

        return is_valid_private_hostname

    @classmethod
    def is_valid_public_hostname(cls, hostname_public):
        is_valid_public_hostname = True

        try:
            ip_address_object = ipaddress.ip_address(hostname_public)

            if not ip_address_object.is_global:
                is_valid_public_hostname = False
        except ValueError:
            # This is a weak attempt to differentiate between a badly input IP address and a hostname.
            if re.match('\A[0-9]+\.[0-9]+.[0-9]+.[0-9]+\Z', hostname_public) or not \
                    IPTVProxyUtility.is_valid_hostname(hostname_public):
                is_valid_public_hostname = False

        return is_valid_public_hostname

    @classmethod
    def is_valid_server_password(cls, server_password):
        return len(server_password)

    @classmethod
    def make_http_request(cls,
                          requests_http_method,
                          url,
                          params=None,
                          data=None,
                          json_=None,
                          headers=None,
                          cookies=None,
                          stream=False,
                          timeout=60):
        try:
            # noinspection PyUnresolvedReferences
            logger.trace('Request\n'
                         '[Method]\n'
                         '========\n{0}\n\n'
                         '[URL]\n'
                         '=====\n{1}\n'
                         '{2}{3}{4}{5}'.format(requests_http_method.__name__.upper(),
                                               url,
                                               '\n'
                                               '[Query Parameters]\n'
                                               '==================\n{0}\n'.format('\n'.join(
                                                   ['{0:32} => {1!s}'.format(key, params[key])
                                                    for key in sorted(params)])) if params else '',
                                               '\n'
                                               '[Headers]\n'
                                               '=========\n{0}\n'.format(
                                                   '\n'.join(
                                                       ['{0:32} => {1!s}'.format(header, headers[header])
                                                        for header in sorted(headers)])) if headers else '',
                                               '\n'
                                               '[Cookies]\n'
                                               '=========\n{0}\n'.format(
                                                   '\n'.join(
                                                       ['{0:32} => {1!s}'.format(cookie, cookies[cookie])
                                                        for cookie in sorted(cookies)])) if cookies else '',
                                               '\n'
                                               '[JSON]\n'
                                               '======\n{0}\n'.format(
                                                   json.dumps(json_,
                                                              sort_keys=True,
                                                              indent=2)) if json_ else '').strip())

            return requests_http_method(url,
                                        params=params,
                                        data=data,
                                        json=json_,
                                        headers=headers,
                                        cookies=cookies,
                                        stream=stream,
                                        timeout=timeout)
        except requests.exceptions.RequestException as e:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

            raise e

    @classmethod
    def parse_command_line_arguments(cls):
        parser = ArgumentParser()

        parser.add_argument('-c',
                            action='store',
                            default=DEFAULT_CONFIGURATION_FILE_PATH,
                            dest='configuration_file_path',
                            help='path to the configuration file',
                            metavar='configuration file path')
        parser.add_argument('-d',
                            action='store',
                            default=DEFAULT_DB_FILE_PATH,
                            dest='db_file_path',
                            help='path to the database file',
                            metavar='db file path')
        parser.add_argument('-l',
                            action='store',
                            default=DEFAULT_LOG_FILE_PATH,
                            dest='log_file_path',
                            help='path to the log file',
                            metavar='log file path')
        parser.add_argument('-r',
                            action='store',
                            default=DEFAULT_RECORDINGS_DIRECTORY_PATH,
                            dest='recordings_directory_path',
                            help='path to the recordings folder',
                            metavar='recordings folder path')
        parser.add_argument('-sc',
                            action='store',
                            default=DEFAULT_SSL_CERTIFICATE_FILE_PATH,
                            dest='certificate_file_path',
                            help='path to the SSL certificate file',
                            metavar='certificate file path')
        parser.add_argument('-sk',
                            action='store',
                            default=DEFAULT_SSL_KEY_FILE_PATH,
                            dest='key_file_path',
                            help='path to the SSL key file',
                            metavar='key file path')

        arguments = parser.parse_args()

        return (arguments.configuration_file_path,
                arguments.db_file_path,
                arguments.log_file_path,
                arguments.recordings_directory_path,
                arguments.certificate_file_path,
                arguments.key_file_path)

    @classmethod
    def read_file(cls, file_path, in_binary=False, in_base_64=False):
        try:
            with open(file_path, 'r{0}'.format('b' if in_binary else '')) as input_file:
                file_content = base64.b64encode(input_file.read()) if in_base_64 else input_file.read()

                # noinspection PyUnresolvedReferences
                logger.trace('Read file\n'
                             'File path => {0}'.format(file_path))
        except OSError:
            logger.error('Failed to read file\n'
                         'File path => {0}'.format(file_path))

            raise

        return file_content

    @classmethod
    def read_png_file(cls, file_name, in_base_64=False):
        png_file_path = os.path.join(CHANNEL_ICONS_DIRECTORY_PATH, file_name)

        return IPTVProxyUtility.read_file(png_file_path, in_binary=True, in_base_64=in_base_64)

    @classmethod
    def read_template(cls, template_file_name):
        with open(os.path.join(TEMPLATES_DIRECTORY_PATH, template_file_name), 'r') as input_file:
            template_content = input_file.read()

            return Template(template_content)

    @classmethod
    def set_logging_level(cls, log_level):
        logging.getLogger('iptv_proxy').setLevel(log_level)

        for handler in logger.handlers:
            handler.setLevel(log_level)


def trace(self, msg, *args, **kwargs):
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)
