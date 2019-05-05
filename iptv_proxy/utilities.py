import base64
import ipaddress
import json
import logging.config
import os
import re
import socket
import sys
import traceback
from argparse import ArgumentParser
from gzip import GzipFile
from io import BytesIO
from json import JSONDecodeError

import requests

from iptv_proxy.constants import CHANNEL_ICONS_DIRECTORY_PATH
from iptv_proxy.constants import DEFAULT_CONFIGURATION_FILE_PATH
from iptv_proxy.constants import DEFAULT_DB_FILE_PATH
from iptv_proxy.constants import DEFAULT_HOSTNAME_LOOPBACK
from iptv_proxy.constants import DEFAULT_LOG_FILE_PATH
from iptv_proxy.constants import DEFAULT_OPTIONAL_SETTINGS_FILE_PATH
from iptv_proxy.constants import DEFAULT_RECORDINGS_DIRECTORY_PATH
from iptv_proxy.constants import DEFAULT_SSL_CERTIFICATE_FILE_PATH
from iptv_proxy.constants import DEFAULT_SSL_KEY_FILE_PATH
from iptv_proxy.enums import IPAddressType

logger = logging.getLogger(__name__)


class Utility(object):
    __slots__ = []

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
                                                 response_content if do_print_content
                                                 else len(response_content),
                                                 '' if do_print_content
                                                 else ',')
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
        except (JSONDecodeError, requests.exceptions.RequestException):
            logger.error('Failed to determine IP address location')

        return ip_address_location

    @classmethod
    def determine_ip_address_type(cls, ip_address):
        ip_address_object = ipaddress.ip_address(ip_address)

        if ip_address_object.is_loopback:
            return IPAddressType.LOOPBACK
        elif ip_address_object in ipaddress.ip_network('10.0.0.0/8') or \
                ip_address_object in ipaddress.ip_network('172.16.0.0/12') or \
                ip_address_object in ipaddress.ip_network('192.168.0.0/16'):
            return IPAddressType.PRIVATE
        elif ip_address_object.is_global:
            return IPAddressType.PUBLIC

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
        except (JSONDecodeError, requests.exceptions.RequestException):
            logger.error('Failed to determine public IP address')

        return public_ip_address

    @classmethod
    def gzip(cls, data):
        compressed_bytes = BytesIO()

        with GzipFile(fileobj=compressed_bytes, mode='w') as gzip_file:
            if type(data) != bytes:
                gzip_file.write(data.encode())
            else:
                gzip_file.write(data)
            gzip_file.flush()

        return compressed_bytes.getvalue()

    @classmethod
    def is_valid_hostname(cls, hostname):
        if len(hostname) > 255:
            return False

        if hostname and hostname[-1] == ".":
            hostname = hostname[:-1]

        regular_expression = re.compile("(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)

        return all(regular_expression.match(label) for label in hostname.split("."))

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
            if re.match(r'\A\d+\.\d+.\d+.\d+\Z', hostname_private) or not \
                    Utility.is_valid_hostname(hostname_private):
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
            if re.match(r'\A\d+\.\d+.\d+.\d+\Z', hostname_public) or not \
                    Utility.is_valid_hostname(hostname_public):
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
                                                    for key in sorted(params)])) if params
                                               else '',
                                               '\n'
                                               '[Headers]\n'
                                               '=========\n{0}\n'.format(
                                                   '\n'.join(
                                                       ['{0:32} => {1!s}'.format(header, headers[header])
                                                        for header in sorted(headers)])) if headers
                                               else '',
                                               '\n'
                                               '[Cookies]\n'
                                               '=========\n{0}\n'.format(
                                                   '\n'.join(
                                                       ['{0:32} => {1!s}'.format(cookie, cookies[cookie])
                                                        for cookie in sorted(cookies)])) if cookies
                                               else '',
                                               '\n'
                                               '[JSON]\n'
                                               '======\n{0}\n'.format(
                                                   json.dumps(json_,
                                                              sort_keys=True,
                                                              indent=2)) if json_
                                               else '').strip())

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
        parser.add_argument('-os',
                            action='store',
                            default=DEFAULT_OPTIONAL_SETTINGS_FILE_PATH,
                            dest='optional_settings_file_path',
                            help='path to the optional settings file',
                            metavar='optional settings file path')
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
                arguments.optional_settings_file_path,
                arguments.db_file_path,
                arguments.log_file_path,
                arguments.recordings_directory_path,
                arguments.certificate_file_path,
                arguments.key_file_path)

    @classmethod
    def read_file(cls, file_path, in_binary=False, in_base_64=False):
        try:
            with open(file_path, 'r{0}'.format('b' if in_binary
                                               else '')) as input_file:
                file_content = base64.b64encode(input_file.read()) if in_base_64 else input_file.read()

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

        return Utility.read_file(png_file_path, in_binary=True, in_base_64=in_base_64)

    @classmethod
    def write_file(cls, file_content, file_path, in_binary=False):
        try:
            with open(file_path, 'w{0}'.format('b' if in_binary
                                               else '')) as output_file:
                output_file.write(file_content)

                logger.trace('Wrote file\n'
                             'File path => {0}'.format(file_path))
        except OSError:
            logger.error('Failed to write file\n'
                         'File path => {0}'.format(file_path))

            raise

        return file_content
