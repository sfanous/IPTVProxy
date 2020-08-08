import logging

from iptv_proxy.providers import ProvidersController
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    ProviderHTMLTemplateEngine,
)
from iptv_proxy.providers.vaderstreams.constants import VaderStreamsConstants

logger = logging.getLogger(__name__)


class VaderStreamsHTMLTemplateEngine(ProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = VaderStreamsConstants.PROVIDER_NAME.lower()

    @classmethod
    def render_configuration_template(
        cls, environment, configuration, active_providers_map_class
    ):
        provider_map_class = ProvidersController.get_provider_map_class(
            cls._provider_name
        )

        configuration_vaderstreams_template = environment.get_template(
            'configuration_vaderstreams.html'
        )

        configuration_vaderstreams_template_fields = {
            'configuration_vaderstreams_active': 'checked="checked"'
            if 'vaderstreams' in active_providers_map_class
            else '',
            'configuration_vaderstreams_username': '',
            'configuration_vaderstreams_password': '',
            'configuration_vaderstreams_playlist_protocol_hls_selected': '',
            'configuration_vaderstreams_playlist_protocol_mpegts_selected': '',
            'configuration_vaderstreams_playlist_type_dynamic_selected': '',
            'configuration_vaderstreams_playlist_type_static_selected': '',
            'configuration_vaderstreams_epg_source_vaderstreams_selected': '',
            'configuration_vaderstreams_epg_source_other_selected': '',
            'configuration_vaderstreams_epg_url': '',
        }

        if 'VADERSTREAMS_SERVER' in configuration:
            configuration_vaderstreams_template_fields[
                'configuration_{0}_selected'.format(
                    configuration['VADERSTREAMS_SERVER'].lower().replace('-', '_')
                )
            ] = 'selected="selected" '
        if 'VADERSTREAMS_USERNAME' in configuration:
            configuration_vaderstreams_template_fields[
                'configuration_vaderstreams_username'
            ] = configuration['VADERSTREAMS_USERNAME']
        if 'VADERSTREAMS_PASSWORD' in configuration:
            configuration_vaderstreams_template_fields[
                'configuration_vaderstreams_password'
            ] = configuration['VADERSTREAMS_PASSWORD']
        if 'VADERSTREAMS_PLAYLIST_PROTOCOL' in configuration:
            configuration_vaderstreams_template_fields[
                'configuration_vaderstreams_playlist_protocol_{0}_selected'.format(
                    configuration['VADERSTREAMS_PLAYLIST_PROTOCOL'].lower()
                )
            ] = 'selected="selected" '
        if 'VADERSTREAMS_PLAYLIST_TYPE' in configuration:
            configuration_vaderstreams_template_fields[
                'configuration_vaderstreams_playlist_type_{0}_selected'.format(
                    configuration['VADERSTREAMS_PLAYLIST_TYPE'].lower()
                )
            ] = 'selected="selected" '
        if 'VADERSTREAMS_EPG_SOURCE' in configuration:
            configuration_vaderstreams_template_fields[
                'configuration_vaderstreams_epg_source_{0}_selected'.format(
                    configuration['VADERSTREAMS_EPG_SOURCE'].lower()
                )
            ] = 'selected="selected" '
        if 'VADERSTREAMS_EPG_URL' in configuration:
            if configuration['VADERSTREAMS_EPG_URL'] is None:
                configuration_vaderstreams_template_fields[
                    'configuration_vaderstreams_epg_url'
                ] = ''
            else:
                configuration_vaderstreams_template_fields[
                    'configuration_vaderstreams_epg_url'
                ] = configuration['VADERSTREAMS_EPG_URL']

        return {
            provider_map_class.constants_class().PROVIDER_NAME: configuration_vaderstreams_template.render(
                configuration_vaderstreams_template_fields
            )
        }

    @classmethod
    def render_iptv_proxy_script_configuration_clear_template(cls, environment):
        iptv_proxy_script_configuration_vaderstreams_clear_template = environment.get_template(
            'iptv_proxy_script_configuration_vaderstreams_clear.js'
        )

        return iptv_proxy_script_configuration_vaderstreams_clear_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_declarations_template(cls, environment):
        iptv_proxy_script_configuration_vaderstreams_declarations_template = environment.get_template(
            'iptv_proxy_script_configuration_vaderstreams_declarations.js'
        )

        return iptv_proxy_script_configuration_vaderstreams_declarations_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_init_template(cls, environment):
        iptv_proxy_script_configuration_vaderstreams_init_template = environment.get_template(
            'iptv_proxy_script_configuration_vaderstreams_init.js'
        )

        return iptv_proxy_script_configuration_vaderstreams_init_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_reset_template(cls, environment):
        iptv_proxy_script_configuration_vaderstreams_reset_template = environment.get_template(
            'iptv_proxy_script_configuration_vaderstreams_reset.js'
        )

        return iptv_proxy_script_configuration_vaderstreams_reset_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_update_template(cls, environment):
        iptv_proxy_script_configuration_vaderstreams_update_template = environment.get_template(
            'iptv_proxy_script_configuration_vaderstreams_update.js'
        )

        return iptv_proxy_script_configuration_vaderstreams_update_template.render().split(
            '\n'
        )
