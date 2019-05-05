import logging

import requests

from iptv_proxy.providers import ProvidersController

logger = logging.getLogger(__name__)


class ProviderValidations(object):
    __slots__ = []

    _provider_name = None

    @classmethod
    def is_valid_epg_source(cls, epg_source):
        is_valid_epg_source = True

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        if epg_source not in provider_map_class.constants_class().VALID_EPG_SOURCE_VALUES:
            is_valid_epg_source = False

        return is_valid_epg_source

    @classmethod
    def is_valid_epg_url(cls, epg_url):
        is_valid_epg_url = True

        try:
            requests.head(epg_url)
        except requests.RequestException:
            is_valid_epg_url = False

        return is_valid_epg_url

    @classmethod
    def is_valid_password(cls, password):
        return len(password)

    @classmethod
    def is_valid_playlist_protocol(cls, playlist_protocol):
        is_valid_playlist_protocol = True

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        if playlist_protocol not in provider_map_class.constants_class().VALID_PLAYLIST_PROTOCOL_VALUES:
            is_valid_playlist_protocol = False

        return is_valid_playlist_protocol

    @classmethod
    def is_valid_playlist_type(cls, playlist_type):
        is_valid_playlist_type = True

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        if playlist_type not in provider_map_class.constants_class().VALID_PLAYLIST_TYPE_VALUES:
            is_valid_playlist_type = False

        return is_valid_playlist_type

    @classmethod
    def is_valid_server(cls, server):
        is_valid_server = True

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        if server not in provider_map_class.constants_class().VALID_SERVER_VALUES:
            is_valid_server = False

        return is_valid_server

    @classmethod
    def is_valid_service(cls, service):
        is_valid_service = True

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        if service not in provider_map_class.constants_class().VALID_SERVICE_VALUES:
            is_valid_service = False

        return is_valid_service

    @classmethod
    def is_valid_username(cls, username):
        return len(username)
