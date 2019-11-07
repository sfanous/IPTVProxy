import logging
from abc import ABC
from abc import abstractmethod

from iptv_proxy.providers import ProvidersController

logger = logging.getLogger(__name__)


class ProviderHTMLTemplateEngine(ABC):
    __slots__ = []

    _provider_name = None

    @classmethod
    @abstractmethod
    def render_configuration_template(cls, environment, configuration, active_providers_map_class):
        pass

    @classmethod
    @abstractmethod
    def render_iptv_proxy_script_configuration_clear_template(cls, environment):
        pass

    @classmethod
    @abstractmethod
    def render_iptv_proxy_script_configuration_declarations_template(cls, environment):
        pass

    @classmethod
    @abstractmethod
    def render_iptv_proxy_script_configuration_init_template(cls, environment):
        pass

    @classmethod
    @abstractmethod
    def render_iptv_proxy_script_configuration_reset_template(cls, environment):
        pass

    @classmethod
    def render_iptv_proxy_script_configuration_toggle_password_template(cls, environment):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        iptv_proxy_script_configuration_provider_toggle_password_template = environment.get_template(
            'iptv_proxy_script_configuration_provider_toggle_password.js')

        iptv_proxy_script_configuration_provider_toggle_password_template_fields = {
            'provider_name_camel_case': '{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                        provider_map_class.constants_class().PROVIDER_NAME[1:])
        }

        return iptv_proxy_script_configuration_provider_toggle_password_template.render(
            iptv_proxy_script_configuration_provider_toggle_password_template_fields).lstrip()

    @classmethod
    @abstractmethod
    def render_iptv_proxy_script_configuration_update_template(cls, environment):
        pass


class XtreamCodesProviderHTMLTemplateEngine(ProviderHTMLTemplateEngine):
    __slots__ = []

    @classmethod
    def render_configuration_template(cls, environment, configuration, active_providers_map_class):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        configuration_xstream_provider_template = environment.get_template('configuration_xstream_provider.html')
        configuration_xstream_provider_template_fields = dict(
            provider_name_camel_case='{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                     provider_map_class.constants_class().PROVIDER_NAME[1:]),
            provider_name_pascal_case=provider_map_class.constants_class().PROVIDER_NAME,
            configuration_provider_url='',
            configuration_provider_username='',
            configuration_provider_password='',
            configuration_provider_playlist_protocol_hls_selected='',
            configuration_provider_playlist_protocol_mpegts_selected='',
            configuration_provider_playlist_type_static_selected='',
            configuration_provider_playlist_type_dynamic_selected='',
            configuration_provider_epg_source_provider_selected='',
            configuration_provider_epg_source_other_selected='',
            configuration_provider_epg_url=''
        )

        configuration_xstream_provider_template_fields['configuration_provider_active'] = \
            'checked="checked"' if cls._provider_name in active_providers_map_class else ''

        if '{0}_URL'.format(cls._provider_name.upper()) in configuration:
            configuration_xstream_provider_template_fields['configuration_provider_url'] = \
                configuration['{0}_URL'.format(cls._provider_name.upper())]

        if '{0}_USERNAME'.format(cls._provider_name.upper()) in configuration:
            configuration_xstream_provider_template_fields['configuration_provider_username'] = \
                configuration['{0}_USERNAME'.format(cls._provider_name.upper())]

        if '{0}_PASSWORD'.format(cls._provider_name.upper()) in configuration:
            configuration_xstream_provider_template_fields['configuration_provider_password'] = \
                configuration['{0}_PASSWORD'.format(cls._provider_name.upper())]

        if '{0}_PLAYLIST_PROTOCOL'.format(cls._provider_name.upper()) in configuration:
            if configuration['{0}_PLAYLIST_PROTOCOL'.format(cls._provider_name.upper())].lower() == 'hls':
                configuration_xstream_provider_template_fields[
                    'configuration_provider_playlist_protocol_hls_selected'] = 'selected="selected" '
            elif configuration['{0}_PLAYLIST_PROTOCOL'.format(cls._provider_name.upper())].lower() == 'mpegts':
                configuration_xstream_provider_template_fields[
                    'configuration_provider_playlist_protocol_mpegts_selected'] = 'selected="selected" '

        if '{0}_PLAYLIST_TYPE'.format(cls._provider_name.upper()) in configuration:
            if configuration['{0}_PLAYLIST_TYPE'.format(cls._provider_name.upper())].lower() == 'dynamic':
                configuration_xstream_provider_template_fields[
                    'configuration_provider_playlist_type_dynamic_selected'] = 'selected="selected" '
            elif configuration['{0}_PLAYLIST_TYPE'.format(cls._provider_name.upper())].lower() == 'static':
                configuration_xstream_provider_template_fields[
                    'configuration_provider_playlist_type_static_selected'] = 'selected="selected" '

        if '{0}_EPG_SOURCE'.format(cls._provider_name.upper()) in configuration:
            if configuration['{0}_EPG_SOURCE'.format(cls._provider_name.upper())].lower() == 'other':
                configuration_xstream_provider_template_fields[
                    'configuration_provider_epg_source_other_selected'] = 'selected="selected" '
            elif configuration['{0}_EPG_SOURCE'.format(cls._provider_name.upper())].lower() == cls._provider_name:
                configuration_xstream_provider_template_fields[
                    'configuration_provider_epg_source_provider_selected'] = 'selected="selected" '
        if '{0}_EPG_URL'.format(cls._provider_name.upper()) in configuration:
            if configuration['{0}_EPG_URL'.format(cls._provider_name.upper())] is not None:
                configuration_xstream_provider_template_fields[
                    'configuration_provider_epg_url'] = \
                    configuration['{0}_EPG_URL'.format(cls._provider_name.upper())]

        return {provider_map_class.constants_class().PROVIDER_NAME: configuration_xstream_provider_template.render(
            configuration_xstream_provider_template_fields)}

    @classmethod
    def render_iptv_proxy_script_configuration_clear_template(cls, environment):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        iptv_proxy_script_configuration_xstream_provider_clear_template = environment.get_template(
            'iptv_proxy_script_configuration_xstream_provider_clear.js')

        iptv_proxy_script_configuration_xstream_provider_clear_template_fields = {
            'provider_name_camel_case': '{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                        provider_map_class.constants_class().PROVIDER_NAME[1:])
        }

        return iptv_proxy_script_configuration_xstream_provider_clear_template.render(
            iptv_proxy_script_configuration_xstream_provider_clear_template_fields).split('\n')

    @classmethod
    def render_iptv_proxy_script_configuration_declarations_template(cls, environment):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        iptv_proxy_script_configuration_xstream_provider_declarations_template = environment.get_template(
            'iptv_proxy_script_configuration_xstream_provider_declarations.js')

        iptv_proxy_script_configuration_xstream_provider_declarations_template_fields = {
            'provider_name_camel_case': '{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                        provider_map_class.constants_class().PROVIDER_NAME[1:])
        }

        return iptv_proxy_script_configuration_xstream_provider_declarations_template.render(
            iptv_proxy_script_configuration_xstream_provider_declarations_template_fields).split('\n')

    @classmethod
    def render_iptv_proxy_script_configuration_init_template(cls, environment):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        iptv_proxy_script_configuration_xstream_provider_init_template = environment.get_template(
            'iptv_proxy_script_configuration_xstream_provider_init.js')

        iptv_proxy_script_configuration_xstream_provider_init_template_fields = {
            'provider_name_camel_case': '{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                        provider_map_class.constants_class().PROVIDER_NAME[1:])
        }

        return iptv_proxy_script_configuration_xstream_provider_init_template.render(
            iptv_proxy_script_configuration_xstream_provider_init_template_fields).split('\n')

    @classmethod
    def render_iptv_proxy_script_configuration_reset_template(cls, environment):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        iptv_proxy_script_configuration_xstream_provider_reset_template = environment.get_template(
            'iptv_proxy_script_configuration_xstream_provider_reset.js')

        iptv_proxy_script_configuration_xstream_provider_reset_template_fields = {
            'provider_name_camel_case': '{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                        provider_map_class.constants_class().PROVIDER_NAME[1:]),
            'provider_name_snake_case': cls._provider_name.lower()
        }

        return iptv_proxy_script_configuration_xstream_provider_reset_template.render(
            iptv_proxy_script_configuration_xstream_provider_reset_template_fields).split('\n')

    @classmethod
    def render_iptv_proxy_script_configuration_update_template(cls, environment):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        iptv_proxy_script_configuration_xstream_provider_update_template = environment.get_template(
            'iptv_proxy_script_configuration_xstream_provider_update.js')

        iptv_proxy_script_configuration_xstream_provider_update_template_fields = {
            'provider_name_camel_case': '{0}{1}'.format(provider_map_class.constants_class().PROVIDER_NAME[0].lower(),
                                                        provider_map_class.constants_class().PROVIDER_NAME[1:]),
            'provider_name_snake_case': cls._provider_name.lower()
        }

        return iptv_proxy_script_configuration_xstream_provider_update_template.render(
            iptv_proxy_script_configuration_xstream_provider_update_template_fields).split('\n')
