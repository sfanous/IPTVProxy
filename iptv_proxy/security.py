import base64
import binascii
import logging
import sys
import traceback
from datetime import datetime
from datetime import timedelta

import pytz
import tzlocal
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.constants import DEFAULT_SSL_CERTIFICATE_FILE_PATH
from iptv_proxy.constants import DEFAULT_SSL_KEY_FILE_PATH
from iptv_proxy.data_access import DatabaseAccess
from iptv_proxy.data_model import Setting
from iptv_proxy.db import Database
from iptv_proxy.enums import PasswordState
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class SecurityManager(object):
    __slots__ = []

    _auto_generate_self_signed_certificate = True
    _certificate_file_path = None
    _fernet = None
    _key_file_path = None

    @classmethod
    def _determine_password_state(cls, password):
        password_state = PasswordState.ENCRYPTED

        try:
            base64_decoded_encrypted_fernet_token = base64.urlsafe_b64decode(password)

            if base64_decoded_encrypted_fernet_token[0] == 0x80:
                length_of_base64_decoded_encrypted_fernet_token = len(base64_decoded_encrypted_fernet_token)

                if length_of_base64_decoded_encrypted_fernet_token < 73 or \
                        (length_of_base64_decoded_encrypted_fernet_token - 57) % 16 != 0:
                    password_state = PasswordState.DECRYPTED
            else:
                password_state = PasswordState.DECRYPTED
        except binascii.Error:
            password_state = PasswordState.DECRYPTED

        return password_state

    @classmethod
    def _encrypt_password(cls, decrypted_password):
        return cls._fernet.encrypt(decrypted_password.encode()).decode()

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_auto_generate_self_signed_certificate(
                OptionalSettings.get_optional_settings_parameter('auto_generate_self_signed_certificate'))
        except KeyError:
            pass

    @classmethod
    def _initialize_fernet_key(cls):
        db_session = Database.create_session()

        try:
            password_encryption_key_setting = DatabaseAccess.query_setting(db_session, 'password_encryption_key')

            if password_encryption_key_setting is not None:
                fernet_key = password_encryption_key_setting.value.encode()
                cls._fernet = Fernet(fernet_key)
        finally:
            db_session.close()

    @classmethod
    def decrypt_password(cls, encrypted_password):
        return cls._fernet.decrypt(encrypted_password.encode())

    @classmethod
    def determine_certificate_validity(cls):
        server_hostname_loopback = Configuration.get_configuration_parameter('SERVER_HOSTNAME_LOOPBACK')
        server_hostname_private = Configuration.get_configuration_parameter('SERVER_HOSTNAME_PRIVATE')
        server_hostname_public = Configuration.get_configuration_parameter('SERVER_HOSTNAME_PUBLIC')

        with open(cls._certificate_file_path, 'rb') as input_file:
            certificate = x509.load_pem_x509_certificate(input_file.read(), default_backend())
            certificate_subjects = certificate.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value.get_values_for_type(x509.DNSName)

            logger.debug(
                'Certificate status\n'
                'File path  => {0}\n'
                'Expires on => {1}\n'
                'Subjects   => {2}\n\n'
                '{3}'.format(cls._certificate_file_path,
                             certificate.not_valid_after.replace(tzinfo=pytz.utc).astimezone(
                                 tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                             ', '.join(certificate_subjects),
                             '\n'.join(
                                 ['Certificate is {0}valid for domain => {1}'.format(
                                     '' if server_hostname in certificate_subjects
                                     else 'not ',
                                     server_hostname)
                                     for server_hostname in
                                     [server_hostname_loopback, server_hostname_private, server_hostname_public]])))

    @classmethod
    def generate_self_signed_certificate(cls):
        ip_address_location = Utility.determine_ip_address_location()

        if ip_address_location is not None:
            private_key = rsa.generate_private_key(public_exponent=65537,
                                                   key_size=2048,
                                                   backend=default_backend())

            with open(DEFAULT_SSL_KEY_FILE_PATH, 'wb') as output_file:
                output_file.write(private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                                                            encryption_algorithm=serialization.NoEncryption()))

            current_date_time_in_utc = datetime.now(pytz.utc)

            subject = issuer = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, ip_address_location['countryCode']),
                                          x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,
                                                             ip_address_location['region']),
                                          x509.NameAttribute(NameOID.LOCALITY_NAME, ip_address_location['city']),
                                          x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'IPTVProxy'),
                                          x509.NameAttribute(NameOID.COMMON_NAME,
                                                             Configuration.get_configuration_parameter(
                                                                 'SERVER_HOSTNAME_PUBLIC'))])

            certificate = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                current_date_time_in_utc
            ).not_valid_after(
                current_date_time_in_utc + timedelta(days=10 * 365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(Configuration.get_configuration_parameter('SERVER_HOSTNAME_LOOPBACK')),
                    x509.DNSName(Configuration.get_configuration_parameter('SERVER_HOSTNAME_PRIVATE')),
                    x509.DNSName(Configuration.get_configuration_parameter('SERVER_HOSTNAME_PUBLIC'))]),
                critical=False
            ).sign(
                private_key,
                hashes.SHA256(),
                default_backend())

            with open(DEFAULT_SSL_CERTIFICATE_FILE_PATH, 'wb') as output_file:
                output_file.write(certificate.public_bytes(serialization.Encoding.PEM))
        else:
            logger.error('Failed to generate self signed certificate')

    @classmethod
    def get_auto_generate_self_signed_certificate(cls):
        return cls._auto_generate_self_signed_certificate

    @classmethod
    def get_certificate_file_path(cls):
        return cls._certificate_file_path

    @classmethod
    def get_key_file_path(cls):
        return cls._key_file_path

    @classmethod
    def initialize(cls):
        cls._initialize_class_variables()

        cls._initialize_fernet_key()

    @classmethod
    def is_password_decrypted(cls, password):
        is_password_decrypted = False

        if cls._determine_password_state(password) == PasswordState.DECRYPTED:
            is_password_decrypted = True

        return is_password_decrypted

    @classmethod
    def scrub_password(cls, provider_name, password):
        if cls._determine_password_state(password) == PasswordState.DECRYPTED:
            if cls._fernet is None:
                fernet_key = Fernet.generate_key()
                cls._fernet = Fernet(fernet_key)

                with Database.get_write_lock():
                    db_session = Database.create_session()

                    try:
                        db_session.add(Setting('password_encryption_key', fernet_key.decode()))
                        db_session.commit()
                    except Exception:
                        (type_, value_, traceback_) = sys.exc_info()
                        logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                        db_session.rollback()
                    finally:
                        db_session.close()

            encrypted_password = cls._encrypt_password(password)

            logger.debug('Scrubbed {0} password\n'
                         'Encrypted password => {1}'.format(provider_name,
                                                            encrypted_password))
        else:
            if cls._fernet:
                try:
                    cls.decrypt_password(password)
                    encrypted_password = password

                    logger.debug('Decryption key loaded is valid for the encrypted {0} password'.format(provider_name))
                except InvalidToken:
                    logger.error(
                        'Decryption key loaded is not valid for the encrypted {0} password\n'
                        'Please re-enter your cleartext password in the configuration file\n'
                        'Configuration file path => {0}\n'
                        'Exiting...'.format(provider_name,
                                            Configuration.get_configuration_file_path))

                    sys.exit()
            else:
                logger.error(
                    '{0} password is encrypted, but no decryption key was found\n'
                    'Please re-enter your cleartext password in the configuration file\n'
                    'Configuration file path => {0}\n'
                    'Exiting...'.format(provider_name,
                                        Configuration.get_configuration_file_path))

                sys.exit()

        return encrypted_password

    @classmethod
    def set_auto_generate_self_signed_certificate(cls, auto_generate_self_signed_certificate):
        cls._auto_generate_self_signed_certificate = auto_generate_self_signed_certificate

    @classmethod
    def set_certificate_file_path(cls, certificate_file_path):
        cls._certificate_file_path = certificate_file_path

    @classmethod
    def set_key_file_path(cls, key_file_path):
        cls._key_file_path = key_file_path
