import base64
import html
import json
import logging
from datetime import datetime
from datetime import timedelta
from threading import RLock

import pytz
import tzlocal

from .configuration import IPTVProxyConfiguration
from .constants import ERROR_HTML_TEMPLATES
from .constants import INDEX_HTML_TEMPLATES
from .constants import LOGIN_HTML_TEMPLATES
from .constants import VERSION
from .db import IPTVProxyDatabase
from .enums import IPTVProxyRecordingStatus
from .recorder import IPTVProxyPVR
from .utilities import IPTVProxyUtility

logger = logging.getLogger(__name__)


class IPTVProxyHTMLTemplateEngine(object):
    __slots__ = []

    _configuration = None
    _lock = RLock()

    @classmethod
    def _render_alert_li_template(cls, alert_li_id_prefix, alert_li_id_suffix):
        alert_li_html_template_fields = {
            'alert_li_id_prefix': alert_li_id_prefix,
            'alert_li_id_suffix': alert_li_id_suffix
        }

        return INDEX_HTML_TEMPLATES['alert_li.html.st'].safe_substitute(alert_li_html_template_fields)

    @classmethod
    def _render_buttons_li_template(cls, buttons_li_id_prefix, buttons_li_id_suffix):
        buttons_li_html_template_fields = {
            'buttons_li_id_prefix': buttons_li_id_prefix,
            'buttons_li_id_suffix': buttons_li_id_suffix
        }
        return INDEX_HTML_TEMPLATES['buttons_li.html.st'].safe_substitute(buttons_li_html_template_fields)

    @classmethod
    def _render_channel_li_template(cls,
                                    is_server_secure,
                                    authorization_required,
                                    client_ip_address_type,
                                    client_uuid,
                                    channel_record,
                                    channel_index,
                                    channels,
                                    guide_provider):
        if channel_index == len(channels) - 1:
            channel_li_border = ' w3-border-0'
        else:
            channel_li_border = ''

        channel_li_id_prefix = channel_record['id']

        channel_li_channel_name = html.escape(channel_record['name'])

        if channel_record['icon_data_uri']:
            channel_li_channel_img_src = channel_record['icon_data_uri']
        else:
            channel_li_channel_img_src = channel_record['icon_url'].format(
                's'
                if is_server_secure
                else '',
                cls._configuration['SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value)],
                cls._configuration['SERVER_HTTP{0}_PORT'.format('S'
                                                                if is_server_secure
                                                                else '')],
                '?http_token={0}'.format(cls._configuration['SERVER_PASSWORD'])
                if authorization_required
                else '')

        channel_li_channel_number = channel_record['number']

        provider = IPTVProxyConfiguration.get_provider(guide_provider.lower())

        channel_sources = {'type': 'live'}
        for provider_supported_protocol in provider['api'].get_supported_protocols():
            channel_sources[provider_supported_protocol] = {}

            channel_sources[provider_supported_protocol]['videoSource'] = provider[
                'api'].generate_playlist_m3u8_track_url(dict(channel_number=int(channel_li_channel_number),
                                                             client_uuid=client_uuid,
                                                             http_token=cls._configuration['SERVER_PASSWORD']
                                                             if authorization_required
                                                             else None,
                                                             is_server_secure=is_server_secure,
                                                             playlist_protocol=provider_supported_protocol,
                                                             server_hostname=cls._configuration[
                                                                 'SERVER_HOSTNAME_{0}'.format(
                                                                     client_ip_address_type.value)],
                                                             server_port=cls._configuration[
                                                                 'SERVER_HTTP{0}_PORT'.format('S'
                                                                                              if is_server_secure
                                                                                              else '')]))

        return {
            'channel_li_border': channel_li_border,
            'channel_li_id_prefix': channel_li_id_prefix,
            'channel_li_channel_name': channel_li_channel_name,
            'channel_li_channel_img_src': channel_li_channel_img_src,
            'channel_li_channel_number': channel_index + 1,
            'channel_sources_data_json': json.dumps(channel_sources)
        }

    @classmethod
    def _render_channel_programs_li_template(cls, channel_programs_li_id_prefix, channel_programs_lis):
        channel_programs_li_html_template_fields = {
            'channel_programs_li_id_prefix': channel_programs_li_id_prefix,
            'channel_programs_lis': '\n'.join(channel_programs_lis)
        }

        return INDEX_HTML_TEMPLATES['channel_programs_li.html.st'].safe_substitute(
            channel_programs_li_html_template_fields)

    @classmethod
    def _render_date_li_template(cls, date_li_id_prefix, date_li_id_suffix, date_li_h2_text):
        date_li_html_template_fields = {
            'date_li_id_prefix': date_li_id_prefix,
            'date_li_id_suffix': date_li_id_suffix,
            'date_li_h2_text': date_li_h2_text
        }

        return INDEX_HTML_TEMPLATES['date_li.html.st'].safe_substitute(date_li_html_template_fields)

    @classmethod
    def _render_date_programs_li_template(cls,
                                          date_programs_lis,
                                          date_programs_li_id_prefix,
                                          date_programs_li_id_suffix):
        date_programs_lis.append(cls._render_separator_li_template(date_programs_li_id_prefix,
                                                                   date_programs_li_id_suffix))
        date_programs_lis.append(cls._render_alert_li_template(date_programs_li_id_prefix,
                                                               date_programs_li_id_suffix))
        date_programs_lis.append(cls._render_buttons_li_template(date_programs_li_id_prefix,
                                                                 date_programs_li_id_suffix))

        date_programs_li_html_template_fields = {
            'date_programs_li_id_prefix': date_programs_li_id_prefix,
            'date_programs_li_id_suffix': date_programs_li_id_suffix,
            'date_programs_lis': '\n'.join(date_programs_lis)
        }

        return INDEX_HTML_TEMPLATES['date_programs_li.html.st'].safe_substitute(date_programs_li_html_template_fields)

    @classmethod
    def _render_date_separator_li_template(cls, date_separator_li_id_prefix, date_separator_li_id_suffix):
        date_separator_li_html_template_fields = {
            'date_separator_li_id_prefix': date_separator_li_id_prefix,
            'date_separator_li_id_suffix': date_separator_li_id_suffix
        }

        return INDEX_HTML_TEMPLATES['date_separator_li.html.st'].safe_substitute(date_separator_li_html_template_fields)

    @classmethod
    def _render_guide_group_select_options(cls, guide_provider, guide_group, providers):
        guide_group_select_options = []

        if guide_provider.lower() in providers:
            selected_provider = providers[guide_provider.lower()]
            provider_groups = selected_provider['epg'].get_groups()

            if guide_group in provider_groups:
                selected_channel_group = guide_group
            else:
                selected_channel_group = sorted(provider_groups)[0]
        else:
            selected_provider = providers[sorted(providers)[0]]
            provider_groups = selected_provider['epg'].get_groups()

            selected_channel_group = sorted(provider_groups)[0]

        for provider_name in sorted(providers):
            provider = providers[provider_name]

            for group in sorted(provider['epg'].get_groups()):
                guide_group_select_options_template = {
                    'guide_group_select_option_selected': 'selected="selected" '
                    if selected_provider == provider and selected_channel_group == group else '',
                    'guide_group_select_option_provider': provider['api']().__class__.__name__,
                    'guide_group_select_option_group': group
                }

                guide_group_select_options.append(
                    INDEX_HTML_TEMPLATES['guide_group_select_option.html.st'].safe_substitute(
                        guide_group_select_options_template))

        return guide_group_select_options

    @classmethod
    def _render_guide_lis_template(cls,
                                   is_server_secure,
                                   authorization_required,
                                   client_ip_address_type,
                                   client_uuid,
                                   guide_number_of_days,
                                   guide_provider,
                                   guide_group,
                                   providers):
        current_date_time_in_utc = datetime.now(pytz.utc)
        cutoff_date_time_in_utc = (current_date_time_in_utc.astimezone(tzlocal.get_localzone()) +
                                   timedelta(days=int(guide_number_of_days) + 1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0).astimezone(pytz.utc)

        if guide_provider.lower() in providers:
            provider = providers[guide_provider.lower()]
            provider_groups = provider['epg'].get_groups()

            if guide_group in provider_groups:
                channel_group = guide_group
            else:
                channel_group = sorted(provider_groups)[0]
        else:
            provider = providers[sorted(providers)[0]]
            provider_groups = provider['epg'].get_groups()

            channel_group = sorted(provider_groups)[0]

        db = IPTVProxyDatabase()
        channel_records = provider['sql'].query_channels(db)
        db.close_connection()

        channels = {channel_record['number']: channel_record
                    for channel_record in channel_records if channel_group == channel_record['group']}

        guide_lis = []

        for (channel_index, channel_record) in enumerate(channels.values()):
            channel_li_html_template_fields = cls._render_channel_li_template(is_server_secure,
                                                                              authorization_required,
                                                                              client_ip_address_type,
                                                                              client_uuid,
                                                                              channel_record,
                                                                              channel_index,
                                                                              channels,
                                                                              guide_provider)

            guide_lis.append(
                INDEX_HTML_TEMPLATES['channel_li.html.st'].safe_substitute(channel_li_html_template_fields))

            day_of_containing_date_li = None
            channel_programs_lis = []
            date_li_id_suffix = 0
            date_programs_lis = []
            program_li_input_label_span_id_suffix = 0

            db = IPTVProxyDatabase()
            program_records = provider['sql'].query_programs_by_channel_id(db, channel_record['id'])
            db.close_connection()

            for (program_index, program_record) in enumerate(
                    sorted(program_records,
                           key=lambda program_record_: datetime.strptime(
                               program_record_['start_date_time_in_utc'], '%Y-%m-%d %H:%M:%S%z'))):
                program_start_date_time_in_utc = datetime.strptime(program_record['start_date_time_in_utc'],
                                                                   '%Y-%m-%d %H:%M:%S%z')
                program_end_date_time_in_utc = datetime.strptime(program_record['end_date_time_in_utc'],
                                                                 '%Y-%m-%d %H:%M:%S%z')

                if current_date_time_in_utc >= program_end_date_time_in_utc:
                    continue

                program_start_date_time_in_local = program_start_date_time_in_utc.astimezone(
                    tzlocal.get_localzone())

                program_li_input_label_span_id_suffix += 1

                day_of_program_start_date_time_in_local = program_start_date_time_in_local.day

                if day_of_program_start_date_time_in_local != day_of_containing_date_li:
                    if day_of_containing_date_li:
                        if date_programs_lis:
                            channel_programs_lis.append(cls._render_date_programs_li_template(
                                date_programs_lis,
                                channel_li_html_template_fields['channel_li_id_prefix'],
                                date_li_id_suffix))

                            channel_programs_lis.append(cls._render_date_separator_li_template(
                                channel_li_html_template_fields['channel_li_id_prefix'],
                                date_li_id_suffix))

                            date_programs_lis = []
                            date_li_id_suffix += 1
                        else:
                            channel_programs_lis.pop()

                    channel_programs_lis.append(cls._render_date_li_template(
                        channel_li_html_template_fields['channel_li_id_prefix'],
                        date_li_id_suffix,
                        program_start_date_time_in_local.strftime('%B %d, %Y')))

                    day_of_containing_date_li = program_start_date_time_in_local.day

                if cutoff_date_time_in_utc > program_start_date_time_in_utc:
                    date_programs_lis.append(INDEX_HTML_TEMPLATES['program_li.html.st'].safe_substitute(
                        cls._render_program_li_template(channel_record,
                                                        program_record,
                                                        channel_li_html_template_fields[
                                                            'channel_li_id_prefix'],
                                                        program_li_input_label_span_id_suffix,
                                                        date_li_id_suffix,
                                                        guide_provider)))

                if program_index == len(program_records) - 1:
                    if day_of_containing_date_li:
                        if date_programs_lis:
                            channel_programs_lis.append(cls._render_date_programs_li_template(
                                date_programs_lis,
                                channel_li_html_template_fields['channel_li_id_prefix'],
                                date_li_id_suffix))

                            channel_programs_lis.append(cls._render_date_separator_li_template(
                                channel_li_html_template_fields['channel_li_id_prefix'],
                                date_li_id_suffix))

                            date_programs_lis = []
                            date_li_id_suffix += 1
                        else:
                            channel_programs_lis.pop()

            if channel_programs_lis:
                guide_lis.append(cls._render_channel_programs_li_template(
                    channel_li_html_template_fields['channel_li_id_prefix'],
                    channel_programs_lis))

        return guide_lis

    @classmethod
    def _render_iptv_proxy_script_template(cls, authorization_required, guide_number_of_days, streaming_protocol):
        iptv_proxy_script_javascript_template = {
            'authorization_basic_password': '{0}'.format(
                base64.b64encode(':{0}'.format(
                    cls._configuration['SERVER_PASSWORD']).encode()).decode()) if authorization_required else '',
            'last_selected_guide_number_of_days': guide_number_of_days,
            'last_selected_streaming_protocol': streaming_protocol
        }

        return INDEX_HTML_TEMPLATES['iptv_proxy_script.js.st'].safe_substitute(
            iptv_proxy_script_javascript_template)

    @classmethod
    def _render_program_li_template(cls,
                                    channel_record,
                                    program_record,
                                    program_li_id_prefix,
                                    program_li_input_label_span_id_suffix,
                                    program_li_input_name_suffix,
                                    guide_provider):
        program_start_date_time_in_utc = datetime.strptime(program_record['start_date_time_in_utc'],
                                                           '%Y-%m-%d %H:%M:%S%z')
        program_end_date_time_in_utc = datetime.strptime(program_record['end_date_time_in_utc'], '%Y-%m-%d %H:%M:%S%z')

        program_start_date_time_in_local = program_start_date_time_in_utc.astimezone(tzlocal.get_localzone())
        program_end_date_time_in_local = program_end_date_time_in_utc.astimezone(tzlocal.get_localzone())

        program_post_recording_body = {
            'data': {
                'type': 'recordings',
                'attributes': {
                    'channel_number': '{0:02}'.format(int(channel_record['number'])),
                    'end_date_time_in_utc': '{0}'.format(program_end_date_time_in_utc.strftime('%Y-%m-%d %H:%M:%S')),
                    'program_title': '{0}'.format(html.escape(program_record['title'])),
                    'provider': '{0}'.format(guide_provider),
                    'start_date_time_in_utc': '{0}'.format(program_start_date_time_in_utc.strftime('%Y-%m-%d %H:%M:%S'))
                }
            }
        }

        return {
            'program_li_id_prefix': program_li_id_prefix,
            'program_li_input_label_span_id_suffix': program_li_input_label_span_id_suffix,
            'program_li_input_name_suffix': program_li_input_name_suffix,
            'program_li_input_value': json.dumps(program_post_recording_body),
            'program_li_label_start_time': program_start_date_time_in_local.strftime('%H:%M:%S'),
            'program_li_label_end_time': program_end_date_time_in_local.strftime('%H:%M:%S'),
            'program_li_label_program_title': html.escape(program_record['title']),
            'program_li_span_description': html.escape(program_record['description'])
        }

    @classmethod
    def _render_recordings_tables_rows_template(cls,
                                                is_server_secure,
                                                authorization_required,
                                                client_uuid,
                                                server_hostname,
                                                server_port):
        recordings = IPTVProxyPVR.get_recordings()

        recording_table_rows = {
            'live': [],
            'persisted': [],
            'scheduled': []
        }

        for recording in recordings:
            spacing_and_control_spans_display = 'display: none;'
            recording_source = None

            if recording.status == IPTVProxyRecordingStatus.PERSISTED.value:
                spacing_and_control_spans_display = 'display: inline-block;'

                recording_source = {
                    'type': 'vod',
                    'hls': {
                        'videoSource': '{0}'.format(IPTVProxyPVR.generate_recording_playlist_url(
                            is_server_secure,
                            server_hostname,
                            server_port,
                            client_uuid,
                            recording.base_recording_directory,
                            cls._configuration['SERVER_PASSWORD'] if authorization_required else None))
                    }
                }

            recordings_table_row_html_template_field = {
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
                INDEX_HTML_TEMPLATES['recordings_table_row.html.st'].safe_substitute(
                    recordings_table_row_html_template_field))

        return recording_table_rows

    @classmethod
    def _render_separator_li_template(cls, separator_li_id_prefix, separator_li_id_suffix):
        separator_li_html_template_fields = {
            'separator_li_id_prefix': separator_li_id_prefix,
            'separator_li_id_suffix': separator_li_id_suffix
        }

        return INDEX_HTML_TEMPLATES['separator_li.html.st'].safe_substitute(separator_li_html_template_fields)

    @classmethod
    def render_errors_template(cls, http_error_code, http_error_title, http_error_details):
        with cls._lock:
            for template_file_name in ERROR_HTML_TEMPLATES:
                ERROR_HTML_TEMPLATES[template_file_name] = IPTVProxyUtility.read_template(template_file_name)

            login_template_fields = {
                'iptv_proxy_version': VERSION,
                'http_error_code': http_error_code,
                'http_error_title': http_error_title,
                'http_error_details': http_error_details
            }

            return ERROR_HTML_TEMPLATES['errors.html.st'].safe_substitute(login_template_fields)

    @classmethod
    def render_guide_div_template(cls,
                                  is_server_secure,
                                  authorization_required,
                                  client_ip_address,
                                  client_uuid,
                                  guide_number_of_days,
                                  guide_provider,
                                  guide_group,
                                  providers):
        with cls._lock:
            cls._configuration = IPTVProxyConfiguration.get_configuration_copy()

            client_ip_address_type = IPTVProxyUtility.determine_ip_address_type(client_ip_address)

            for template_file_name in INDEX_HTML_TEMPLATES:
                INDEX_HTML_TEMPLATES[template_file_name] = IPTVProxyUtility.read_template(template_file_name)

            guide_lis = cls._render_guide_lis_template(is_server_secure,
                                                       authorization_required,
                                                       client_ip_address_type,
                                                       client_uuid,
                                                       guide_number_of_days,
                                                       guide_provider,
                                                       guide_group,
                                                       providers)

            guide_div_template_fields = {
                'guide_lis': '\n'.join(guide_lis)
            }

            return INDEX_HTML_TEMPLATES['guide_div.html.st'].safe_substitute(guide_div_template_fields)

    @classmethod
    def render_index_template(cls,
                              is_server_secure,
                              authorization_required,
                              client_ip_address,
                              client_uuid,
                              guide_number_of_days,
                              guide_provider,
                              guide_group,
                              streaming_protocol,
                              providers):
        with cls._lock:
            cls._configuration = IPTVProxyConfiguration.get_configuration_copy()

            client_ip_address_type = IPTVProxyUtility.determine_ip_address_type(client_ip_address)
            server_hostname = cls._configuration['SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value)]
            server_http_port = cls._configuration['SERVER_HTTP_PORT']
            server_https_port = cls._configuration['SERVER_HTTPS_PORT']

            for template_file_name in INDEX_HTML_TEMPLATES:
                INDEX_HTML_TEMPLATES[template_file_name] = IPTVProxyUtility.read_template(template_file_name)

            guide_group_select_options = cls._render_guide_group_select_options(guide_provider, guide_group, providers)

            guide_lis = cls._render_guide_lis_template(is_server_secure,
                                                       authorization_required,
                                                       client_ip_address_type,
                                                       client_uuid,
                                                       guide_number_of_days,
                                                       guide_provider,
                                                       guide_group,
                                                       providers)
            recording_table_rows = cls._render_recordings_tables_rows_template(
                is_server_secure,
                authorization_required,
                client_uuid,
                server_hostname,
                server_https_port if is_server_secure else server_http_port)

            index_html_template_fields = {
                'iptv_proxy_script': cls._render_iptv_proxy_script_template(authorization_required,
                                                                            guide_number_of_days,
                                                                            streaming_protocol),
                'iptv_proxy_version': VERSION,
                'guide_group_select_options': '\n'.join(guide_group_select_options),
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
                '{0}_image_style'.format(streaming_protocol): 'max-width: 92px; padding: 8px;',
                'guide_lis': '\n'.join(guide_lis),
                'live_no_recordings_li_style': 'display:none' if recording_table_rows['live'] else '',
                'live_recordings_li_style': '' if recording_table_rows['live'] else 'display:none',
                'live_recordings_table_rows': '\n'.join(recording_table_rows['live']),
                'persisted_no_recordings_li_style': 'display:none' if recording_table_rows['persisted'] else '',
                'persisted_recordings_li_style': '' if recording_table_rows['persisted'] else 'display:none',
                'persisted_recordings_table_rows': '\n'.join(recording_table_rows['persisted']),
                'scheduled_no_recordings_li_style': 'display:none' if recording_table_rows['scheduled'] else '',
                'scheduled_recordings_li_style': '' if recording_table_rows['scheduled'] else 'display:none',
                'scheduled_recordings_table_rows': '\n'.join(recording_table_rows['scheduled']),
                'configuration_server_password': cls._configuration['SERVER_PASSWORD'],
                'configuration_server_http_port': server_http_port,
                'configuration_server_https_port': server_https_port,
                'configuration_server_hostname_loopback': cls._configuration['SERVER_HOSTNAME_LOOPBACK'],
                'configuration_server_hostname_private': cls._configuration['SERVER_HOSTNAME_PRIVATE'],
                'configuration_server_hostname_public': cls._configuration['SERVER_HOSTNAME_PUBLIC'],
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
                'configuration_smooth_streams_username': '',
                'configuration_smooth_streams_password': '',
                'configuration_smooth_streams_playlist_protocol_hls_selected': '',
                'configuration_smooth_streams_playlist_protocol_rtmp_selected': '',
                'configuration_smooth_streams_playlist_type_dynamic_selected': '',
                'configuration_smooth_streams_playlist_type_static_selected': '',
                'configuration_smooth_streams_epg_source_smoothstreams_selected': '',
                'configuration_smooth_streams_epg_source_fog_selected': '',
                'configuration_vader_streams_username': '',
                'configuration_vader_streams_password': '',
                'configuration_vader_streams_playlist_protocol_hls_selected': '',
                'configuration_vader_streams_playlist_protocol_mpegts_selected': '',
                'configuration_vader_streams_playlist_type_dynamic_selected': '',
                'configuration_vader_streams_playlist_type_static_selected': '',
                'configuration_info_selected': '',
                'configuration_debug_selected': '',
                'configuration_trace_selected': '',
                'configuration_{0}_selected'.format(cls._configuration['LOGGING_LEVEL'].lower()): 'selected="selected" '
            }

            if 'SMOOTH_STREAMS_SERVICE' in cls._configuration:
                index_html_template_fields['configuration_{0}_selected'.format(
                    cls._configuration['SMOOTH_STREAMS_SERVICE'].lower())] = 'selected="selected" '
            if 'SMOOTH_STREAMS_SERVER' in cls._configuration:
                index_html_template_fields['configuration_{0}_selected'.format(
                    cls._configuration['SMOOTH_STREAMS_SERVER'].lower().replace('-', '_'))] = 'selected="selected" '
            if 'SMOOTH_STREAMS_USERNAME' in cls._configuration:
                index_html_template_fields['configuration_smooth_streams_username'] = cls._configuration[
                    'SMOOTH_STREAMS_USERNAME']
            if 'SMOOTH_STREAMS_PASSWORD' in cls._configuration:
                index_html_template_fields['configuration_smooth_streams_password'] = cls._configuration[
                    'SMOOTH_STREAMS_PASSWORD']
            if 'SMOOTH_STREAMS_PLAYLIST_PROTOCOL' in cls._configuration:
                index_html_template_fields['configuration_smooth_streams_playlist_protocol_{0}_selected'.format(
                    cls._configuration['SMOOTH_STREAMS_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
            if 'SMOOTH_STREAMS_PLAYLIST_TYPE' in cls._configuration:
                index_html_template_fields['configuration_smooth_streams_playlist_type_{0}_selected'.format(
                    cls._configuration['SMOOTH_STREAMS_PLAYLIST_TYPE'].lower())] = 'selected="selected" '
            if 'SMOOTH_STREAMS_EPG_SOURCE' in cls._configuration:
                index_html_template_fields['configuration_smooth_streams_epg_source_{0}_selected'.format(
                    cls._configuration['SMOOTH_STREAMS_EPG_SOURCE'].lower())] = 'selected="selected" '

            if 'VADER_STREAMS_SERVER' in cls._configuration:
                index_html_template_fields['configuration_{0}_selected'.format(
                    cls._configuration['VADER_STREAMS_SERVER'].lower().replace('-', '_'))] = 'selected="selected" '
            if 'VADER_STREAMS_USERNAME' in cls._configuration:
                index_html_template_fields['configuration_vader_streams_username'] = cls._configuration[
                    'VADER_STREAMS_USERNAME']
            if 'VADER_STREAMS_PASSWORD' in cls._configuration:
                index_html_template_fields['configuration_vader_streams_password'] = cls._configuration[
                    'VADER_STREAMS_PASSWORD']
            if 'VADER_STREAMS_PLAYLIST_PROTOCOL' in cls._configuration:
                index_html_template_fields['configuration_vader_streams_playlist_protocol_{0}_selected'.format(
                    cls._configuration['VADER_STREAMS_PLAYLIST_PROTOCOL'].lower())] = 'selected="selected" '
            if 'VADER_STREAMS_PLAYLIST_TYPE' in cls._configuration:
                index_html_template_fields['configuration_vader_streams_playlist_type_{0}_selected'.format(
                    cls._configuration['VADER_STREAMS_PLAYLIST_TYPE'].lower())] = 'selected="selected" '

            return INDEX_HTML_TEMPLATES['index.html.st'].safe_substitute(index_html_template_fields)

    @classmethod
    def render_login_template(cls):
        with cls._lock:
            for template_file_name in LOGIN_HTML_TEMPLATES:
                LOGIN_HTML_TEMPLATES[template_file_name] = IPTVProxyUtility.read_template(template_file_name)

            login_template_fields = {
                'iptv_proxy_version': VERSION
            }

            return LOGIN_HTML_TEMPLATES['login.html.st'].safe_substitute(login_template_fields)
