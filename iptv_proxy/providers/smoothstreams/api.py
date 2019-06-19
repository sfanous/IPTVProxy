import logging
import re
import sys
import traceback
import urllib.parse
from datetime import datetime
from datetime import timedelta
from threading import Timer

import jsonpickle
import m3u8
import pytz
import requests
import tzlocal
from rwlock import RWLock

from iptv_proxy.configuration import Configuration
from iptv_proxy.enums import M388PlaylistSortOrder
from iptv_proxy.providers.iptv_provider.api import Provider
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants
from iptv_proxy.providers.smoothstreams.data_access import SmoothStreamsDatabaseAccess
from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsSetting
from iptv_proxy.providers.smoothstreams.db import SmoothStreamsDatabase
from iptv_proxy.providers.smoothstreams.epg import SmoothStreamsEPG
from iptv_proxy.proxy import IPTVProxy
from iptv_proxy.security import SecurityManager
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class SmoothStreams(Provider):
    __slots__ = []

    _nimble_session_id_map = {}
    _nimble_session_id_map_lock = RWLock()
    _refresh_session_timer = None
    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
    _session = {}
    _session_lock = RWLock()

    @classmethod
    def _cancel_refresh_session_timer(cls):
        if cls._refresh_session_timer:
            cls._refresh_session_timer.cancel()
            cls._refresh_session_timer = None

    @classmethod
    def _clear_nimble_session_id_map(cls):
        with cls._nimble_session_id_map_lock.writer_lock:
            cls._nimble_session_id_map = {}

    @classmethod
    def _do_refresh_session(cls):
        try:
            if datetime.now(pytz.utc) < (cls._get_session_parameter('expires_on') - timedelta(minutes=30)):
                return False
            else:
                logger.debug('SmoothStreams session\n'
                             'Status => Expired\n'
                             'Action => Retrieve it')

                return True
        except KeyError:
            logger.error('SmoothStreams session\n'
                         'Status => Never retrieved\n'
                         'Action => Retrieve it')

            return True

    @classmethod
    def _generate_playlist_m3u8_static_track_url(cls, track_information, **kwargs):
        channel_number = kwargs['channel_number']
        playlist_protocol = kwargs['playlist_protocol']
        authorization_token = kwargs['authorization_token']

        track_information.append(
            '{0}://{1}.smoothstreams.tv:{2}/{3}/ch{4:02}q1.stream{5}?wmsAuthSign={6}\n'.format(
                'https' if playlist_protocol in ['hls', 'mpegts']
                else 'rtmp',
                Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVER'),
                '443' if playlist_protocol in ['hls', 'mpegts']
                else '3635',
                Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVICE'),
                int(channel_number),
                '/mpeg.2ts' if playlist_protocol == 'mpegts'
                else '',
                authorization_token))

    @classmethod
    def _get_session_parameter(cls, parameter_name):
        with cls._session_lock.reader_lock:
            return cls._session[parameter_name]

    @classmethod
    def _get_target_nimble_session_id(cls, hijacked_nimble_session_id):
        with cls._nimble_session_id_map_lock.reader_lock:
            return cls._nimble_session_id_map.get(hijacked_nimble_session_id)

    @classmethod
    def _hijack_nimble_session_id(cls, hijacked_nimble_session_id, hijacking_nimble_session_id):
        with cls._nimble_session_id_map_lock.writer_lock:
            cls._nimble_session_id_map[hijacked_nimble_session_id] = hijacking_nimble_session_id

    @classmethod
    def _initialize(cls, **kwargs):
        do_refresh_session = False

        if 'do_refresh_session' in kwargs:
            do_refresh_session = kwargs['do_refresh_session']
        else:
            with SmoothStreamsDatabase.get_access_lock().shared_lock:
                db_session = SmoothStreamsDatabase.create_session()

                try:
                    setting_row = SmoothStreamsDatabaseAccess.query_setting(db_session, 'session')

                    if setting_row is not None:
                        cls._session = jsonpickle.decode(setting_row.value)

                        current_date_time_in_utc = datetime.now(pytz.utc)

                        if current_date_time_in_utc < cls._session['expires_on']:
                            logger.debug('Loaded SmoothStreams session\n'
                                         'Authorization token => {0}\n'
                                         'Expires on          => {1}'.format(cls._session['authorization_token'],
                                                                             cls._session['expires_on'].astimezone(
                                                                                 tzlocal.get_localzone()).strftime(
                                                                                 '%Y-%m-%d %H:%M:%S%z')))
                        else:
                            do_refresh_session = True
                    else:
                        do_refresh_session = True
                finally:
                    db_session.close()

        if do_refresh_session:
            cls.refresh_session(force_refresh=True)

    @classmethod
    def _map_nimble_session_id(cls,
                               client_ip_address,
                               channel_number,
                               client_uuid,
                               nimble_session_id,
                               authorization_token):
        if authorization_token != cls._get_session_parameter('authorization_token'):
            target_nimble_session_id = cls._get_target_nimble_session_id(nimble_session_id)

            if not target_nimble_session_id:
                logger.debug('SmoothStreams authorization token {0} in request from {1}/{2} expired'.format(
                    authorization_token,
                    client_ip_address,
                    client_uuid))

                try:
                    response_text = cls.download_playlist_m3u8(client_ip_address,
                                                               client_uuid,
                                                               '/playlist.m3u8',
                                                               dict(channel_number=channel_number,
                                                                    protocol='hls'))

                    m3u8_object = m3u8.loads(response_text)

                    requested_path_with_query_string = '/{0}'.format(m3u8_object.data['playlists'][0]['uri'])
                    requested_url_components = urllib.parse.urlparse(requested_path_with_query_string)
                    requested_query_string_parameters = dict(urllib.parse.parse_qsl(requested_url_components.query))

                    target_nimble_session_id = requested_query_string_parameters.get('nimblesessionid',
                                                                                     nimble_session_id)

                    logger.debug('Hijacking SmoothStreams session\n'
                                 'Expired nimble session ID => {0}\n'
                                 'Target nimble session ID  => {1}'.format(nimble_session_id, target_nimble_session_id))
                    cls._hijack_nimble_session_id(nimble_session_id, target_nimble_session_id)
                except requests.exceptions.HTTPError:
                    target_nimble_session_id = nimble_session_id

                    (type_, value_, traceback_) = sys.exc_info()
                    logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))
        else:
            target_nimble_session_id = nimble_session_id

        return target_nimble_session_id

    @classmethod
    def _refresh_session(cls):
        requests_session = requests.Session()

        if Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVICE') == 'viewmmasr':
            url = 'https://www.mma-tv.net/loginForm.php'
        else:
            url = 'https://auth.smoothstreams.tv/hash_api.php'

        username = Configuration.get_configuration_parameter('SMOOTHSTREAMS_USERNAME')
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('SMOOTHSTREAMS_PASSWORD')).decode()
        site = Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVICE')

        logger.debug('Retrieving SmoothStreams authorization token\n'
                     'URL => {0}\n'
                     '  Parameters\n'
                     '    username => {0}\n'
                     '    password => {1}\n'
                     '    site     => {2}'.format(url, username, '\u2022' * len(password), site))

        response = Utility.make_http_request(requests_session.get,
                                             url,
                                             params={
                                                 'username': username,
                                                 'password': password,
                                                 'site': site
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict())

        response_status_code = response.status_code
        if response_status_code != requests.codes.OK and response_status_code != requests.codes.NOT_FOUND:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

        logger.trace(Utility.assemble_response_from_log_message(response,
                                                                is_content_json=True,
                                                                do_print_content=True))

        authorization_token_response = response.json()
        session = {}

        if 'code' in authorization_token_response:
            if authorization_token_response['code'] == '0':
                logger.error('Failed to retrieve SmoothStreams authorization token\n'
                             'Error => {0}'.format(authorization_token_response['error']))
            elif authorization_token_response['code'] == '1':
                session['authorization_token'] = authorization_token_response['hash']
                session['expires_on'] = datetime.now(pytz.utc) + timedelta(
                    seconds=(authorization_token_response['valid'] * 60))
                session['requests_session'] = requests_session

                logger.info('Retrieved SmoothStreams authorization token\n'
                            'Hash       => {0}\n'
                            'Expires On => {1}'.format(session['authorization_token'],
                                                       session['expires_on'].astimezone(
                                                           tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S%z')))
        else:
            logger.error('Failed to retrieve SmoothStreams authorization token\n'
                         'Error => JSON response contains no [\'code\'] field')

        if response_status_code != requests.codes.OK:
            response.raise_for_status()

        return session

    @classmethod
    def _retrieve_fresh_authorization_token(cls):
        try:
            session = cls._refresh_session()

            return session['authorization_token']
        except (KeyError, requests.exceptions.HTTPError):
            logger.error('Failed to retrieve a fresh SmoothStreams authorization token')

    @classmethod
    def _set_session_parameter(cls, parameter_name, parameter_value):
        with cls._session_lock.writer_lock:
            cls._session[parameter_name] = parameter_value

    @classmethod
    def _terminate(cls, **kwargs):
        pass

    @classmethod
    def _timed_refresh_session(cls):
        logger.debug('SmoothStreams refresh session timer triggered')

        cls.refresh_session(force_refresh=True)

    @classmethod
    def download_chunks_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        authorization_token = requested_query_string_parameters.get('wmsAuthSign')
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        nimble_session_id = requested_query_string_parameters.get('nimblesessionid')

        nimble_session_id = cls._map_nimble_session_id(client_ip_address,
                                                       channel_number,
                                                       client_uuid,
                                                       nimble_session_id,
                                                       authorization_token)

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)

        authorization_token = cls._get_session_parameter('authorization_token')
        requests_session = cls._get_session_parameter('requests_session')

        target_url = 'https://{0}.smoothstreams.tv/{1}/ch{2}q1.stream{3}'.format(
            Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVER'),
            Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVICE'),
            channel_number,
            re.sub(r'(/.*)?(/.*\.m3u8)', r'\2', requested_path))

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_number  => {2}\n'
                     '    client_uuid     => {3}\n'
                     'Target path    => {4}\n'
                     '  Parameters\n'
                     '    nimblesessionid => {5}\n'
                     '    wmsAuthSign     => {6}'.format(client_ip_address,
                                                         requested_path,
                                                         channel_number,
                                                         client_uuid,
                                                         target_url,
                                                         nimble_session_id,
                                                         authorization_token))

        response = Utility.make_http_request(requests_session.get,
                                             target_url,
                                             params={
                                                 'nimblesessionid': nimble_session_id,
                                                 'wmsAuthSign': authorization_token
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response,
                                                                    is_content_text=True,
                                                                    do_print_content=True))

            return response.text.replace('.ts?', '.ts?channel_number={0}&client_uuid={1}&http_token={2}&'.format(
                channel_number,
                client_uuid,
                urllib.parse.quote(http_token) if http_token
                else ''))
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def download_playlist_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        channel_number = requested_query_string_parameters.get('channel_number')
        http_token = requested_query_string_parameters.get('http_token')
        protocol = requested_query_string_parameters.get('protocol')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)
        cls.refresh_session()

        if protocol == 'hls':
            authorization_token = cls._get_session_parameter('authorization_token')
            requests_session = cls._get_session_parameter('requests_session')

            target_url = 'https://{0}.smoothstreams.tv/{1}/ch{2}q1.stream{3}'.format(
                Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVER'),
                Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVICE'),
                channel_number,
                re.sub(r'(/.*)?(/.*\.m3u8)', r'\2', requested_path))

            logger.debug('Proxying request\n'
                         'Source IP      => {0}\n'
                         'Requested path => {1}\n'
                         '  Parameters\n'
                         '    channel_number => {2}\n'
                         '    client_uuid    => {3}\n'
                         '    protocol       => {4}\n'
                         'Target path    => {5}\n'
                         '  Parameters\n'
                         '    wmsAuthSign    => {6}'.format(client_ip_address,
                                                            requested_path,
                                                            channel_number,
                                                            client_uuid,
                                                            protocol,
                                                            target_url,
                                                            authorization_token))

            response = Utility.make_http_request(requests_session.get,
                                                 target_url,
                                                 params={
                                                     'wmsAuthSign': authorization_token
                                                 },
                                                 headers=requests_session.headers,
                                                 cookies=requests_session.cookies.get_dict())

            if response.status_code == requests.codes.OK:
                logger.trace(Utility.assemble_response_from_log_message(response,
                                                                        is_content_text=True,
                                                                        do_print_content=True))

                return response.text.replace('chunks.m3u8?',
                                             'chunks.m3u8?channel_number={0}&client_uuid={1}&http_token={2}&'.format(
                                                 channel_number,
                                                 client_uuid,
                                                 urllib.parse.quote(http_token) if http_token
                                                 else ''))
            else:
                logger.error(Utility.assemble_response_from_log_message(response))

                response.raise_for_status()
        elif protocol == 'mpegts':
            authorization_token = cls._get_session_parameter('authorization_token')

            return '#EXTM3U\n' \
                   '#EXTINF:-1 ,{0}\n' \
                   'https://{1}.smoothstreams.tv:443/{2}/ch{3}q1.stream/mpeg.2ts?' \
                   'wmsAuthSign={4}'.format(SmoothStreamsEPG.get_channel_name(int(channel_number)),
                                            Configuration.get_configuration_parameter(
                                                'SMOOTHSTREAMS_SERVER'),
                                            Configuration.get_configuration_parameter(
                                                'SMOOTHSTREAMS_SERVICE'),
                                            channel_number,
                                            authorization_token)
        elif protocol == 'rtmp':
            authorization_token = cls._get_session_parameter('authorization_token')

            return '#EXTM3U\n' \
                   '#EXTINF:-1 ,{0}\n' \
                   'rtmp://{1}.smoothstreams.tv:3635/{2}/ch{3}q1.stream?' \
                   'wmsAuthSign={4}'.format(SmoothStreamsEPG.get_channel_name(int(channel_number)),
                                            Configuration.get_configuration_parameter(
                                                'SMOOTHSTREAMS_SERVER'),
                                            Configuration.get_configuration_parameter(
                                                'SMOOTHSTREAMS_SERVICE'),
                                            channel_number,
                                            authorization_token)

    @classmethod
    def download_ts_file(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        authorization_token = requested_query_string_parameters.get('wmsAuthSign')
        channel_number = requested_query_string_parameters.get('channel_number')
        nimble_session_id = requested_query_string_parameters.get('nimblesessionid')

        IPTVProxy.refresh_serviceable_clients(client_uuid, client_ip_address)

        requests_session = cls._get_session_parameter('requests_session')

        target_url = 'https://{0}.smoothstreams.tv/{1}/ch{2}q1.stream{3}'.format(
            Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVER'),
            Configuration.get_configuration_parameter('SMOOTHSTREAMS_SERVICE'),
            channel_number,
            re.sub(r'(/.*)?(/.*\.ts)', r'\2', requested_path))

        logger.debug('Proxying request\n'
                     'Source IP      => {0}\n'
                     'Requested path => {1}\n'
                     '  Parameters\n'
                     '    channel_number  => {2}\n'
                     '    client_uuid     => {3}\n'
                     'Target path    => {4}\n'
                     '  Parameters\n'
                     '    nimblesessionid => {5}\n'
                     '    wmsAuthSign     => {6}'.format(client_ip_address,
                                                         requested_path,
                                                         channel_number,
                                                         client_uuid,
                                                         target_url,
                                                         nimble_session_id,
                                                         authorization_token))

        response = Utility.make_http_request(requests_session.get,
                                             target_url,
                                             params={
                                                 'nimblesessionid': nimble_session_id,
                                                 'wmsAuthSign': authorization_token
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict())

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response,
                                                                    is_content_binary=True))

            return response.content
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def generate_playlist_m3u8_tracks(cls,
                                      generate_playlist_m3u8_tracks_mapping,
                                      sort_by=M388PlaylistSortOrder.CHANNEL_NUMBER.value):
        return super().generate_playlist_m3u8_tracks(generate_playlist_m3u8_tracks_mapping, sort_by=sort_by)

    @classmethod
    def refresh_session(cls, force_refresh=False):
        with cls._session_lock.writer_lock:
            do_start_timer = False

            if force_refresh or cls._do_refresh_session():
                do_start_timer = True

                cls._clear_nimble_session_id_map()

                session = cls._refresh_session()

                if session:
                    cls._session = session

                    with SmoothStreamsDatabase.get_write_lock(), SmoothStreamsDatabase.get_access_lock().shared_lock:
                        db_session = SmoothStreamsDatabase.create_session()

                        try:
                            db_session.merge(SmoothStreamsSetting('session', jsonpickle.encode(cls._session)))
                            db_session.commit()
                        except Exception:
                            (type_, value_, traceback_) = sys.exc_info()
                            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

                            db_session.rollback()
                        finally:
                            db_session.close()

                if cls._refresh_session_timer:
                    cls._refresh_session_timer.cancel()
            elif not cls._refresh_session_timer:
                do_start_timer = True

            if do_start_timer:
                interval = (cls._get_session_parameter('expires_on') - datetime.now(pytz.utc)).total_seconds() - 1800
                cls._refresh_session_timer = Timer(interval, cls._timed_refresh_session)
                cls._refresh_session_timer.daemon = True
                cls._refresh_session_timer.start()

                logger.debug('Started SmoothStreams session refresh timer\n'
                             'Interval => {0} seconds'.format(interval))
