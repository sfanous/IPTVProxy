import copy
import hashlib
import html
import json
import logging
import os
import pickle
import re
import sys
import traceback
import uuid
from abc import ABC
from abc import abstractmethod
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from threading import Timer

import ijson
import pytz
import requests
import tzlocal
from lxml import etree

from iptv_proxy.configuration import Configuration
from iptv_proxy.configuration import OptionalSettings
from iptv_proxy.constants import CHANNEL_ICONS_DIRECTORY_PATH
from iptv_proxy.constants import VERSION
from iptv_proxy.enums import EPGStyle
from iptv_proxy.providers import ProvidersController
from iptv_proxy.security import SecurityManager
from iptv_proxy.utilities import Utility
from iptv_proxy.xmltv import XMLTVActor
from iptv_proxy.xmltv import XMLTVAdapter
from iptv_proxy.xmltv import XMLTVAspect
from iptv_proxy.xmltv import XMLTVAudio
from iptv_proxy.xmltv import XMLTVCategory
from iptv_proxy.xmltv import XMLTVChannel
from iptv_proxy.xmltv import XMLTVColour
from iptv_proxy.xmltv import XMLTVCommentator
from iptv_proxy.xmltv import XMLTVComposer
from iptv_proxy.xmltv import XMLTVCountry
from iptv_proxy.xmltv import XMLTVCredits
from iptv_proxy.xmltv import XMLTVDate
from iptv_proxy.xmltv import XMLTVDescription
from iptv_proxy.xmltv import XMLTVDirector
from iptv_proxy.xmltv import XMLTVDisplayName
from iptv_proxy.xmltv import XMLTVEditor
from iptv_proxy.xmltv import XMLTVEpisodeNumber
from iptv_proxy.xmltv import XMLTVGuest
from iptv_proxy.xmltv import XMLTVIcon
from iptv_proxy.xmltv import XMLTVKeyword
from iptv_proxy.xmltv import XMLTVLanguage
from iptv_proxy.xmltv import XMLTVLastChance
from iptv_proxy.xmltv import XMLTVLength
from iptv_proxy.xmltv import XMLTVNew
from iptv_proxy.xmltv import XMLTVOriginalLanguage
from iptv_proxy.xmltv import XMLTVPremiere
from iptv_proxy.xmltv import XMLTVPresent
from iptv_proxy.xmltv import XMLTVPresenter
from iptv_proxy.xmltv import XMLTVPreviouslyShown
from iptv_proxy.xmltv import XMLTVProducer
from iptv_proxy.xmltv import XMLTVProgram
from iptv_proxy.xmltv import XMLTVQuality
from iptv_proxy.xmltv import XMLTVRating
from iptv_proxy.xmltv import XMLTVReview
from iptv_proxy.xmltv import XMLTVStarRating
from iptv_proxy.xmltv import XMLTVStereo
from iptv_proxy.xmltv import XMLTVSubTitle
from iptv_proxy.xmltv import XMLTVSubtitles
from iptv_proxy.xmltv import XMLTVTitle
from iptv_proxy.xmltv import XMLTVURL
from iptv_proxy.xmltv import XMLTVValue
from iptv_proxy.xmltv import XMLTVVideo
from iptv_proxy.xmltv import XMLTVWriter

logger = logging.getLogger(__name__)


class ProviderEPG(ABC):
    __slots__ = []

    _channel_group_map = None
    _channel_group_map_lock = None
    _channel_name_map = None
    _channel_name_map_lock = None
    _do_use_provider_icons = None
    _do_use_provider_icons_lock = None
    _ignored_channels = None
    _ignored_channels_lock = None
    _ignored_m3u8_groups = None
    _ignored_m3u8_groups_lock = None
    _lock = None
    _m3u8_group_map = None
    _m3u8_group_map_lock = None
    _provider_name = None
    _refresh_epg_timer = None
    _supported_attributes = []
    _update_times = None
    _update_times_lock = None

    @classmethod
    def _apply_channel_transformations(cls,
                                       channel,
                                       channel_name_map,
                                       do_use_iptv_proxy_icons,
                                       channel_group_map=None,
                                       m3u8_group_map=None):
        if channel_group_map is not None:
            for channel_group_map_regular_expression in channel_group_map['name']:
                for display_name in channel.display_names:
                    if re.search(channel_group_map_regular_expression, display_name.text):
                        channel.m3u8_group = channel_group_map['name'][channel_group_map_regular_expression]

                        break

            for channel_group_name in sorted(channel_group_map['number']):
                if channel.number in channel_group_map['number'][channel_group_name]:
                    channel.m3u8_group = channel_group_name

                    break

        if m3u8_group_map is not None:
            for m3u8_group_map_regular_expression in m3u8_group_map:
                if re.search(m3u8_group_map_regular_expression, channel.m3u8_group):
                    channel.m3u8_group = m3u8_group_map[m3u8_group_map_regular_expression]

                    break

        channel.xmltv_id = '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID, '{0} - {1}'.format(channel.number,
                                                                                          channel.m3u8_group)))

        do_set_channel_display_names = False
        channel_display_names = []

        for display_name in channel.display_names:
            if display_name.text in channel_name_map:
                do_set_channel_display_names = True

                display_name.text = channel_name_map[display_name.text]

            channel_display_names.append(display_name)

        if do_set_channel_display_names:
            channel.display_names = channel_display_names

        if do_use_iptv_proxy_icons:
            for channel_icon_file_name in os.listdir(os.path.join(CHANNEL_ICONS_DIRECTORY_PATH, cls._provider_name)):
                if '{0}.png'.format(channel.number) == channel_icon_file_name:
                    break
            else:
                channel_icon_file_name = '0.png'

            channel.icons = [XMLTVIcon(source='{0}{1}/{2}{3}'.format('http{0}://{1}:{2}/',
                                                                     cls._provider_name,
                                                                     channel_icon_file_name,
                                                                     '{3}'),
                                       width=None,
                                       height=None)]

    @classmethod
    def _calculate_epg_settings_md5(cls, **kwargs):
        epg_settings = OrderedDict()

        for kwarg in sorted(kwargs):
            if hasattr(cls, '_{0}'.format(kwarg)) and getattr(cls, '_{0}'.format(kwarg)) is not None:
                epg_settings[kwarg] = kwargs[kwarg]

        epg_settings['epg_source'] = Configuration.get_configuration_parameter(
            '{0}_EPG_SOURCE'.format(cls._provider_name.upper()))

        if epg_settings['epg_source'] == ProvidersController.get_provider_map_class(
                cls._provider_name).epg_source_enum().OTHER.value:
            epg_settings['epg_url'] = Configuration.get_configuration_parameter(
                '{0}_EPG_URL'.format(cls._provider_name.upper()))

        return hashlib.md5(json.dumps(epg_settings, sort_keys=True).encode()).hexdigest()

    @classmethod
    def _cancel_refresh_epg_timer(cls):
        if cls._refresh_epg_timer is not None:
            cls._refresh_epg_timer.cancel()
            cls._refresh_epg_timer = None

    @classmethod
    def _do_update_epg(cls, **kwargs):
        do_update_epg = False

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                epg_settings_md5 = None
                last_epg_refresh_date_time_in_utc = None

                for setting_row in provider_map_class.database_access_class().query_settings(db_session):
                    if setting_row.name == 'epg_settings_md5':
                        epg_settings_md5 = setting_row.value
                    elif setting_row.name == 'last_epg_refresh_date_time_in_utc':
                        last_epg_refresh_date_time_in_utc = datetime.strptime(setting_row.value, '%Y-%m-%d %H:%M:%S%z')

                current_date_time_in_utc = datetime.now(pytz.utc)

                if cls._calculate_epg_settings_md5(**kwargs) != epg_settings_md5 or \
                        current_date_time_in_utc >= last_epg_refresh_date_time_in_utc + timedelta(days=1):
                    do_update_epg = True
                else:
                    with cls._update_times_lock.reader_lock:
                        next_epg_refresh_minimum_interval = 86400

                        for update_time in cls._update_times:
                            next_epg_refresh_date_time_in_utc = last_epg_refresh_date_time_in_utc.astimezone(
                                tzlocal.get_localzone()).replace(hour=int(update_time[0:2]),
                                                                 minute=int(update_time[3:5]),
                                                                 second=int(update_time[6:8])).astimezone(pytz.utc)

                            interval = (next_epg_refresh_date_time_in_utc -
                                        last_epg_refresh_date_time_in_utc).total_seconds()

                            if 0 < interval < next_epg_refresh_minimum_interval:
                                next_epg_refresh_minimum_interval = interval
                            else:
                                next_epg_refresh_date_time_in_utc = next_epg_refresh_date_time_in_utc + \
                                                                    timedelta(days=1)

                            if current_date_time_in_utc > next_epg_refresh_date_time_in_utc:
                                do_update_epg = True

                                break

            finally:
                db_session.close()

            return do_update_epg

    @classmethod
    def _initialize(cls, **kwargs):
        if cls._channel_group_map_lock is not None:
            with cls._channel_group_map_lock.reader_lock:
                kwargs['channel_group_map'] = copy.deepcopy(cls._channel_group_map)
        if cls._channel_name_map_lock is not None:
            with cls._channel_name_map_lock.reader_lock:
                kwargs['channel_name_map'] = copy.deepcopy(cls._channel_name_map)
        if cls._do_use_provider_icons_lock is not None:
            with cls._do_use_provider_icons_lock.reader_lock:
                kwargs['do_use_provider_icons'] = cls._do_use_provider_icons
        if cls._ignored_channels_lock is not None:
            with cls._ignored_channels_lock.reader_lock:
                kwargs['ignored_channels'] = copy.deepcopy(cls._ignored_channels)
        if cls._ignored_m3u8_groups_lock is not None:
            with cls._ignored_m3u8_groups_lock.reader_lock:
                kwargs['ignored_m3u8_groups'] = copy.deepcopy(cls._ignored_m3u8_groups)
        if cls._m3u8_group_map_lock is not None:
            with cls._m3u8_group_map_lock.reader_lock:
                kwargs['m3u8_group_map'] = copy.deepcopy(cls._m3u8_group_map)

        if cls._do_update_epg(**kwargs):
            logger.debug('Updating EPG')

            cls._update_epg(**kwargs)
        else:
            cls._initialize_refresh_epg_timer()

    @classmethod
    def _initialize_class_variables(cls):
        if cls._channel_group_map_lock is not None:
            try:
                cls.set_channel_group_map(OptionalSettings.get_optional_settings_parameter(
                    '{0}_channel_group_map'.format(cls._provider_name)))
            except KeyError:
                pass

        if cls._channel_name_map_lock is not None:
            try:
                cls.set_channel_name_map(OptionalSettings.get_optional_settings_parameter(
                    '{0}_channel_name_map'.format(cls._provider_name)))
            except KeyError:
                pass

        if cls._do_use_provider_icons_lock is not None:
            try:
                cls.set_do_use_provider_icons(OptionalSettings.get_optional_settings_parameter(
                    'use_{0}_icons'.format(cls._provider_name)))
            except KeyError:
                pass

        if cls._ignored_channels_lock is not None:
            try:
                cls.set_ignored_channels(OptionalSettings.get_optional_settings_parameter(
                    '{0}_ignored_channels'.format(cls._provider_name)))
            except KeyError:
                pass

        if cls._ignored_m3u8_groups_lock is not None:
            try:
                cls.set_ignored_m3u8_groups(
                    OptionalSettings.get_optional_settings_parameter(
                        '{0}_ignored_m3u8_groups'.format(cls._provider_name)))
            except KeyError:
                pass

        if cls._m3u8_group_map_lock is not None:
            try:
                cls.set_m3u8_group_map(OptionalSettings.get_optional_settings_parameter(
                    '{0}_m3u8_group_map'.format(cls._provider_name)))
            except KeyError:
                pass

        if cls._update_times_lock is not None:
            try:
                cls.set_update_times(OptionalSettings.get_optional_settings_parameter(
                    '{0}_epg_update_times'.format(cls._provider_name)))
            except KeyError:
                pass

    @classmethod
    def _initialize_refresh_epg_timer(cls, do_set_timer_for_retry=False):
        current_date_time_in_utc = datetime.now(pytz.utc)

        if do_set_timer_for_retry:
            refresh_epg_date_time_in_utc = (current_date_time_in_utc.astimezone(
                tzlocal.get_localzone()).replace(minute=0,
                                                 second=0,
                                                 microsecond=0) + timedelta(hours=1)).astimezone(pytz.utc)

            cls._start_refresh_epg_timer((refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds())
        else:
            with cls._update_times_lock.reader_lock:
                minimum_refresh_epg_time_interval = 172800

                for update_time in cls._update_times:
                    refresh_epg_date_time_in_utc = current_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()).replace(hour=int(update_time[0:2]),
                                                         minute=int(update_time[3:5]),
                                                         second=int(update_time[6:8])).astimezone(pytz.utc)

                    interval = (refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds()

                    if 0 < interval < minimum_refresh_epg_time_interval:
                        minimum_refresh_epg_time_interval = interval
                    elif interval + 86400 < minimum_refresh_epg_time_interval:
                        minimum_refresh_epg_time_interval = interval + 86400

                cls._cancel_refresh_epg_timer()
                cls._start_refresh_epg_timer(minimum_refresh_epg_time_interval)

    @classmethod
    def _parse_external_epg_xml(cls, db_session, **kwargs):
        epg_xml_stream = cls._request_external_epg_xml()

        logger.debug('Processing external XML EPG')

        if 'channel_name_map' in kwargs:
            channel_name_map = kwargs['channel_name_map']
        else:
            channel_name_map = {}

        if 'do_use_provider_icons' in kwargs:
            do_use_provider_icons = kwargs['do_use_provider_icons']
        else:
            do_use_provider_icons = True

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        parsed_channel_xmltv_id_to_channel = {}
        number_of_objects_added_to_db_session = 0

        tv_element = None

        try:
            for (event, element) in etree.iterparse(epg_xml_stream,
                                                    events=('start', 'end'),
                                                    tag=('channel', 'programme', 'tv')):
                if event == 'end':
                    if element.tag == 'channel':
                        channel_m3u8_group = provider_map_class.constants_class().PROVIDER_NAME
                        channel_number = None
                        channel_xmltv_id = element.get('id')
                        channel_display_names = []
                        channel_icons = []
                        channel_urls = []

                        for sub_element in list(element):
                            if sub_element.tag == 'display-name':
                                if sub_element.text.isdigit():
                                    channel_number = int(sub_element.text)
                                else:
                                    channel_display_names.append(XMLTVDisplayName(language=sub_element.get('language'),
                                                                                  text=sub_element.text))
                            elif sub_element.tag == 'icon':
                                channel_icons.append(XMLTVIcon(source=sub_element.get('src'),
                                                               width=sub_element.get('width'),
                                                               height=sub_element.get('height')))
                            elif sub_element.tag == 'url':
                                channel_urls.append(XMLTVURL(text=sub_element.text))

                        channel = XMLTVChannel(provider=provider_map_class.constants_class().PROVIDER_NAME,
                                               m3u8_group=channel_m3u8_group,
                                               xmltv_id=channel_xmltv_id,
                                               number=channel_number,
                                               display_names=channel_display_names,
                                               icons=channel_icons,
                                               urls=channel_urls)
                        cls._apply_channel_transformations(channel,
                                                           channel_name_map,
                                                           not do_use_provider_icons)

                        parsed_channel_xmltv_id_to_channel[channel_xmltv_id] = channel

                        db_session.add(provider_map_class.channel_class()(
                            id_=channel.xmltv_id,
                            m3u8_group=channel.m3u8_group,
                            number=channel.number,
                            name=channel.display_names[0].text,
                            pickle=pickle.dumps(channel, protocol=pickle.HIGHEST_PROTOCOL),
                            complete_xmltv=channel.format(minimal_xmltv=False),
                            minimal_xmltv=channel.format()))
                        number_of_objects_added_to_db_session += 1

                        element.clear()
                        tv_element.clear()
                    elif element.tag == 'programme':
                        program_start = datetime.strptime(element.get('start'), '%Y%m%d%H%M%S %z').astimezone(pytz.utc)
                        program_stop = datetime.strptime(element.get('stop'), '%Y%m%d%H%M%S %z').astimezone(pytz.utc)
                        program_pdc_start = element.get('pdc-start')
                        program_vps_start = element.get('vps-start')
                        program_show_view = element.get('showview')
                        program_video_plus = element.get('videoplus')
                        program_channel_xmltv_id = element.get('channel')
                        program_clump_index = element.get('clumpidx')
                        program_titles = []
                        program_sub_titles = []
                        program_descriptions = []
                        program_credits = None
                        program_date = None
                        program_categories = []
                        program_keywords = []
                        program_language = None
                        program_original_language = None
                        program_length = None
                        program_icons = []
                        program_urls = []
                        program_countries = []
                        program_episode_numbers = []
                        program_video = None
                        program_audio = None
                        program_previously_shown = None
                        program_premiere = None
                        program_last_chance = None
                        program_new = None
                        program_subtitles = []
                        program_ratings = []
                        program_star_ratings = []
                        program_reviews = []

                        for sub_element in list(element):
                            if sub_element.tag == 'title':
                                program_titles.append(XMLTVTitle(language=sub_element.get('lang'),
                                                                 text=sub_element.text))
                            elif sub_element.tag == 'sub-title':
                                program_sub_titles.append(XMLTVSubTitle(language=sub_element.get('lang'),
                                                                        text=sub_element.text))
                            elif sub_element.tag == 'desc':
                                program_descriptions.append(XMLTVDescription(language=sub_element.get('lang'),
                                                                             text=sub_element.text))
                            elif sub_element.tag == 'credits':
                                credits_actors = []
                                credits_adapters = []
                                credits_commentators = []
                                credits_composers = []
                                credits_directors = []
                                credits_editors = []
                                credits_guests = []
                                credits_presenters = []
                                credits_producers = []
                                credits_writers = []

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'actor':
                                        credits_actors.append(XMLTVActor(sub_sub_element.get('role'),
                                                                         sub_sub_element.text))
                                    elif sub_sub_element.tag == 'adapter':
                                        credits_adapters.append(XMLTVAdapter(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'commentator':
                                        credits_commentators.append(XMLTVCommentator(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'composer':
                                        credits_composers.append(XMLTVComposer(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'director':
                                        credits_directors.append(XMLTVDirector(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'editor':
                                        credits_editors.append(XMLTVEditor(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'guest':
                                        credits_guests.append(XMLTVGuest(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'presenter':
                                        credits_presenters.append(XMLTVPresenter(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'producer':
                                        credits_producers.append(XMLTVProducer(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'writer':
                                        credits_writers.append(XMLTVWriter(sub_sub_element.text))

                                program_credits = XMLTVCredits(actors=credits_actors,
                                                               adapters=credits_adapters,
                                                               commentators=credits_commentators,
                                                               composers=credits_composers,
                                                               directors=credits_directors,
                                                               editors=credits_editors,
                                                               guests=credits_guests,
                                                               presenters=credits_presenters,
                                                               producers=credits_producers,
                                                               writers=credits_writers)
                            elif sub_element.tag == 'date':
                                program_date = XMLTVDate(text=sub_element.text)
                            elif sub_element.tag == 'category':
                                program_categories.append(XMLTVCategory(language=sub_element.get('lang'),
                                                                        text=sub_element.text))
                            elif sub_element.tag == 'keyword':
                                program_keywords.append(XMLTVKeyword(language=sub_element.get('lang'),
                                                                     text=sub_element.text))
                            elif sub_element.tag == 'language':
                                program_language = XMLTVLanguage(language=sub_element.get('lang'),
                                                                 text=sub_element.text)
                            elif sub_element.tag == 'orig-language':
                                program_original_language = XMLTVOriginalLanguage(language=sub_element.get('lang'),
                                                                                  text=sub_element.text)
                            elif sub_element.tag == 'length':
                                program_length = XMLTVLength(units=sub_element.get('units'),
                                                             text=sub_element.text)
                            elif sub_element.tag == 'icon':
                                program_icons.append(XMLTVIcon(source=sub_element.get('src'),
                                                               width=sub_element.get('width'),
                                                               height=sub_element.get('height')))
                            elif sub_element.tag == 'url':
                                program_urls.append(XMLTVURL(text=sub_element.text))
                            elif sub_element.tag == 'country':
                                program_countries.append(XMLTVCountry(language=sub_element.get('lang'),
                                                                      text=sub_element.text))
                            elif sub_element.tag == 'episode-num':
                                program_episode_numbers.append(XMLTVEpisodeNumber(system=sub_element.get('system'),
                                                                                  text=sub_element.text))
                            elif sub_element.tag == 'video':
                                video_present = None
                                video_colour = None
                                video_aspect = None
                                video_quality = None

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'present':
                                        video_present = XMLTVPresent(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'colour':
                                        video_colour = XMLTVColour(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'aspect':
                                        video_aspect = XMLTVAspect(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'quality':
                                        video_quality = XMLTVQuality(sub_sub_element.text)

                                if video_present is not None or video_colour is not None or \
                                        video_aspect is not None or video_quality is not None:
                                    program_video = XMLTVVideo(present=video_present,
                                                               colour=video_colour,
                                                               aspect=video_aspect,
                                                               quality=video_quality)
                            elif sub_element.tag == 'audio':
                                audio_present = None
                                audio_stereo = None

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'present':
                                        audio_present = XMLTVPresent(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'stereo':
                                        audio_stereo = XMLTVStereo(sub_sub_element.text)

                                if audio_present is not None or audio_stereo is not None:
                                    program_audio = XMLTVAudio(present=audio_present,
                                                               stereo=audio_stereo)
                            elif sub_element.tag == 'previously-shown':
                                program_previously_shown = XMLTVPreviouslyShown(start=sub_element.get('start'),
                                                                                channel=sub_element.get('channel'))
                            elif sub_element.tag == 'premiere':
                                program_premiere = XMLTVPremiere(language=sub_element.get('lang'),
                                                                 text=sub_element.text)
                            elif sub_element.tag == 'last-chance':
                                program_last_chance = XMLTVLastChance(language=sub_element.get('lang'),
                                                                      text=sub_element.text)
                            elif sub_element.tag == 'new':
                                program_new = XMLTVNew()
                            elif sub_element.tag == 'subtitles':
                                subtitles_type = sub_element.get('type')
                                subtitles_language = None

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'language':
                                        subtitles_language = XMLTVLanguage(language=sub_sub_element.get('lang'),
                                                                           text=sub_sub_element.text)

                                program_subtitles.append(XMLTVSubtitles(type_=subtitles_type,
                                                                        language=subtitles_language))
                            elif sub_element.tag == 'rating':
                                rating_system = sub_element.get('system')
                                rating_value = None
                                rating_icons = []

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'value':
                                        rating_value = XMLTVValue(text=sub_sub_element.text)
                                    elif sub_sub_element.tag == 'icon':
                                        rating_icons.append(XMLTVIcon(source=sub_sub_element.get('src'),
                                                                      width=sub_sub_element.get('width'),
                                                                      height=sub_sub_element.get('height')))

                                program_ratings.append(XMLTVRating(system=rating_system,
                                                                   value=rating_value,
                                                                   icons=rating_icons))
                            elif sub_element.tag == 'star-rating':
                                star_rating_system = sub_element.get('system')
                                star_rating_value = None
                                star_rating_icons = []

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'value':
                                        star_rating_value = XMLTVValue(text=sub_sub_element.text)
                                    elif sub_sub_element.tag == 'icon':
                                        star_rating_icons.append(XMLTVIcon(source=sub_sub_element.get('src'),
                                                                           width=sub_sub_element.get('width'),
                                                                           height=sub_sub_element.get('height')))

                                program_star_ratings.append(XMLTVStarRating(system=star_rating_system,
                                                                            value=star_rating_value,
                                                                            icons=star_rating_icons))
                            elif sub_element.tag == 'review':
                                program_reviews.append(XMLTVReview(type_=sub_element.get('type'),
                                                                   source=sub_element.get('source'),
                                                                   reviewer=sub_element.get('reviewer'),
                                                                   language=sub_element.get('lang'),
                                                                   text=sub_element.text))

                        channel = parsed_channel_xmltv_id_to_channel[program_channel_xmltv_id]
                        program = XMLTVProgram(provider=provider_map_class.constants_class().PROVIDER_NAME,
                                               start=program_start,
                                               stop=program_stop,
                                               pdc_start=program_pdc_start,
                                               vps_start=program_vps_start,
                                               show_view=program_show_view,
                                               video_plus=program_video_plus,
                                               channel_xmltv_id=channel.xmltv_id,
                                               clump_index=program_clump_index,
                                               titles=program_titles,
                                               sub_titles=program_sub_titles,
                                               descriptions=program_descriptions,
                                               credits_=program_credits,
                                               date=program_date,
                                               categories=program_categories,
                                               keywords=program_keywords,
                                               language=program_language,
                                               original_language=program_original_language,
                                               length=program_length,
                                               icons=program_icons,
                                               urls=program_urls,
                                               countries=program_countries,
                                               episode_numbers=program_episode_numbers,
                                               video=program_video,
                                               audio=program_audio,
                                               previously_shown=program_previously_shown,
                                               premiere=program_premiere,
                                               last_chance=program_last_chance,
                                               new=program_new,
                                               subtitles=program_subtitles,
                                               ratings=program_ratings,
                                               star_ratings=program_star_ratings,
                                               reviews=program_reviews)

                        db_session.add(provider_map_class.program_class()(
                            id_='{0}'.format(uuid.uuid4()),
                            start=program.start,
                            stop=program.stop,
                            channel_xmltv_id=channel.xmltv_id,
                            channel_number=channel.number,
                            pickle=pickle.dumps(program, protocol=pickle.HIGHEST_PROTOCOL),
                            complete_xmltv=program.format(minimal_xmltv=False),
                            minimal_xmltv=program.format()))
                        number_of_objects_added_to_db_session += 1

                        element.clear()
                        tv_element.clear()
                elif event == 'start':
                    if element.tag == 'tv':
                        tv_element = element

                if number_of_objects_added_to_db_session and number_of_objects_added_to_db_session % 1000 == 0:
                    db_session.flush()

            db_session.flush()

            logger.debug('Processed external XML XMLTV')
        except Exception:
            logger.error('Failed to process external XML XMLTV')

            raise

    @classmethod
    def _refresh_epg(cls, provider_name):
        logger.debug('{0} EPG refresh timer triggered'.format(provider_name))

        try:
            kwargs = {}

            if cls._channel_group_map_lock is not None:
                with cls._channel_group_map_lock.reader_lock:
                    kwargs['channel_group_map'] = copy.deepcopy(cls._channel_group_map)
            if cls._channel_name_map_lock is not None:
                with cls._channel_name_map_lock.reader_lock:
                    kwargs['channel_name_map'] = copy.deepcopy(cls._channel_name_map)
            if cls._do_use_provider_icons_lock is not None:
                with cls._do_use_provider_icons_lock.reader_lock:
                    kwargs['do_use_provider_icons'] = cls._do_use_provider_icons
            if cls._ignored_channels_lock is not None:
                with cls._ignored_channels_lock.reader_lock:
                    kwargs['ignored_channels'] = copy.deepcopy(cls._ignored_channels)
            if cls._ignored_m3u8_groups_lock is not None:
                with cls._ignored_m3u8_groups_lock.reader_lock:
                    kwargs['ignored_m3u8_groups'] = copy.deepcopy(cls._ignored_m3u8_groups)
            if cls._m3u8_group_map_lock is not None:
                with cls._m3u8_group_map_lock.reader_lock:
                    kwargs['m3u8_group_map'] = copy.deepcopy(cls._m3u8_group_map)

            cls._update_epg(**kwargs)
        except Exception:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

    @classmethod
    def _request_external_epg_xml(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        url = '{0}'.format(Configuration.get_configuration_parameter(
            '{0}_EPG_URL'.format(provider_map_class.constants_class().PROVIDER_NAME.upper())))

        logger.debug('Downloading external XML EPG\n'
                     'URL => {0}'.format(url))

        requests_session = requests.Session()
        response = Utility.make_http_request(requests_session.get, url, headers=requests_session.headers, stream=True)

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _start_refresh_epg_timer(cls, interval):
        if interval:
            logger.debug('Started {0} EPG refresh timer\n'
                         'Interval => {1} seconds'.format(cls.__name__[:-3], interval))

        cls._refresh_epg_timer = Timer(interval,
                                       cls._refresh_epg,
                                       [ProvidersController.get_provider_map_class(
                                           cls._provider_name).database_access_class().__name__])
        cls._refresh_epg_timer.daemon = True
        cls._refresh_epg_timer.start()

    @classmethod
    @abstractmethod
    def _terminate(cls, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def _update_epg(cls, **kwargs):
        cls._cancel_refresh_epg_timer()

    @classmethod
    def generate_xmltv(cls,
                       is_server_secure,
                       authorization_required,
                       client_ip_address,
                       number_of_days,
                       style):
        current_date_time_in_utc = datetime.now(pytz.utc)

        yield '<?xml version="1.0" encoding="utf-8"?>\n<tv date="{0}" generator-info-name="IPTVProxy {1}">\n'.format(
            current_date_time_in_utc.strftime('%Y%m%d%H%M%S %z'),
            VERSION)

        client_ip_address_type = Utility.determine_ip_address_type(client_ip_address)
        server_password = Configuration.get_configuration_parameter('SERVER_PASSWORD')
        server_hostname = Configuration.get_configuration_parameter(
            'SERVER_HOSTNAME_{0}'.format(client_ip_address_type.value))
        server_port = Configuration.get_configuration_parameter(
            'SERVER_HTTP{0}_PORT'.format('S' if is_server_secure
                                         else ''))

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                # region channel elements
                if style.capitalize() == EPGStyle.COMPLETE.value:
                    query_channels_xmltv = provider_map_class.database_access_class().query_channels_complete_xmltv
                else:
                    query_channels_xmltv = provider_map_class.database_access_class().query_channels_minimal_xmltv

                for channel_row in query_channels_xmltv(db_session):
                    yield channel_row.xmltv.format('s' if is_server_secure
                                                   else '',
                                                   server_hostname,
                                                   server_port,
                                                   '?http_token={0}'.format(server_password) if authorization_required
                                                   else '')
                # endregion

                # region programme elements
                cutoff_date_time_in_local = datetime.now(tzlocal.get_localzone()).replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0) + timedelta(days=int(number_of_days) + 1)
                cutoff_date_time_in_utc = cutoff_date_time_in_local.astimezone(pytz.utc)

                if style.capitalize() == EPGStyle.COMPLETE.value:
                    query_programs_xmltv = provider_map_class.database_access_class().query_programs_complete_xmltv
                else:
                    query_programs_xmltv = provider_map_class.database_access_class().query_programs_minimal_xmltv

                for channel_row in query_programs_xmltv(db_session, cutoff_date_time_in_utc):
                    yield channel_row.xmltv
                # endregion
            finally:
                db_session.close()

        yield '</tv>\n'

    @classmethod
    def get_channel_name(cls, channel_number):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                channel_row = provider_map_class.database_access_class().query_channel_name_by_channel_number(
                    db_session,
                    channel_number)

                if channel_row is not None:
                    channel_name = channel_row.name
                else:
                    channel_name = 'Channel {0:02}'.format(int(channel_number))

                return channel_name
            finally:
                db_session.close()

    @classmethod
    def get_channel_numbers_range(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                channel_row = provider_map_class.database_access_class().query_minimum_maximum_channel_numbers(
                    db_session)
            finally:
                db_session.close()

        return (channel_row.minimum_channel_number, channel_row.maximum_channel_number)

    @classmethod
    def get_m3u8_groups(cls):
        m3u8_groups = []

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                for channel_row in provider_map_class.database_access_class().query_channels_m3u8_groups(db_session):
                    m3u8_groups.append(channel_row.m3u8_group)
            finally:
                db_session.close()

        return m3u8_groups

    @classmethod
    def initialize(cls, **kwargs):
        try:
            cls._initialize_class_variables()

            cls._initialize(**kwargs)
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()

    @classmethod
    def is_attribute_supported(cls, attribute_name):
        if getattr(cls, '{0}_lock'.format(attribute_name)) is not None:
            return True

        return False

    @classmethod
    def is_channel_number_in_epg(cls, channel_number):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        with provider_map_class.database_class().get_access_lock().shared_lock:
            db_session = provider_map_class.database_class().create_session()

            try:
                channel_row = provider_map_class.database_access_class().query_channel_name_by_channel_number(
                    db_session,
                    channel_number)

                if channel_row is not None:
                    return True
                else:
                    return False
            finally:
                db_session.close()

    @classmethod
    def set_channel_group_map(cls, channel_group_map):
        with cls._channel_group_map_lock.writer_lock:
            cls._channel_group_map = channel_group_map

    @classmethod
    def set_channel_name_map(cls, channel_name_map):
        with cls._channel_name_map_lock.writer_lock:
            cls._channel_name_map = channel_name_map

    @classmethod
    def set_do_use_provider_icons(cls, do_use_provider_icons):
        with cls._do_use_provider_icons_lock.writer_lock:
            cls._do_use_provider_icons = do_use_provider_icons

    @classmethod
    def set_ignored_channels(cls, ignored_channels):
        with cls._ignored_channels_lock.writer_lock:
            cls._ignored_channels = ignored_channels

    @classmethod
    def set_ignored_m3u8_groups(cls, ignored_m3u8_groups):
        with cls._ignored_m3u8_groups_lock.writer_lock:
            cls._ignored_m3u8_groups = ignored_m3u8_groups

    @classmethod
    def set_m3u8_group_map(cls, m3u8_group_map):
        with cls._m3u8_group_map_lock.writer_lock:
            cls._m3u8_group_map = m3u8_group_map

    @classmethod
    def set_update_times(cls, epg_update_times):
        with cls._update_times_lock.writer_lock:
            cls._update_times = epg_update_times

    @classmethod
    def terminate(cls, **kwargs):
        try:
            cls._cancel_refresh_epg_timer()

            cls._terminate(**kwargs)
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()


class XStreamCodesProviderEPG(ProviderEPG):
    __slots__ = []

    @classmethod
    def _do_ignore_channel(cls, channel, channel_group_map, ignored_channels, ignored_m3u8_groups):
        for ignored_channels_regular_expression in ignored_channels['name']:
            for display_name in channel.display_names:
                if re.search(ignored_channels_regular_expression, display_name.text):
                    return True

        if channel.number in ignored_channels['number']:
            return True

        for channel_group_map_regular_expression in channel_group_map['name']:
            for display_name in channel.display_names:
                if re.search(channel_group_map_regular_expression, display_name.text):
                    return False

        for channel_group_name in sorted(channel_group_map['number']):
            if channel.number in channel_group_map['number'][channel_group_name]:
                return False

        for ignored_m3u8_group_regular_expression in ignored_m3u8_groups:
            if re.search(ignored_m3u8_group_regular_expression, channel.m3u8_group):
                return True

    @classmethod
    def _parse_categories_json(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))

        categories_json_stream = cls._request_epg_json('categories_{0}.json'.format(username),
                                                       'get_live_categories')

        categories_map = {}

        logger.debug('Processing {0} categories\n'
                     'File name => categories_{1}.json'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                               username))

        category_id = None

        try:
            ijson_parser = ijson.parse(categories_json_stream)

            for (prefix, event, value) in ijson_parser:
                if (prefix, event) == ('item.category_id', 'string'):
                    category_id = value
                elif (prefix, event) == ('item.category_name', 'string'):
                    categories_map[category_id] = value
                elif (prefix, event) == ('item', 'end_map'):
                    category_id = None

            logger.debug(
                'Processed {0} categories\n'
                'File name => categories_{1}.json'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                          username))
        except Exception:
            logger.error(
                'Failed to process {0} categories\n'
                'File name => categories_{1}.json'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                          username))

            raise

        return categories_map

    @classmethod
    def _parse_channels_json(cls,
                             db_session,
                             categories_map,
                             channel_group_map,
                             channel_name_map,
                             do_use_provider_icons,
                             ignored_channels,
                             ignored_m3u8_groups,
                             m3u8_group_map,
                             parsed_channel_xmltv_id_to_channel):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))

        live_streams_stream = cls._request_epg_json('channels_{0}.json'.format(username), 'get_live_streams')

        logger.debug('Processing {0} channels\n'
                     'File name => channels_{1}.json'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                             username))

        number_of_objects_added_to_db_session = 0

        channel_name = None
        channel_number = None
        channel_icon_source = None
        channel_xmltv_id = None
        channel_m3u8_group = None

        try:
            ijson_parser = ijson.parse(live_streams_stream)

            for (prefix, event, value) in ijson_parser:
                if (prefix, event) == ('item.name', 'string'):
                    channel_name = html.unescape(value)
                elif (prefix, event) == ('item.stream_id', 'number'):
                    channel_number = value
                elif (prefix, event) == ('item.stream_icon', 'string'):
                    channel_icon_source = html.unescape(value)
                elif (prefix, event) == ('item.epg_channel_id', 'string'):
                    channel_xmltv_id = html.unescape(value)
                elif (prefix, event) == ('item.category_id', 'string'):
                    channel_m3u8_group = '{0} - {1}'.format(ProvidersController.get_provider_map_class(
                        cls._provider_name).constants_class().PROVIDER_NAME,
                                                            categories_map.get(value, 'UNKNOWN'))
                elif (prefix, event) == ('item', 'end_map'):
                    if channel_m3u8_group is None:
                        channel_m3u8_group = '{0} - UNKNOWN'.format(ProvidersController.get_provider_map_class(
                            cls._provider_name).constants_class().PROVIDER_NAME)

                    channel = XMLTVChannel(provider=provider_map_class.constants_class().PROVIDER_NAME,
                                           m3u8_group=channel_m3u8_group,
                                           xmltv_id=channel_xmltv_id,
                                           number=channel_number,
                                           display_names=[XMLTVDisplayName(language=None,
                                                                           text=channel_name)],
                                           icons=[XMLTVIcon(source=channel_icon_source,
                                                            width=None,
                                                            height=None)] if channel_icon_source
                                           else [],
                                           urls=[])
                    if not cls._do_ignore_channel(channel,
                                                  channel_group_map,
                                                  ignored_channels,
                                                  ignored_m3u8_groups):
                        cls._apply_channel_transformations(channel,
                                                           channel_name_map,
                                                           not do_use_provider_icons,
                                                           channel_group_map,
                                                           m3u8_group_map)

                        if channel_xmltv_id in parsed_channel_xmltv_id_to_channel:
                            parsed_channel_xmltv_id_to_channel[channel_xmltv_id].append(channel)
                        else:
                            parsed_channel_xmltv_id_to_channel[channel_xmltv_id] = [channel]

                        db_session.add(provider_map_class.channel_class()(
                            id_=channel.xmltv_id,
                            m3u8_group=channel.m3u8_group,
                            number=channel.number,
                            name=channel.display_names[0].text,
                            pickle=pickle.dumps(channel, protocol=pickle.HIGHEST_PROTOCOL),
                            complete_xmltv=channel.format(minimal_xmltv=False),
                            minimal_xmltv=channel.format()))
                        number_of_objects_added_to_db_session += 1

                        if number_of_objects_added_to_db_session and number_of_objects_added_to_db_session % 1000 == 0:
                            db_session.flush()

                    channel_name = None
                    channel_number = None
                    channel_icon_source = None
                    channel_xmltv_id = None
                    channel_m3u8_group = None

            db_session.flush()

            logger.debug('Processed {0} channels\n'
                         'File name => channels_{1}.json'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                                 username))
        except Exception:
            logger.error('Failed to process {0} channels\n'
                         'File name => channels_{1}.json'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                                 username))

            raise

    @classmethod
    def _parse_epg_json(cls,
                        db_session,
                        channel_group_map,
                        channel_name_map,
                        do_use_provider_icons,
                        ignored_channels,
                        ignored_m3u8_groups,
                        m3u8_group_map,
                        parsed_channel_xmltv_id_to_channel):
        categories_map = cls._parse_categories_json()

        cls._parse_channels_json(db_session,
                                 categories_map,
                                 channel_group_map,
                                 channel_name_map,
                                 do_use_provider_icons,
                                 ignored_channels,
                                 ignored_m3u8_groups,
                                 m3u8_group_map,
                                 parsed_channel_xmltv_id_to_channel)

    @classmethod
    def _parse_epg_xml(cls, db_session, parsed_channel_xmltv_id_to_channel):
        epg_xml_stream = cls._request_epg_xml()

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))

        logger.debug('Processing {0} XML EPG\n'
                     'File name => xmltv_{1}.xml'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                         username))

        number_of_objects_added_to_db_session = 0

        tv_element = None

        try:
            for (event, element) in etree.iterparse(epg_xml_stream,
                                                    events=('start', 'end'),
                                                    recover=True,
                                                    tag=('channel', 'programme', 'tv')):
                if event == 'end':
                    if element.tag == 'channel':
                        element.clear()
                        tv_element.clear()
                    elif element.tag == 'programme':
                        program_start = datetime.strptime(element.get('start'), '%Y%m%d%H%M%S %z').astimezone(
                            pytz.utc)
                        program_stop = datetime.strptime(element.get('stop'), '%Y%m%d%H%M%S %z').astimezone(
                            pytz.utc)
                        program_pdc_start = element.get('pdc-start')
                        program_vps_start = element.get('vps-start')
                        program_show_view = element.get('showview')
                        program_video_plus = element.get('videoplus')
                        program_channel_xmltv_id = element.get('channel')
                        program_clump_index = element.get('clumpidx')
                        program_titles = []
                        program_sub_titles = []
                        program_descriptions = []
                        program_credits = None
                        program_date = None
                        program_categories = []
                        program_keywords = []
                        program_language = None
                        program_original_language = None
                        program_length = None
                        program_icons = []
                        program_urls = []
                        program_countries = []
                        program_episode_numbers = []
                        program_video = None
                        program_audio = None
                        program_previously_shown = None
                        program_premiere = None
                        program_last_chance = None
                        program_new = None
                        program_subtitles = []
                        program_ratings = []
                        program_star_ratings = []
                        program_reviews = []

                        for sub_element in list(element):
                            if sub_element.tag == 'title':
                                program_titles.append(XMLTVTitle(language=sub_element.get('lang'),
                                                                 text=sub_element.text))
                            elif sub_element.tag == 'sub-title':
                                program_sub_titles.append(XMLTVSubTitle(language=sub_element.get('lang'),
                                                                        text=sub_element.text))
                            elif sub_element.tag == 'desc':
                                program_descriptions.append(XMLTVDescription(language=sub_element.get('lang'),
                                                                             text=sub_element.text))
                            elif sub_element.tag == 'credits':
                                credits_actors = []
                                credits_adapters = []
                                credits_commentators = []
                                credits_composers = []
                                credits_directors = []
                                credits_editors = []
                                credits_guests = []
                                credits_presenters = []
                                credits_producers = []
                                credits_writers = []

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'actor':
                                        credits_actors.append(XMLTVActor(sub_sub_element.get('role'),
                                                                         sub_sub_element.text))
                                    elif sub_sub_element.tag == 'adapter':
                                        credits_adapters.append(XMLTVAdapter(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'commentator':
                                        credits_commentators.append(XMLTVCommentator(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'composer':
                                        credits_composers.append(XMLTVComposer(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'director':
                                        credits_directors.append(XMLTVDirector(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'editor':
                                        credits_editors.append(XMLTVEditor(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'guest':
                                        credits_guests.append(XMLTVGuest(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'presenter':
                                        credits_presenters.append(XMLTVPresenter(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'producer':
                                        credits_producers.append(XMLTVProducer(sub_sub_element.text))
                                    elif sub_sub_element.tag == 'writer':
                                        credits_writers.append(XMLTVWriter(sub_sub_element.text))

                                program_credits = XMLTVCredits(actors=credits_actors,
                                                               adapters=credits_adapters,
                                                               commentators=credits_commentators,
                                                               composers=credits_composers,
                                                               directors=credits_directors,
                                                               editors=credits_editors,
                                                               guests=credits_guests,
                                                               presenters=credits_presenters,
                                                               producers=credits_producers,
                                                               writers=credits_writers)
                            elif sub_element.tag == 'date':
                                program_date = XMLTVDate(text=sub_element.text)
                            elif sub_element.tag == 'category':
                                program_categories.append(XMLTVCategory(language=sub_element.get('lang'),
                                                                        text=sub_element.text))
                            elif sub_element.tag == 'keyword':
                                program_keywords.append(XMLTVKeyword(language=sub_element.get('lang'),
                                                                     text=sub_element.text))
                            elif sub_element.tag == 'language':
                                program_language = XMLTVLanguage(language=sub_element.get('lang'),
                                                                 text=sub_element.text)
                            elif sub_element.tag == 'orig-language':
                                program_original_language = XMLTVOriginalLanguage(language=sub_element.get('lang'),
                                                                                  text=sub_element.text)
                            elif sub_element.tag == 'length':
                                program_length = XMLTVLength(units=sub_element.get('units'),
                                                             text=sub_element.text)
                            elif sub_element.tag == 'icon':
                                program_icons.append(XMLTVIcon(source=sub_element.get('src'),
                                                               width=sub_element.get('width'),
                                                               height=sub_element.get('height')))
                            elif sub_element.tag == 'url':
                                program_urls.append(XMLTVURL(text=sub_element.text))
                            elif sub_element.tag == 'country':
                                program_countries.append(XMLTVCountry(language=sub_element.get('lang'),
                                                                      text=sub_element.text))
                            elif sub_element.tag == 'episode-num':
                                program_episode_numbers.append(XMLTVEpisodeNumber(system=sub_element.get('system'),
                                                                                  text=sub_element.text))
                            elif sub_element.tag == 'video':
                                video_present = None
                                video_colour = None
                                video_aspect = None
                                video_quality = None

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'present':
                                        video_present = XMLTVPresent(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'colour':
                                        video_colour = XMLTVColour(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'aspect':
                                        video_aspect = XMLTVAspect(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'quality':
                                        video_quality = XMLTVQuality(sub_sub_element.text)

                                if video_present is not None or video_colour is not None or \
                                        video_aspect is not None or video_quality is not None:
                                    program_video = XMLTVVideo(present=video_present,
                                                               colour=video_colour,
                                                               aspect=video_aspect,
                                                               quality=video_quality)
                            elif sub_element.tag == 'audio':
                                audio_present = None
                                audio_stereo = None

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'present':
                                        audio_present = XMLTVPresent(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'stereo':
                                        audio_stereo = XMLTVStereo(sub_sub_element.text)

                                if audio_present is not None or audio_stereo is not None:
                                    program_audio = XMLTVAudio(present=audio_present,
                                                               stereo=audio_stereo)
                            elif sub_element.tag == 'previously-shown':
                                program_previously_shown = XMLTVPreviouslyShown(start=sub_element.get('start'),
                                                                                channel=sub_element.get('channel'))
                            elif sub_element.tag == 'premiere':
                                program_premiere = XMLTVPremiere(language=sub_element.get('lang'),
                                                                 text=sub_element.text)
                            elif sub_element.tag == 'last-chance':
                                program_last_chance = XMLTVLastChance(language=sub_element.get('lang'),
                                                                      text=sub_element.text)
                            elif sub_element.tag == 'new':
                                program_new = XMLTVNew()
                            elif sub_element.tag == 'subtitles':
                                subtitles_type = sub_element.get('type')
                                subtitles_language = None

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'language':
                                        subtitles_language = XMLTVLanguage(language=sub_sub_element.get('lang'),
                                                                           text=sub_sub_element.text)

                                program_subtitles.append(XMLTVSubtitles(type_=subtitles_type,
                                                                        language=subtitles_language))
                            elif sub_element.tag == 'rating':
                                rating_system = sub_element.get('system')
                                rating_value = None
                                rating_icons = []

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'value':
                                        rating_value = XMLTVValue(text=sub_sub_element.text)
                                    elif sub_sub_element.tag == 'icon':
                                        rating_icons.append(XMLTVIcon(source=sub_sub_element.get('src'),
                                                                      width=sub_sub_element.get('width'),
                                                                      height=sub_sub_element.get('height')))

                                program_ratings.append(XMLTVRating(system=rating_system,
                                                                   value=rating_value,
                                                                   icons=rating_icons))
                            elif sub_element.tag == 'star-rating':
                                star_rating_system = sub_element.get('system')
                                star_rating_value = None
                                star_rating_icons = []

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'value':
                                        star_rating_value = XMLTVValue(text=sub_sub_element.text)
                                    elif sub_sub_element.tag == 'icon':
                                        star_rating_icons.append(XMLTVIcon(source=sub_sub_element.get('src'),
                                                                           width=sub_sub_element.get('width'),
                                                                           height=sub_sub_element.get('height')))

                                program_star_ratings.append(XMLTVStarRating(system=star_rating_system,
                                                                            value=star_rating_value,
                                                                            icons=star_rating_icons))
                            elif sub_element.tag == 'review':
                                program_reviews.append(XMLTVReview(type_=sub_element.get('type'),
                                                                   source=sub_element.get('source'),
                                                                   reviewer=sub_element.get('reviewer'),
                                                                   language=sub_element.get('lang'),
                                                                   text=sub_element.text))

                        try:
                            for channel in parsed_channel_xmltv_id_to_channel[program_channel_xmltv_id]:
                                program = XMLTVProgram(provider=provider_map_class.constants_class().PROVIDER_NAME,
                                                       start=program_start,
                                                       stop=program_stop,
                                                       pdc_start=program_pdc_start,
                                                       vps_start=program_vps_start,
                                                       show_view=program_show_view,
                                                       video_plus=program_video_plus,
                                                       channel_xmltv_id=channel.xmltv_id,
                                                       clump_index=program_clump_index,
                                                       titles=program_titles,
                                                       sub_titles=program_sub_titles,
                                                       descriptions=program_descriptions,
                                                       credits_=program_credits,
                                                       date=program_date,
                                                       categories=program_categories,
                                                       keywords=program_keywords,
                                                       language=program_language,
                                                       original_language=program_original_language,
                                                       length=program_length,
                                                       icons=program_icons,
                                                       urls=program_urls,
                                                       countries=program_countries,
                                                       episode_numbers=program_episode_numbers,
                                                       video=program_video,
                                                       audio=program_audio,
                                                       previously_shown=program_previously_shown,
                                                       premiere=program_premiere,
                                                       last_chance=program_last_chance,
                                                       new=program_new,
                                                       subtitles=program_subtitles,
                                                       ratings=program_ratings,
                                                       star_ratings=program_star_ratings,
                                                       reviews=program_reviews)

                                db_session.add(provider_map_class.program_class()(
                                    id_='{0}'.format(uuid.uuid4()),
                                    start=program.start,
                                    stop=program.stop,
                                    channel_xmltv_id=channel.xmltv_id,
                                    channel_number=channel.number,
                                    pickle=pickle.dumps(program, protocol=pickle.HIGHEST_PROTOCOL),
                                    complete_xmltv=program.format(minimal_xmltv=False),
                                    minimal_xmltv=program.format()))
                                number_of_objects_added_to_db_session += 1
                        except Exception:
                            pass

                        element.clear()
                        tv_element.clear()
                elif event == 'start':
                    if element.tag == 'tv':
                        tv_element = element

                if number_of_objects_added_to_db_session and number_of_objects_added_to_db_session % 1000 == 0:
                    db_session.flush()

            db_session.flush()

            logger.debug('Processed {0} XML EPG\n'
                         'File name => xmltv_{1}.xml'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                             username))
        except Exception:
            logger.error('Failed to process {0} XML EPG\n'
                         'File name => xmltv_{1}.xml'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                             username))

            raise

    @classmethod
    def _parse_m3u8_playlist(cls,
                             db_session,
                             channel_group_map,
                             channel_name_map,
                             do_use_provider_icons,
                             ignored_channels,
                             ignored_m3u8_groups,
                             m3u8_group_map,
                             parsed_channel_xmltv_id_to_channel):
        m3u8_playlist_stream = cls._request_m3u8_playlist()

        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))

        logger.debug('Processing {0} m3u8 playlist\n'
                     'File name => tv_channels_{1}.m3u'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                               username))

        number_of_objects_added_to_db_session = 0

        channel_xmltv_id = None
        channel_name = None
        channel_icon_source = None
        channel_m3u8_group = None

        try:
            for (m3u8_playlist_line_number, m3u8_playlist_line) in enumerate(m3u8_playlist_stream):
                m3u8_playlist_line = m3u8_playlist_line.decode()

                if m3u8_playlist_line_number:
                    if m3u8_playlist_line_number % 2:
                        m3u8_line_tokens = re.findall(r'(?:"[^"]*"|[^\s"])+', m3u8_playlist_line)

                        for m3u8_line_token in m3u8_line_tokens:
                            if channel_xmltv_id is None and 'tvg-id="' in m3u8_line_token:
                                channel_xmltv_id = m3u8_line_token[len('tvg-id="'):-1]

                                continue

                            if channel_name is None and 'tvg-name="' in m3u8_line_token:
                                channel_name = m3u8_line_token[len('tvg-name="'):-1]

                                continue

                            if channel_icon_source is None and m3u8_line_token.startswith('tvg-logo="http'):
                                channel_icon_source = m3u8_line_token[len('tvg-logo="'):-1]

                                continue

                            if channel_m3u8_group is None and 'group-title="' in m3u8_line_token:
                                channel_m3u8_group = '{0} - {1}'.format(
                                    ProvidersController.get_provider_map_class(
                                        cls._provider_name).constants_class().PROVIDER_NAME,
                                    m3u8_line_token[len('group-title="'):m3u8_line_token.rfind('"')])

                                continue
                    else:
                        match = re.search(r'/(\d*)\.m3u8', m3u8_playlist_line)

                        if match is not None:
                            channel_number = int(match.group(1))

                            channel = XMLTVChannel(provider=provider_map_class.constants_class().PROVIDER_NAME,
                                                   m3u8_group=channel_m3u8_group,
                                                   xmltv_id=channel_xmltv_id,
                                                   number=channel_number,
                                                   display_names=[XMLTVDisplayName(language=None,
                                                                                   text=channel_name)],
                                                   icons=[XMLTVIcon(source=channel_icon_source,
                                                                    width=None,
                                                                    height=None)] if channel_icon_source
                                                   else [],
                                                   urls=[])
                            if not cls._do_ignore_channel(channel,
                                                          channel_group_map,
                                                          ignored_channels,
                                                          ignored_m3u8_groups):
                                cls._apply_channel_transformations(channel,
                                                                   channel_name_map,
                                                                   not do_use_provider_icons,
                                                                   channel_group_map,
                                                                   m3u8_group_map)

                                if channel_xmltv_id in parsed_channel_xmltv_id_to_channel:
                                    parsed_channel_xmltv_id_to_channel[channel_xmltv_id].append(channel)
                                else:
                                    parsed_channel_xmltv_id_to_channel[channel_xmltv_id] = [channel]

                                db_session.add(provider_map_class.channel_class()(
                                    id_=channel.xmltv_id,
                                    m3u8_group=channel.m3u8_group,
                                    number=channel.number,
                                    name=channel.display_names[0].text,
                                    pickle=pickle.dumps(channel, protocol=pickle.HIGHEST_PROTOCOL),
                                    complete_xmltv=channel.format(minimal_xmltv=False),
                                    minimal_xmltv=channel.format()))
                                number_of_objects_added_to_db_session += 1

                                if number_of_objects_added_to_db_session and \
                                        number_of_objects_added_to_db_session % 1000 == 0:
                                    db_session.flush()

                        channel_xmltv_id = None
                        channel_name = None
                        channel_icon_source = None
                        channel_m3u8_group = None

            db_session.flush()

            logger.debug('Processed {0} m3u8 playlist\n'
                         'File name => tv_channels_{1}.m3u'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                                   username))
        except Exception:
            logger.error('Failed to process {0} m3u8 playlist\n'
                         'File name => tv_channels_{1}.m3u'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                                   username))

            raise

    @classmethod
    def _request_epg_json(cls, epg_json_file_name, action):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('{0}_PASSWORD'.format(cls._provider_name.upper()))).decode()

        url = '{0}player_api.php'.format(provider_map_class.constants_class().BASE_URL)

        logger.debug('Downloading {0} {1}\n'
                     'URL => {2}\n'
                     '  Parameters\n'
                     '    username => {3}\n'
                     '    password => {4}\n'
                     '    action   => {5}'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                  epg_json_file_name,
                                                  url,
                                                  username,
                                                  '\u2022' * len(password),
                                                  action))

        requests_session = requests.Session()
        response = Utility.make_http_request(requests_session.get,
                                             url,
                                             params={
                                                 'username': username,
                                                 'password': password,
                                                 'action': action
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict(),
                                             stream=True)

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _request_epg_xml(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('{0}_PASSWORD'.format(cls._provider_name.upper()))).decode()

        url = '{0}xmltv.php'.format(provider_map_class.constants_class().BASE_URL)

        logger.debug(
            'Downloading {0} xmltv_{1}.xml\n'
            'URL => {1}\n'
            '  Parameters\n'
            '    username => {1}\n'
            '    password => {2}'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                         username,
                                         url,
                                         '\u2022' * len(password)))

        requests_session = requests.Session()
        response = Utility.make_http_request(requests_session.get,
                                             url,
                                             params={
                                                 'username': username,
                                                 'password': password
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict(),
                                             stream=True)

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _request_m3u8_playlist(cls):
        provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

        username = Configuration.get_configuration_parameter('{0}_USERNAME'.format(cls._provider_name.upper()))
        password = SecurityManager.decrypt_password(
            Configuration.get_configuration_parameter('{0}_PASSWORD'.format(cls._provider_name.upper()))).decode()

        url = '{0}get.php'.format(provider_map_class.constants_class().BASE_URL)

        logger.debug('Downloading {0} tv_channels_{1}.m3u\n'
                     'URL => {2}\n'
                     '  Parameters\n'
                     '    username => {1}\n'
                     '    password => {3}\n'
                     '    type     => m3u_plus\n'
                     '    output   => hls'.format(provider_map_class.constants_class().PROVIDER_NAME,
                                                  username,
                                                  url,
                                                  '\u2022' * len(password)))

        requests_session = requests.Session()
        response = Utility.make_http_request(requests_session.get,
                                             url,
                                             params={
                                                 'username': username,
                                                 'password': password,
                                                 'type': 'm3u_plus',
                                                 'output': 'hls'
                                             },
                                             headers=requests_session.headers,
                                             cookies=requests_session.cookies.get_dict(),
                                             stream=True)

        if response.status_code == requests.codes.OK:
            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw
        else:
            logger.error(Utility.assemble_response_from_log_message(response))

            response.raise_for_status()

    @classmethod
    def _terminate(cls, **kwargs):
        pass

    @classmethod
    def _update_epg(cls, **kwargs):
        with cls._lock:
            super()._update_epg()

            provider_map_class = ProvidersController.get_provider_map_class(cls._provider_name)

            channel_group_map = kwargs['channel_group_map']
            channel_name_map = kwargs['channel_name_map']
            do_use_provider_icons = kwargs['do_use_provider_icons']
            ignored_channels = kwargs['ignored_channels']
            ignored_m3u8_groups = kwargs['ignored_m3u8_groups']
            m3u8_group_map = kwargs['m3u8_group_map']

            was_exception_raised = False

            provider_map_class.database_class().initialize_temporary()

            db_session = provider_map_class.database_class().create_temporary_session()

            try:
                if Configuration.get_configuration_parameter('{0}_EPG_SOURCE'.format(cls._provider_name.upper())) == \
                        provider_map_class.epg_source_enum().OTHER.value:
                    cls._parse_external_epg_xml(db_session,
                                                channel_name_map=channel_name_map,
                                                do_use_provider_icons=do_use_provider_icons)
                elif Configuration.get_configuration_parameter('{0}_EPG_SOURCE'.format(cls._provider_name.upper())) == \
                        provider_map_class.epg_source_enum().PROVIDER.value:
                    parsed_channel_xmltv_id_to_channel = {}

                    cls._parse_epg_json(db_session,
                                        channel_group_map,
                                        channel_name_map,
                                        do_use_provider_icons,
                                        ignored_channels,
                                        ignored_m3u8_groups,
                                        m3u8_group_map,
                                        parsed_channel_xmltv_id_to_channel)
                    cls._parse_epg_xml(db_session, parsed_channel_xmltv_id_to_channel)

                db_session.add(provider_map_class.setting_class()('epg_settings_md5',
                                                                  cls._calculate_epg_settings_md5(**kwargs)))
                db_session.add(provider_map_class.setting_class()('last_epg_refresh_date_time_in_utc',
                                                                  datetime.strftime(datetime.now(pytz.utc),
                                                                                    '%Y-%m-%d %H:%M:%S%z')))

                db_session.commit()
            except Exception:
                was_exception_raised = True

                db_session.rollback()

                raise
            finally:
                db_session.close()

                cls._initialize_refresh_epg_timer(do_set_timer_for_retry=was_exception_raised)

                if not was_exception_raised:
                    try:
                        provider_map_class.database_class().migrate()
                    except Exception:
                        cls._initialize_refresh_epg_timer(do_set_timer_for_retry=True)

                        raise
