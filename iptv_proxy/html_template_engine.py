import base64
import html
import json
import logging
import pickle
import urllib.parse
from datetime import datetime
from datetime import timedelta

import pytz
import tzlocal
from jinja2 import Environment
from jinja2 import FileSystemBytecodeCache
from jinja2 import FileSystemLoader
from jinja2 import StrictUndefined
from jinja2 import select_autoescape

from iptv_proxy.configuration import Configuration
from iptv_proxy.constants import TEMPLATES_BYTECODE_CACHE_DIRECTORY_PATH
from iptv_proxy.constants import TEMPLATES_DIRECTORY_PATH
from iptv_proxy.constants import VERSION
from iptv_proxy.enums import RecordingStatus
from iptv_proxy.recorder import PVR
from iptv_proxy.utilities import Utility

logger = logging.getLogger(__name__)


class HTMLTemplateEngine(object):
    __slots__ = ['_configuration']

    _environment = None

    @classmethod
    def render_errors_template(cls, http_error_code, http_error_title, http_error_details):
        errors_template = cls._environment.get_template('errors.html')

        errors_template_fields = {
            'iptv_proxy_version': VERSION,
            'http_error_code': http_error_code,
            'http_error_title': http_error_title,
            'http_error_details': http_error_details
        }

        return errors_template.render(errors_template_fields)

    @classmethod
    def render_login_template(cls):
        login_template = cls._environment.get_template('login.html')

        login_template_fields = {
            'iptv_proxy_version': VERSION
        }

        return login_template.render(login_template_fields)

    @classmethod
    def initialize(cls):
        cls._environment = Environment(
            undefined=StrictUndefined,
            autoescape=select_autoescape(enabled_extensions=()),
            loader=FileSystemLoader(TEMPLATES_DIRECTORY_PATH),
            bytecode_cache=FileSystemBytecodeCache(directory=TEMPLATES_BYTECODE_CACHE_DIRECTORY_PATH))

    def __init__(self):
        self._configuration = Configuration.get_configuration_copy()

    def _render_about_div_template(self):
        about_div_template = self._environment.get_template('about_div.html')

        about_div_template_fields = {
            'iptv_proxy_version': VERSION
        }

        return about_div_template.render(about_div_template_fields)

    def _render_alert_li_template(self, alert_li_id_prefix, alert_li_id_suffix):
        alert_li_template = self._environment.get_template('alert_li.html')

        alert_li_template_fields = {
            'alert_li_id_prefix': alert_li_id_prefix,
            'alert_li_id_suffix': alert_li_id_suffix
        }

        return alert_li_template.render(alert_li_template_fields)

    def _render_buttons_li_template(self, buttons_li_id_prefix, buttons_li_id_suffix):
        buttons_li_template = self._environment.get_template('buttons_li.html')

        buttons_li_template_fields = {
            'buttons_li_id_prefix': buttons_li_id_prefix,
            'buttons_li_id_suffix': buttons_li_id_suffix
        }

        return buttons_li_template.render(buttons_li_template_fields)

    def _render_channel_li_template(self,
                                    is_server_secure,
                                    authorization_required,
                                    client_ip_address_type,
                                    client_uuid,
                                    channel,
                                    channel_row_index,
                                    channel_rows,
                                    provider):
        channel_li_template = self._environment.get_template('channel_li.html')

        if channel_row_index == len(channel_rows) - 1:
            channel_li_border = ' w3-border-0'
        else:
            channel_li_border = ''

        channel_li_id_prefix = channel.xmltv_id
        channel_li_channel_name = html.escape(channel.display_names[0].text)
        channel_li_channel_img_src = channel.icons[0].source.format(
            's' if is_server_secure
            else '',
            self._configuration['SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value)],
            self._configuration['SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                                             else '')],
            '?http_token={0}'.format(
                urllib.parse.quote(self._configuration['SERVER_PASSWORD'])) if authorization_required
            else '')
        channel_li_channel_number = channel.number

        channel_sources = {'type': 'live'}
        for provider_supported_protocol in provider.api_class().get_supported_protocols():
            if provider_supported_protocol != 'mpegts':
                channel_sources[provider_supported_protocol] = {}

                channel_sources[provider_supported_protocol]['videoSource'] = \
                    provider.api_class().generate_playlist_m3u8_track_url(
                        dict(channel_number=channel_li_channel_number,
                             client_uuid=client_uuid,
                             http_token=self._configuration['SERVER_PASSWORD'] if authorization_required
                             else None,
                             is_server_secure=is_server_secure,
                             playlist_protocol=provider_supported_protocol,
                             server_hostname=self._configuration[
                                 'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value)],
                             server_port=self._configuration['SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                                                                          else '')]))

        channel_li_template_fields = {
            'channel_li_border': channel_li_border,
            'channel_li_id_prefix': channel_li_id_prefix,
            'channel_li_channel_name': channel_li_channel_name,
            'channel_li_channel_img_src': channel_li_channel_img_src,
            'channel_li_channel_number': channel_row_index + 1,
            'channel_sources_data_json': json.dumps(channel_sources)
        }

        return channel_li_template.render(channel_li_template_fields)

    def _render_channel_programs_li_template(self, channel_programs_li_id_prefix, channel_programs_lis):
        channel_programs_li_template = self._environment.get_template('channel_programs_li.html')

        channel_programs_li_template_fields = {
            'channel_programs_li_id_prefix': channel_programs_li_id_prefix,
            'channel_programs_lis': '\n'.join(channel_programs_lis)
        }

        return channel_programs_li_template.render(channel_programs_li_template_fields)

    def _render_configuration_div_template(self, active_providers_map_class):
        configuration_div_template = self._environment.get_template('configuration_div.html')

        configuration_div_template_fields = {
            'configuration_server_password': self._configuration['SERVER_PASSWORD'],
            'configuration_server_http_port': self._configuration['SERVER_HTTP_PORT'],
            'configuration_server_https_port': self._configuration['SERVER_HTTPS_PORT'],
            'configuration_server_hostname_loopback': self._configuration['SERVER_HOSTNAME_LOOPBACK'],
            'configuration_server_hostname_private': self._configuration['SERVER_HOSTNAME_PRIVATE'],
            'configuration_server_hostname_public': self._configuration['SERVER_HOSTNAME_PUBLIC'],
            'configuration_beast_active':
                'checked="checked"' if 'beast' in active_providers_map_class
                else '',
            'configuration_beast_username': '',
            'configuration_beast_password': '',
            'configuration_beast_playlist_protocol_hls_selected': '',
            'configuration_beast_playlist_protocol_mpegts_selected': '',
            'configuration_beast_playlist_type_dynamic_selected': '',
            'configuration_beast_playlist_type_static_selected': '',
            'configuration_beast_epg_source_beast_selected': '',
            'configuration_beast_epg_source_other_selected': '',
            'configuration_beast_epg_url': '',
            'configuration_coolasice_active':
                'checked="checked"' if 'coolasice' in active_providers_map_class
                else '',
            'configuration_coolasice_username': '',
            'configuration_coolasice_password': '',
            'configuration_coolasice_playlist_protocol_hls_selected': '',
            'configuration_coolasice_playlist_protocol_mpegts_selected': '',
            'configuration_coolasice_playlist_type_dynamic_selected': '',
            'configuration_coolasice_playlist_type_static_selected': '',
            'configuration_coolasice_epg_source_coolasice_selected': '',
            'configuration_coolasice_epg_source_other_selected': '',
            'configuration_coolasice_epg_url': '',
            'configuration_crystalclear_active':
                'checked="checked"' if 'crystalclear' in active_providers_map_class
                else '',
            'configuration_crystalclear_username': '',
            'configuration_crystalclear_password': '',
            'configuration_crystalclear_playlist_protocol_hls_selected': '',
            'configuration_crystalclear_playlist_protocol_mpegts_selected': '',
            'configuration_crystalclear_playlist_type_dynamic_selected': '',
            'configuration_crystalclear_playlist_type_static_selected': '',
            'configuration_crystalclear_epg_source_crystalclear_selected': '',
            'configuration_crystalclear_epg_source_other_selected': '',
            'configuration_crystalclear_epg_url': '',
            'configuration_inferno_active':
                'checked="checked"' if 'inferno' in active_providers_map_class
                else '',
            'configuration_inferno_username': '',
            'configuration_inferno_password': '',
            'configuration_inferno_playlist_protocol_hls_selected': '',
            'configuration_inferno_playlist_protocol_mpegts_selected': '',
            'configuration_inferno_playlist_type_dynamic_selected': '',
            'configuration_inferno_playlist_type_static_selected': '',
            'configuration_inferno_epg_source_inferno_selected': '',
            'configuration_inferno_epg_source_other_selected': '',
            'configuration_inferno_epg_url': '',
            'configuration_smoothstreams_active':
                'checked="checked"' if 'smoothstreams' in active_providers_map_class
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
            'configuration_vaderstreams_active':
                'checked="checked"' if 'vaderstreams' in active_providers_map_class
                else '',
            'configuration_vaderstreams_username': '',
            'configuration_vaderstreams_password': '',
            'configuration_vaderstreams_playlist_protocol_hls_selected': '',
            'configuration_vaderstreams_playlist_protocol_mpegts_selected': '',
            'configuration_vaderstreams_playlist_type_dynamic_selected': '',
            'configuration_vaderstreams_playlist_type_static_selected': '',
            'configuration_vaderstreams_epg_source_vaderstreams_selected': '',
            'configuration_vaderstreams_epg_source_other_selected': '',
            'configuration_vaderstreams_epg_url': ''
        }

        if 'BEAST_USERNAME' in self._configuration:
            configuration_div_template_fields['configuration_beast_username'] = self._configuration['BEAST_USERNAME']
        if 'BEAST_PASSWORD' in self._configuration:
            configuration_div_template_fields['configuration_beast_password'] = self._configuration['BEAST_PASSWORD']
        if 'BEAST_PLAYLIST_PROTOCOL' in self._configuration:
            configuration_div_template_fields['configuration_beast_playlist_protocol_{0}_selected'.format(
                self._configuration['BEAST_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
        if 'BEAST_PLAYLIST_TYPE' in self._configuration:
            configuration_div_template_fields['configuration_beast_playlist_type_{0}_selected'.format(
                self._configuration['BEAST_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
        if 'BEAST_EPG_SOURCE' in self._configuration:
            configuration_div_template_fields['configuration_beast_epg_source_{0}_selected'.format(
                self._configuration['BEAST_EPG_SOURCE'].lower())] = 'selected="selected" '
        if 'BEAST_EPG_URL' in self._configuration:
            if self._configuration['BEAST_EPG_URL'] is None:
                configuration_div_template_fields['configuration_beast_epg_url'] = ''
            else:
                configuration_div_template_fields['configuration_beast_epg_url'] = self._configuration['BEAST_EPG_URL']

        if 'COOLASICE_USERNAME' in self._configuration:
            configuration_div_template_fields['configuration_coolasice_username'] = self._configuration[
                'COOLASICE_USERNAME']
        if 'COOLASICE_PASSWORD' in self._configuration:
            configuration_div_template_fields['configuration_coolasice_password'] = self._configuration[
                'COOLASICE_PASSWORD']
        if 'COOLASICE_PLAYLIST_PROTOCOL' in self._configuration:
            configuration_div_template_fields['configuration_coolasice_playlist_protocol_{0}_selected'.format(
                self._configuration['COOLASICE_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
        if 'COOLASICE_PLAYLIST_TYPE' in self._configuration:
            configuration_div_template_fields['configuration_coolasice_playlist_type_{0}_selected'.format(
                self._configuration['COOLASICE_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
        if 'COOLASICE_EPG_SOURCE' in self._configuration:
            configuration_div_template_fields['configuration_coolasice_epg_source_{0}_selected'.format(
                self._configuration['COOLASICE_EPG_SOURCE'].lower())] = 'selected="selected" '
        if 'COOLASICE_EPG_URL' in self._configuration:
            if self._configuration['COOLASICE_EPG_URL'] is None:
                configuration_div_template_fields['configuration_coolasice_epg_url'] = ''
            else:
                configuration_div_template_fields['configuration_coolasice_epg_url'] = self._configuration[
                    'COOLASICE_EPG_URL']

        if 'CRYSTALCLEAR_USERNAME' in self._configuration:
            configuration_div_template_fields['configuration_crystalclear_username'] = self._configuration[
                'CRYSTALCLEAR_USERNAME']
        if 'CRYSTALCLEAR_PASSWORD' in self._configuration:
            configuration_div_template_fields['configuration_crystalclear_password'] = self._configuration[
                'CRYSTALCLEAR_PASSWORD']
        if 'CRYSTALCLEAR_PLAYLIST_PROTOCOL' in self._configuration:
            configuration_div_template_fields['configuration_crystalclear_playlist_protocol_{0}_selected'.format(
                self._configuration['CRYSTALCLEAR_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
        if 'CRYSTALCLEAR_PLAYLIST_TYPE' in self._configuration:
            configuration_div_template_fields['configuration_crystalclear_playlist_type_{0}_selected'.format(
                self._configuration['CRYSTALCLEAR_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
        if 'CRYSTALCLEAR_EPG_SOURCE' in self._configuration:
            configuration_div_template_fields['configuration_crystalclear_epg_source_{0}_selected'.format(
                self._configuration['CRYSTALCLEAR_EPG_SOURCE'].lower())] = 'selected="selected" '
        if 'CRYSTALCLEAR_EPG_URL' in self._configuration:
            if self._configuration['CRYSTALCLEAR_EPG_URL'] is None:
                configuration_div_template_fields['configuration_crystalclear_epg_url'] = ''
            else:
                configuration_div_template_fields['configuration_crystalclear_epg_url'] = self._configuration[
                    'CRYSTALCLEAR_EPG_URL']

        if 'INFERNO_USERNAME' in self._configuration:
            configuration_div_template_fields['configuration_inferno_username'] = self._configuration[
                'INFERNO_USERNAME']
        if 'INFERNO_PASSWORD' in self._configuration:
            configuration_div_template_fields['configuration_inferno_password'] = self._configuration[
                'INFERNO_PASSWORD']
        if 'INFERNO_PLAYLIST_PROTOCOL' in self._configuration:
            configuration_div_template_fields['configuration_inferno_playlist_protocol_{0}_selected'.format(
                self._configuration['INFERNO_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
        if 'INFERNO_PLAYLIST_TYPE' in self._configuration:
            configuration_div_template_fields['configuration_inferno_playlist_type_{0}_selected'.format(
                self._configuration['INFERNO_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
        if 'INFERNO_EPG_SOURCE' in self._configuration:
            configuration_div_template_fields['configuration_inferno_epg_source_{0}_selected'.format(
                self._configuration['INFERNO_EPG_SOURCE'].lower())] = 'selected="selected" '
        if 'INFERNO_EPG_URL' in self._configuration:
            if self._configuration['INFERNO_EPG_URL'] is None:
                configuration_div_template_fields['configuration_inferno_epg_url'] = ''
            else:
                configuration_div_template_fields['configuration_inferno_epg_url'] = self._configuration[
                    'INFERNO_EPG_URL']

        if 'SMOOTHSTREAMS_SERVICE' in self._configuration:
            configuration_div_template_fields['configuration_{0}_selected'.format(
                self._configuration['SMOOTHSTREAMS_SERVICE'].lower())] = 'selected="selected" '
        if 'SMOOTHSTREAMS_SERVER' in self._configuration:
            configuration_div_template_fields['configuration_{0}_selected'.format(
                self._configuration['SMOOTHSTREAMS_SERVER'].lower().replace('-', '_'))] = 'selected="selected" '
        if 'SMOOTHSTREAMS_USERNAME' in self._configuration:
            configuration_div_template_fields['configuration_smoothstreams_username'] = self._configuration[
                'SMOOTHSTREAMS_USERNAME']
        if 'SMOOTHSTREAMS_PASSWORD' in self._configuration:
            configuration_div_template_fields['configuration_smoothstreams_password'] = self._configuration[
                'SMOOTHSTREAMS_PASSWORD']
        if 'SMOOTHSTREAMS_PLAYLIST_PROTOCOL' in self._configuration:
            configuration_div_template_fields['configuration_smoothstreams_playlist_protocol_{0}_selected'.format(
                self._configuration['SMOOTHSTREAMS_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
        if 'SMOOTHSTREAMS_PLAYLIST_TYPE' in self._configuration:
            configuration_div_template_fields['configuration_smoothstreams_playlist_type_{0}_selected'.format(
                self._configuration['SMOOTHSTREAMS_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
        if 'SMOOTHSTREAMS_EPG_SOURCE' in self._configuration:
            configuration_div_template_fields['configuration_smoothstreams_epg_source_{0}_selected'.format(
                self._configuration['SMOOTHSTREAMS_EPG_SOURCE'].lower())] = 'selected="selected" '
        if 'SMOOTHSTREAMS_EPG_URL' in self._configuration:
            if self._configuration['SMOOTHSTREAMS_EPG_URL'] is None:
                configuration_div_template_fields['configuration_smoothstreams_epg_url'] = ''
            else:
                configuration_div_template_fields['configuration_smoothstreams_epg_url'] = self._configuration[
                    'SMOOTHSTREAMS_EPG_URL']

        if 'VADERSTREAMS_SERVER' in self._configuration:
            configuration_div_template_fields['configuration_{0}_selected'.format(
                self._configuration['VADERSTREAMS_SERVER'].lower().replace('-', '_'))] = 'selected="selected" '
        if 'VADERSTREAMS_USERNAME' in self._configuration:
            configuration_div_template_fields['configuration_vaderstreams_username'] = self._configuration[
                'VADERSTREAMS_USERNAME']
        if 'VADERSTREAMS_PASSWORD' in self._configuration:
            configuration_div_template_fields['configuration_vaderstreams_password'] = self._configuration[
                'VADERSTREAMS_PASSWORD']
        if 'VADERSTREAMS_PLAYLIST_PROTOCOL' in self._configuration:
            configuration_div_template_fields['configuration_vaderstreams_playlist_protocol_{0}_selected'.format(
                self._configuration['VADERSTREAMS_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
        if 'VADERSTREAMS_PLAYLIST_TYPE' in self._configuration:
            configuration_div_template_fields['configuration_vaderstreams_playlist_type_{0}_selected'.format(
                self._configuration['VADERSTREAMS_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
        if 'VADERSTREAMS_EPG_SOURCE' in self._configuration:
            configuration_div_template_fields['configuration_vaderstreams_epg_source_{0}_selected'.format(
                self._configuration['VADERSTREAMS_EPG_SOURCE'].lower())] = 'selected="selected" '
        if 'VADERSTREAMS_EPG_URL' in self._configuration:
            if self._configuration['VADERSTREAMS_EPG_URL'] is None:
                configuration_div_template_fields['configuration_vaderstreams_epg_url'] = ''
            else:
                configuration_div_template_fields['configuration_vaderstreams_epg_url'] = self._configuration[
                    'VADERSTREAMS_EPG_URL']

        return configuration_div_template.render(configuration_div_template_fields)

    def _render_date_li_template(self, date_li_id_prefix, date_li_id_suffix, date_li_h2_text):
        date_li_template = self._environment.get_template('date_li.html')

        date_li_template_fields = {
            'date_li_id_prefix': date_li_id_prefix,
            'date_li_id_suffix': date_li_id_suffix,
            'date_li_h2_text': date_li_h2_text
        }

        return date_li_template.render(date_li_template_fields)

    def _render_date_programs_li_template(self,
                                          date_programs_lis,
                                          date_programs_li_id_prefix,
                                          date_programs_li_id_suffix):
        date_programs_li_template = self._environment.get_template('date_programs_li.html')

        date_programs_lis.append(self._render_separator_li_template(date_programs_li_id_prefix,
                                                                    date_programs_li_id_suffix))
        date_programs_lis.append(self._render_alert_li_template(date_programs_li_id_prefix,
                                                                date_programs_li_id_suffix))
        date_programs_lis.append(self._render_buttons_li_template(date_programs_li_id_prefix,
                                                                  date_programs_li_id_suffix))

        date_programs_li_template_fields = {
            'date_programs_li_id_prefix': date_programs_li_id_prefix,
            'date_programs_li_id_suffix': date_programs_li_id_suffix,
            'date_programs_lis': '\n'.join(date_programs_lis)
        }

        return date_programs_li_template.render(date_programs_li_template_fields)

    def _render_date_separator_li_template(self, date_separator_li_id_prefix, date_separator_li_id_suffix):
        date_separator_li_template = self._environment.get_template('date_separator_li.html')

        date_separator_li_template_fields = {
            'date_separator_li_id_prefix': date_separator_li_id_prefix,
            'date_separator_li_id_suffix': date_separator_li_id_suffix
        }

        return date_separator_li_template.render(date_separator_li_template_fields)

    def _render_guide_group_select_option_template(self, guide_provider, guide_group, active_providers_map_class):
        guide_group_select_option_template = self._environment.get_template('guide_group_select_option.html')

        guide_group_select_options = []

        if guide_provider.lower() in active_providers_map_class:
            selected_provider_map_class = active_providers_map_class[guide_provider.lower()]
            provider_groups = selected_provider_map_class.epg_class().get_m3u8_groups()

            if guide_group in provider_groups:
                selected_channel_group = guide_group
            else:
                selected_channel_group = sorted(provider_groups)[0]
        else:
            selected_provider_map_class = active_providers_map_class[sorted(active_providers_map_class)[0]]
            provider_groups = selected_provider_map_class.epg_class().get_m3u8_groups()

            selected_channel_group = sorted(provider_groups)[0]

        for provider_name in sorted(active_providers_map_class):
            provider = active_providers_map_class[provider_name]

            for group in sorted(provider.epg_class().get_m3u8_groups()):
                guide_group_select_option_template_fields = {
                    'guide_group_select_option_selected':
                        'selected="selected" ' if (selected_provider_map_class == provider and
                                                   selected_channel_group == group)
                        else '',
                    'guide_group_select_option_provider': provider.api_class().__name__,
                    'guide_group_select_option_group': group
                }

                guide_group_select_options.append(
                    guide_group_select_option_template.render(guide_group_select_option_template_fields))

        return '\n'.join(guide_group_select_options)

    def _render_guide_lis_template(self,
                                   is_server_secure,
                                   authorization_required,
                                   client_ip_address_type,
                                   client_uuid,
                                   guide_number_of_days,
                                   guide_provider,
                                   guide_group,
                                   active_providers_map_class):
        current_date_time_in_utc = datetime.now(pytz.utc)
        cutoff_date_time_in_utc = (current_date_time_in_utc.astimezone(tzlocal.get_localzone()) +
                                   timedelta(days=int(guide_number_of_days) + 1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0).astimezone(pytz.utc)

        if guide_provider.lower() in active_providers_map_class:
            provider_map_class = active_providers_map_class[guide_provider.lower()]
            provider_groups = provider_map_class.epg_class().get_m3u8_groups()

            if guide_group in provider_groups:
                channel_m3u8_group = guide_group
            else:
                channel_m3u8_group = sorted(provider_groups)[0]
        else:
            provider_map_class = active_providers_map_class[sorted(active_providers_map_class)[0]]
            provider_groups = provider_map_class.epg_class().get_m3u8_groups()

            channel_m3u8_group = sorted(provider_groups)[0]

        guide_lis = []

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                channel_rows = provider_map_class.database_access_class().query_channels_pickle_in_m3u8_group(
                    db_session,
                    channel_m3u8_group)

                for (channel_row_index, channel_row) in enumerate(channel_rows):
                    channel = pickle.loads(channel_row.pickle)

                    guide_lis.append(self._render_channel_li_template(is_server_secure,
                                                                      authorization_required,
                                                                      client_ip_address_type,
                                                                      client_uuid,
                                                                      channel,
                                                                      channel_row_index,
                                                                      channel_rows,
                                                                      provider_map_class))

                    day_of_containing_date_li = None
                    channel_programs_lis = []
                    date_li_id_suffix = 0
                    date_programs_lis = []
                    program_li_input_label_span_id_suffix = 0

                    program_rows = \
                        provider_map_class.database_access_class().query_programs_pickle_by_channel_xmltv_id_start_stop(
                            db_session,
                            channel.xmltv_id,
                            cutoff_date_time_in_utc,
                            current_date_time_in_utc)

                    for (program_row_index, program_row) in enumerate(program_rows):
                        program = pickle.loads(program_row.pickle)

                        program_start_date_time_in_local = program.start.astimezone(tzlocal.get_localzone())

                        program_li_input_label_span_id_suffix += 1

                        day_of_program_start_date_time_in_local = program_start_date_time_in_local.day

                        if day_of_program_start_date_time_in_local != day_of_containing_date_li:
                            if day_of_containing_date_li:
                                if date_programs_lis:
                                    channel_programs_lis.append(self._render_date_programs_li_template(
                                        date_programs_lis,
                                        channel.xmltv_id,
                                        date_li_id_suffix))

                                    channel_programs_lis.append(self._render_date_separator_li_template(
                                        channel.xmltv_id,
                                        date_li_id_suffix))

                                    date_programs_lis = []
                                    date_li_id_suffix += 1
                                else:
                                    channel_programs_lis.pop()

                            channel_programs_lis.append(self._render_date_li_template(
                                channel.xmltv_id,
                                date_li_id_suffix,
                                program_start_date_time_in_local.strftime('%B %d, %Y')))

                            day_of_containing_date_li = program_start_date_time_in_local.day

                        date_programs_lis.append(self._render_program_li_template(channel,
                                                                                  program,
                                                                                  channel.xmltv_id,
                                                                                  program_li_input_label_span_id_suffix,
                                                                                  date_li_id_suffix,
                                                                                  provider_map_class))

                        if program_row_index == len(program_rows) - 1:
                            if day_of_containing_date_li:
                                if date_programs_lis:
                                    channel_programs_lis.append(self._render_date_programs_li_template(
                                        date_programs_lis,
                                        channel.xmltv_id,
                                        date_li_id_suffix))

                                    channel_programs_lis.append(self._render_date_separator_li_template(
                                        channel.xmltv_id,
                                        date_li_id_suffix))

                                    date_programs_lis = []
                                    date_li_id_suffix += 1
                                else:
                                    channel_programs_lis.pop()

                    if channel_programs_lis:
                        guide_lis.append(self._render_channel_programs_li_template(
                            channel.xmltv_id,
                            channel_programs_lis))

                    yield '\n'.join(guide_lis)

                    guide_lis = []
            finally:
                db_session.close()

    def _render_head_template(self, authorization_required, guide_number_of_days, streaming_protocol):
        head_template = self._environment.get_template('head.html')

        head_template_fields = {
            'iptv_proxy_script': self._render_iptv_proxy_script_template(authorization_required,
                                                                         guide_number_of_days,
                                                                         streaming_protocol),
            'iptv_proxy_version': VERSION
        }

        return head_template.render(head_template_fields)

    def _render_iptv_proxy_script_template(self, authorization_required, guide_number_of_days, streaming_protocol):
        iptv_proxy_script_template = self._environment.get_template('iptv_proxy_script.js')

        iptv_proxy_script_template_fields = {
            'authorization_basic_password': '{0}'.format(
                base64.b64encode(':{0}'.format(
                    self._configuration['SERVER_PASSWORD']).encode()).decode()) if authorization_required
            else '',
            'last_selected_guide_number_of_days': guide_number_of_days,
            'last_selected_streaming_protocol': streaming_protocol
        }

        return iptv_proxy_script_template.render(iptv_proxy_script_template_fields)

    def _render_navigation_bar_div_template(self, guide_provider, guide_group, active_providers_map_class):
        navigation_bar_div_template = self._environment.get_template('navigation_bar_div.html')

        navigation_bar_div_template_fields = {
            'guide_group_select_options': self._render_guide_group_select_option_template(guide_provider,
                                                                                          guide_group,
                                                                                          active_providers_map_class)
        }

        return navigation_bar_div_template.render(navigation_bar_div_template_fields)

    def _render_program_li_template(self,
                                    channel,
                                    program,
                                    program_li_id_prefix,
                                    program_li_input_label_span_id_suffix,
                                    program_li_input_name_suffix,
                                    provider):
        program_li_template = self._environment.get_template('program_li.html')

        program_start_date_time_in_local = program.start.astimezone(tzlocal.get_localzone())
        program_end_date_time_in_local = program.stop.astimezone(tzlocal.get_localzone())

        program_post_recording_body = {
            'data': {
                'type': 'recordings',
                'attributes': {
                    'channel_number': '{0:02}'.format(channel.number),
                    'end_date_time_in_utc': '{0}'.format(program.stop.strftime('%Y-%m-%d %H:%M:%S')),
                    'program_title': '{0}{1}{2}'.format(
                        html.escape(program.titles[0].text),
                        ': ' if program.sub_titles and program.sub_titles[0].text
                        else '',
                        html.escape(program.sub_titles[0].text) if (program.sub_titles and
                                                                    program.sub_titles[0].text is not None)
                        else ''),
                    'provider': '{0}'.format(provider.api_class().__name__),
                    'start_date_time_in_utc': '{0}'.format(program.start.strftime('%Y-%m-%d %H:%M:%S'))
                }
            }
        }

        program_li_template_fields = {
            'program_li_id_prefix': program_li_id_prefix,
            'program_li_input_label_span_id_suffix': program_li_input_label_span_id_suffix,
            'program_li_input_name_suffix': program_li_input_name_suffix,
            'program_li_input_value': json.dumps(program_post_recording_body),
            'program_li_label_start_time': program_start_date_time_in_local.strftime('%H:%M:%S'),
            'program_li_label_end_time': program_end_date_time_in_local.strftime('%H:%M:%S'),
            'program_li_label_program_title': html.escape(program.titles[0].text),
            'program_sub_title_span': self._render_program_sub_title_span_template(
                program,
                program_li_id_prefix,
                program_li_input_label_span_id_suffix),
            'program_li_span_description': html.escape(program.descriptions[0].text)
            if program.descriptions and program.descriptions[0].text is not None
            else ''
        }

        return program_li_template.render(program_li_template_fields)

    def _render_program_sub_title_span_template(self,
                                                program,
                                                program_li_id_prefix,
                                                program_li_input_label_span_id_suffix):
        if program.sub_titles and program.sub_titles[0].text is not None:
            program_sub_title_span_template = self._environment.get_template('program_sub_title_span.html')

            program_sub_title_span_template_fields = {
                'program_li_id_prefix': program_li_id_prefix,
                'program_li_input_label_span_id_suffix': program_li_input_label_span_id_suffix,
                'program_li_span_sub_title': html.escape(program.sub_titles[0].text)
            }

            return program_sub_title_span_template.render(program_sub_title_span_template_fields)
        else:
            return ''

    def _render_recordings_div_template(self,
                                        is_server_secure,
                                        authorization_required,
                                        client_uuid,
                                        server_hostname,
                                        server_port):
        recordings_div_template = self._environment.get_template('recordings_div.html')

        recording_table_rows = self._render_recordings_tables_rows_template(is_server_secure,
                                                                            authorization_required,
                                                                            client_uuid,
                                                                            server_hostname,
                                                                            server_port)

        recordings_div_template_fields = {
            'live_no_recordings_li_style': 'display:none' if recording_table_rows['live']
            else '',
            'live_recordings_li_style': '' if recording_table_rows['live']
            else 'display:none',
            'live_recordings_table_rows': '\n'.join(recording_table_rows['live']),
            'persisted_no_recordings_li_style': 'display:none' if recording_table_rows['persisted']
            else '',
            'persisted_recordings_li_style': '' if recording_table_rows['persisted']
            else 'display:none',
            'persisted_recordings_table_rows': '\n'.join(recording_table_rows['persisted']),
            'scheduled_no_recordings_li_style': 'display:none' if recording_table_rows['scheduled']
            else '',
            'scheduled_recordings_li_style': '' if recording_table_rows['scheduled']
            else 'display:none',
            'scheduled_recordings_table_rows': '\n'.join(recording_table_rows['scheduled'])
        }

        return recordings_div_template.render(recordings_div_template_fields)

    def _render_recordings_tables_rows_template(self,
                                                is_server_secure,
                                                authorization_required,
                                                client_uuid,
                                                server_hostname,
                                                server_port):
        recordings_table_row_template = self._environment.get_template('recordings_table_row.html')

        recordings = PVR.get_recordings()

        recording_table_rows = {
            'live': [],
            'persisted': [],
            'scheduled': []
        }

        for recording in recordings:
            spacing_and_control_spans_display = 'display: none;'
            recording_source = None

            if recording.status == RecordingStatus.PERSISTED.value:
                spacing_and_control_spans_display = 'display: inline-block;'

                recording_source = {
                    'type': 'vod',
                    'hls': {
                        'videoSource': '{0}'.format(PVR.generate_vod_recording_playlist_url(
                            is_server_secure,
                            server_hostname,
                            server_port,
                            client_uuid,
                            recording.id,
                            self._configuration['SERVER_PASSWORD'] if authorization_required
                            else None))
                    }
                }

            recordings_table_row_template_fields = {
                'recording_id': recording.id,
                'spacing_span_display': spacing_and_control_spans_display,
                'recording_source_data_json': json.dumps(recording_source),
                'control_span_display': spacing_and_control_spans_display,
                'recording_channel_number': recording.channel_number,
                'recording_channel_name': html.escape(recording.channel_name),
                'recording_program_title': html.escape(recording.program_title),
                'recording_start_date_time_in_utc': recording.start_date_time_in_utc.astimezone(
                    tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S'),
                'recording_end_date_time_in_utc': recording.end_date_time_in_utc.astimezone(
                    tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S')
            }

            recording_table_rows[recording.status].append(
                recordings_table_row_template.render(recordings_table_row_template_fields))

        return recording_table_rows

    def _render_separator_li_template(self, separator_li_id_prefix, separator_li_id_suffix):
        separator_li_template = self._environment.get_template('separator_li.html')

        separator_li_template_fields = {
            'separator_li_id_prefix': separator_li_id_prefix,
            'separator_li_id_suffix': separator_li_id_suffix
        }

        return separator_li_template.render(separator_li_template_fields)

    def _render_settings_div_template(self, guide_number_of_days, streaming_protocol):
        settings_div_template = self._environment.get_template('settings_div.html')

        settings_div_template_fields = {
            '_1_image_class': 'w3-opacity-max w3-image w3-round-large',
            '_1_image_onclick': 'onclick="SettingsModule.updateNumberOfDaysImages(\'1\')"',
            '_1_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            '_2_image_class': 'w3-opacity-max w3-image w3-round-large',
            '_2_image_onclick': 'onclick="SettingsModule.updateNumberOfDaysImages(\'2\')"',
            '_2_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            '_3_image_class': 'w3-opacity-max w3-image w3-round-large',
            '_3_image_onclick': 'onclick="SettingsModule.updateNumberOfDaysImages(\'3\')"',
            '_3_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            '_4_image_class': 'w3-opacity-max w3-image w3-round-large',
            '_4_image_onclick': 'onclick="SettingsModule.updateNumberOfDaysImages(\'4\')"',
            '_4_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            '_5_image_class': 'w3-opacity-max w3-image w3-round-large',
            '_5_image_onclick': 'onclick="SettingsModule.updateNumberOfDaysImages(\'5\')"',
            '_5_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            '_{0}_image_class'.format(guide_number_of_days): 'w3-border-blue w3-bottombar w3-leftbar w3-rightbar '
                                                             'w3-topbar w3-image w3-round-large',
            '_{0}_image_onclick'.format(guide_number_of_days): '',
            '_{0}_image_style'.format(guide_number_of_days): 'max-width: 92px; padding: 8px;',
            'hls_image_class': 'w3-grayscale-max w3-image w3-round-large',
            'hls_image_onclick': 'onclick="SettingsModule.updateProtocolImages(\'hls\')"',
            'hls_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            'rtmp_image_class': 'w3-grayscale-max w3-image w3-round-large',
            'rtmp_image_onclick': 'onclick="SettingsModule.updateProtocolImages(\'rtmp\')"',
            'rtmp_image_style': 'cursor: pointer; max-width: 92px; padding: 14px;',
            '{0}_image_class'.format(
                streaming_protocol): 'w3-border-blue w3-bottombar w3-leftbar w3-rightbar w3-topbar '
                                     'w3-image w3-round-large',
            '{0}_image_onclick'.format(streaming_protocol): '',
            '{0}_image_style'.format(streaming_protocol): 'max-width: 92px; padding: 8px;'
        }

        return settings_div_template.render(settings_div_template_fields)

    def render_guide_div_template(self,
                                  is_server_secure,
                                  authorization_required,
                                  client_ip_address,
                                  client_uuid,
                                  guide_number_of_days,
                                  guide_provider,
                                  guide_group,
                                  active_providers_map_class):
        client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)

        yield self._environment.get_template('guide_div_header.html').render()

        for rendered_guide_li_template in self._render_guide_lis_template(is_server_secure,
                                                                          authorization_required,
                                                                          client_ip_address_type,
                                                                          client_uuid,
                                                                          guide_number_of_days,
                                                                          guide_provider,
                                                                          guide_group,
                                                                          active_providers_map_class):
            yield rendered_guide_li_template

        yield self._environment.get_template('guide_div_footer.html').render()

    def render_index_template(self,
                              is_server_secure,
                              authorization_required,
                              client_ip_address,
                              client_uuid,
                              guide_number_of_days,
                              guide_provider,
                              guide_group,
                              streaming_protocol,
                              active_providers_map_class):
        client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)
        server_hostname = self._configuration['SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value)]
        server_http_port = self._configuration['SERVER_HTTP_PORT']
        server_https_port = self._configuration['SERVER_HTTPS_PORT']

        yield self._environment.get_template('index_header.html').render()

        yield self._render_head_template(authorization_required,
                                         guide_number_of_days,
                                         streaming_protocol)

        yield self._environment.get_template('body_header.html').render()

        yield self._render_navigation_bar_div_template(guide_provider, guide_group, active_providers_map_class)

        yield self._render_settings_div_template(guide_number_of_days, streaming_protocol)

        yield self._environment.get_template('loading_div.html').render()

        yield self._environment.get_template('content_div_header.html').render()

        yield self._environment.get_template('guide_div_header.html').render()

        for rendered_guide_li_template in self._render_guide_lis_template(is_server_secure,
                                                                          authorization_required,
                                                                          client_ip_address_type,
                                                                          client_uuid,
                                                                          guide_number_of_days,
                                                                          guide_provider,
                                                                          guide_group,
                                                                          active_providers_map_class):
            yield rendered_guide_li_template

        yield self._environment.get_template('guide_div_footer.html').render()

        yield self._environment.get_template('video_div.html').render()

        yield self._render_recordings_div_template(
            is_server_secure,
            authorization_required,
            client_uuid,
            server_hostname,
            server_https_port if is_server_secure
            else server_http_port)

        yield self._render_configuration_div_template(active_providers_map_class)

        yield self._environment.get_template('monitor_div.html').render()

        yield self._render_about_div_template()

        yield self._environment.get_template('content_div_footer.html').render()

        yield self._environment.get_template('body_footer.html').render()

        yield self._environment.get_template('index_footer.html').render()
