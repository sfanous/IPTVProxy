import logging
import os
import pickle
import re
import sys
import traceback
import uuid
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from datetime import timedelta
from threading import Timer

import pytz
import requests
import tzlocal
from lxml import etree

from iptv_proxy.configuration import Configuration
from iptv_proxy.constants import CHANNEL_ICONS_DIRECTORY_PATH
from iptv_proxy.constants import VERSION
from iptv_proxy.enums import EPGStyle
from iptv_proxy.providers import ProvidersController
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

    _channel_name_map = None
    _do_use_provider_icons = None
    _lock = None
    _provider_name = None
    _refresh_epg_timer = None

    @classmethod
    def _apply_channel_transformations(cls, channel, channel_name_map, do_use_iptv_proxy_icons):
        channel.xmltv_id = '{0}'.format(uuid.uuid3(uuid.NAMESPACE_OID, '{0} - (1)'.format(channel.number,
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
            for channel_icon_file_name in os.listdir(CHANNEL_ICONS_DIRECTORY_PATH):
                if re.search(r'\A{0}.png\Z|\A{0}_|_{0}_|_{0}.png\Z'.format(channel.number), channel_icon_file_name):
                    break
            else:
                channel_icon_file_name = '0.png'

            channel.icons = [XMLTVIcon(source='{0}{1}{2}'.format('http{0}://{1}:{2}/', channel_icon_file_name, '{3}'),
                                       width=None,
                                       height=None)]

    @classmethod
    def _cancel_refresh_epg_timer(cls):
        if cls._refresh_epg_timer is not None:
            cls._refresh_epg_timer.cancel()
            cls._refresh_epg_timer = None

    @classmethod
    @abstractmethod
    def _do_update_epg(cls):
        pass

    @classmethod
    def _initialize_refresh_epg_timer(cls, db_session, do_set_timer_for_retry=False):
        current_date_time_in_utc = datetime.now(pytz.utc)

        if do_set_timer_for_retry:
            refresh_epg_date_time_in_utc = (current_date_time_in_utc.astimezone(
                tzlocal.get_localzone()).replace(minute=0,
                                                 second=0,
                                                 microsecond=0) + timedelta(hours=1)).astimezone(pytz.utc)

            cls._start_refresh_epg_timer((refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds())
        else:
            setting_row = ProvidersController.get_provider_map_class(
                cls._provider_name).database_access_class().query_setting(db_session,
                                                                          'last_epg_refresh_date_time_in_utc')

            if setting_row is not None:
                last_epg_refresh_date_time_in_utc = datetime.strptime(setting_row.value, '%Y-%m-%d %H:%M:%S%z')

                if cls._refresh_epg_timer is None:
                    refresh_epg_date_time_in_utc = (last_epg_refresh_date_time_in_utc.astimezone(
                        tzlocal.get_localzone()).replace(hour=4,
                                                         minute=0,
                                                         second=0,
                                                         microsecond=0) + timedelta(days=1)).astimezone(pytz.utc)

                    cls._start_refresh_epg_timer(
                        (refresh_epg_date_time_in_utc - current_date_time_in_utc).total_seconds())

    @classmethod
    def _parse_external_epg_xml(cls, db_session):
        epg_xml_stream = cls._request_external_epg_xml()

        logger.debug('Processing external XML EPG')

        parsed_channel_xmltv_id_to_channel = {}
        number_of_objects_added_to_db_session = 0

        tv_element = None

        try:
            for (event, element) in etree.iterparse(epg_xml_stream,
                                                    events=('start', 'end'),
                                                    tag=('channel', 'programme', 'tv')):
                if event == 'end':
                    if element.tag == 'channel':
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

                        channel = XMLTVChannel(provider='SmoothStreams',
                                               m3u8_group='SmoothStreams',
                                               xmltv_id=channel_xmltv_id,
                                               number=channel_number,
                                               display_names=channel_display_names,
                                               icons=channel_icons,
                                               urls=channel_urls)
                        cls._apply_channel_transformations(channel,
                                                           cls._channel_name_map,
                                                           not cls._do_use_provider_icons)

                        parsed_channel_xmltv_id_to_channel[channel_xmltv_id] = channel

                        db_session.add(ProvidersController.get_provider_map_class(cls._provider_name).channel_class()(
                            id_=channel.xmltv_id,
                            m3u8_group='SmoothStreams',
                            number=channel_number,
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
                        program = XMLTVProgram(provider='SmoothStreams',
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

                        db_session.add(ProvidersController.get_provider_map_class(cls._provider_name).program_class()(
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
            logger.debug('Failed to process external XML XMLTV')

            raise

    @classmethod
    def _refresh_epg(cls, provider_name):
        logger.debug('{0} EPG refresh timer triggered'.format(provider_name))

        try:
            cls._update_epg()
        except Exception:
            (type_, value_, traceback_) = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(type_, value_, traceback_)))

    @classmethod
    def _request_external_epg_xml(cls):
        url = '{0}'.format(Configuration.get_configuration_parameter('SMOOTHSTREAMS_EPG_URL'))

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
    def _update_epg(cls):
        pass

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
    @abstractmethod
    def initialize(cls, **kwargs):
        pass

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
    def set_channel_name_map(cls, channel_name_map):
        cls._channel_name_map = channel_name_map

    @classmethod
    def set_do_use_provider_icons(cls, do_use_provider_icons):
        cls._do_use_provider_icons = do_use_provider_icons

    @classmethod
    def terminate(cls, **kwargs):
        try:
            cls._cancel_refresh_epg_timer()
        finally:
            if 'event' in kwargs:
                kwargs['event'].set()
