from abc import ABC, abstractmethod


class IPTVProxyProvider(ABC):
    @classmethod
    @abstractmethod
    def download_chunks_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        pass

    @classmethod
    @abstractmethod
    def download_playlist_m3u8(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        pass

    @classmethod
    @abstractmethod
    def download_ts_file(cls, client_ip_address, client_uuid, requested_path, requested_query_string_parameters):
        pass

    @classmethod
    @abstractmethod
    def generate_playlist_m3u8(cls,
                               is_server_secure,
                               client_ip_address,
                               client_uuid,
                               requested_query_string_parameters):
        pass

    @classmethod
    @abstractmethod
    def generate_playlist_m3u8_track_url(cls, generate_playlist_m3u8_track_url_mapping):
        pass

    @classmethod
    @abstractmethod
    def generate_playlist_m3u8_tracks(cls, generate_playlist_m3u8_tracks_mapping):
        pass

    @classmethod
    @abstractmethod
    def get_supported_protocols(cls):
        pass

    @classmethod
    @abstractmethod
    def initialize(cls):
        pass

    @classmethod
    @abstractmethod
    def terminate(cls):
        pass
