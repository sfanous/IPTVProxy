import logging

from iptv_proxy.providers import ProvidersController
from iptv_proxy.providers.iptv_provider.html_template_engine import (
    ProviderHTMLTemplateEngine,
)
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants

logger = logging.getLogger(__name__)


class SmoothStreamsHTMLTemplateEngine(ProviderHTMLTemplateEngine):
    __slots__ = []

    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()

    @classmethod
    def render_configuration_template(
        cls, environment, configuration, active_providers_map_class
    ):
        provider_map_class = ProvidersController.get_provider_map_class(
            cls._provider_name
        )

        configuration_smoothstreams_template = environment.get_template(
            'configuration_smoothstreams.html'
        )

        configuration_smoothstreams_template_fields = {
            'configuration_smoothstreams_active': 'checked="checked"'
            if 'smoothstreams' in active_providers_map_class
            else '',
            'configuration_view247_selected': '',
            'configuration_viewmmasr_selected': '',
            'configuration_viewss_selected': '',
            'configuration_viewstvn_selected': '',
            'configuration_dap_selected': '',
            'configuration_deu_selected': '',
            'configuration_dna_selected': '',
            'configuration_deu_de_selected': '',
            'configuration_deu_nl_selected': '',
            'configuration_deu_uk_selected': '',
            'configuration_dnae_selected': '',
            'configuration_dnaw_selected': '',
            'configuration_deu_nl1_selected': '',
            'configuration_deu_nl2_selected': '',
            'configuration_deu_nl3_selected': '',
            'configuration_deu_nl4_selected': '',
            'configuration_deu_nl5_selected': '',
            'configuration_deu_uk1_selected': '',
            'configuration_deu_uk2_selected': '',
            'configuration_dnae1_selected': '',
            'configuration_dnae2_selected': '',
            'configuration_dnae3_selected': '',
            'configuration_dnae4_selected': '',
            'configuration_dnae6_selected': '',
            'configuration_dnaw1_selected': '',
            'configuration_dnaw2_selected': '',
            'configuration_dnaw3_selected': '',
            'configuration_dnaw4_selected': '',
            'configuration_smoothstreams_username': '',
            'configuration_smoothstreams_password': '',
            'configuration_smoothstreams_playlist_protocol_hls_selected': '',
            'configuration_smoothstreams_playlist_protocol_rtmp_selected': '',
            'configuration_smoothstreams_playlist_type_dynamic_selected': '',
            'configuration_smoothstreams_playlist_type_static_selected': '',
            'configuration_smoothstreams_epg_source_smoothstreams_selected': '',
            'configuration_smoothstreams_epg_source_fog_selected': '',
            'configuration_smoothstreams_epg_source_other_selected': '',
            'configuration_smoothstreams_epg_url': '',
        }

        if 'SMOOTHSTREAMS_SERVICE' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_{0}_selected'.format(
                    configuration['SMOOTHSTREAMS_SERVICE'].lower()
                )
            ] = 'selected="selected" '
        if 'SMOOTHSTREAMS_SERVER' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_{0}_selected'.format(
                    configuration['SMOOTHSTREAMS_SERVER'].lower().replace('-', '_')
                )
            ] = 'selected="selected" '
        if 'SMOOTHSTREAMS_USERNAME' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_smoothstreams_username'
            ] = configuration['SMOOTHSTREAMS_USERNAME']
        if 'SMOOTHSTREAMS_PASSWORD' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_smoothstreams_password'
            ] = configuration['SMOOTHSTREAMS_PASSWORD']
        if 'SMOOTHSTREAMS_PLAYLIST_PROTOCOL' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_smoothstreams_playlist_protocol_{0}_selected'.format(
                    configuration['SMOOTHSTREAMS_PLAYLIST_PROTOCOL'].lower()
                )
            ] = 'selected="selected" '
        if 'SMOOTHSTREAMS_PLAYLIST_TYPE' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_smoothstreams_playlist_type_{0}_selected'.format(
                    configuration['SMOOTHSTREAMS_PLAYLIST_TYPE'].lower()
                )
            ] = 'selected="selected" '
        if 'SMOOTHSTREAMS_EPG_SOURCE' in configuration:
            configuration_smoothstreams_template_fields[
                'configuration_smoothstreams_epg_source_{0}_selected'.format(
                    configuration['SMOOTHSTREAMS_EPG_SOURCE'].lower()
                )
            ] = 'selected="selected" '
        if 'SMOOTHSTREAMS_EPG_URL' in configuration:
            if configuration['SMOOTHSTREAMS_EPG_URL'] is None:
                configuration_smoothstreams_template_fields[
                    'configuration_smoothstreams_epg_url'
                ] = ''
            else:
                configuration_smoothstreams_template_fields[
                    'configuration_smoothstreams_epg_url'
                ] = configuration['SMOOTHSTREAMS_EPG_URL']

        return {
            provider_map_class.constants_class().PROVIDER_NAME: configuration_smoothstreams_template.render(
                configuration_smoothstreams_template_fields
            )
        }

    @classmethod
    def render_iptv_proxy_script_configuration_clear_template(cls, environment):
        iptv_proxy_script_configuration_smoothstreams_clear_template = environment.get_template(
            'iptv_proxy_script_configuration_smoothstreams_clear.js'
        )

        return iptv_proxy_script_configuration_smoothstreams_clear_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_declarations_template(cls, environment):
        iptv_proxy_script_configuration_smoothstreams_declarations_template = environment.get_template(
            'iptv_proxy_script_configuration_smoothstreams_declarations.js'
        )

        return iptv_proxy_script_configuration_smoothstreams_declarations_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_init_template(cls, environment):
        iptv_proxy_script_configuration_smoothstreams_init_template = environment.get_template(
            'iptv_proxy_script_configuration_smoothstreams_init.js'
        )

        return iptv_proxy_script_configuration_smoothstreams_init_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_reset_template(cls, environment):
        iptv_proxy_script_configuration_smoothstreams_reset_template = environment.get_template(
            'iptv_proxy_script_configuration_smoothstreams_reset.js'
        )

        return iptv_proxy_script_configuration_smoothstreams_reset_template.render().split(
            '\n'
        )

    @classmethod
    def render_iptv_proxy_script_configuration_update_template(cls, environment):
        iptv_proxy_script_configuration_smoothstreams_update_template = environment.get_template(
            'iptv_proxy_script_configuration_smoothstreams_update.js'
        )

        return iptv_proxy_script_configuration_smoothstreams_update_template.render().split(
            '\n'
        )
