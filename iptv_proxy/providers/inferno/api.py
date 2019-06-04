import logging

from rwlock import RWLock

from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.providers import ProvidersController
from iptv_proxy.providers.inferno.constants import InfernoConstants
from iptv_proxy.providers.iptv_provider.api import SmartersProvider
from iptv_proxy.security import SecurityManager

logger = logging.getLogger(__name__)


class Inferno(SmartersProvider):
    __slots__ = []

    _do_reduce_hls_stream_delay = True
    _do_reduce_hls_stream_delay_lock = RWLock()
    _provider_name = InfernoConstants.PROVIDER_NAME.lower()

    @classmethod
    def _generate_playlist_m3u8_static_track_url(cls, track_information, **kwargs):
        channel_number = kwargs['channel_number']
        playlist_protocol = kwargs['playlist_protocol']

        username = Configuration.get_configuration_parameter('INFERNO_USERNAME')
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('INFERNO_PASSWORD')).decode()

        track_information.append(
            '{0}{1}{2}/{3}/{4}{5}\n'.format(
                ProvidersController.get_provider_map_class(cls._provider_name).constants_class().BASE_URL,
                'live/' if playlist_protocol == 'hls'
                else '',
                username,
                password,
                channel_number,
                '.m3u8' if playlist_protocol == 'hls'
                else ''))

    @classmethod
    def _initialize(cls, **kwargs):
        pass

    @classmethod
    def _initialize_class_variables(cls):
        try:
            cls.set_do_reduce_hls_stream_delay(
                OptionalSettings.get_optional_settings_parameter('reduce_inferno_delay'))
        except KeyError:
            pass

    @classmethod
    def _retrieve_fresh_authorization_token(cls):
        return None

    @classmethod
    def _terminate(cls, **kwargs):
        pass
