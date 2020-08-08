import html
import logging
import pickle
import uuid
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from threading import RLock

import ijson
import pytz
import requests
from lxml import etree
from rwlock import RWLock

from iptv_proxy.configuration import Configuration
from iptv_proxy.providers.iptv_provider.epg import ProviderEPG
from iptv_proxy.providers.smoothstreams.constants import SmoothStreamsConstants
from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsChannel
from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsProgram
from iptv_proxy.providers.smoothstreams.data_model import SmoothStreamsSetting
from iptv_proxy.providers.smoothstreams.db import SmoothStreamsDatabase
from iptv_proxy.providers.smoothstreams.enums import SmoothStreamsEPGSource
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


class SmoothStreamsEPG(ProviderEPG):
    __slots__ = []

    _channel_name_map = OrderedDict()
    _channel_name_map_lock = RWLock()
    _do_use_provider_icons = False
    _do_use_provider_icons_lock = RWLock()
    _lock = RLock()
    _provider_name = SmoothStreamsConstants.PROVIDER_NAME.lower()
    _refresh_epg_timer = None
    _update_times = ['06:00:00']
    _update_times_lock = RWLock()

    @classmethod
    def _parse_fog_channels_json(
        cls,
        db_session,
        channel_name_map,
        do_use_provider_icons,
        parsed_channel_xmltv_id_to_channel,
    ):
        epg_json_stream = cls._request_fog_channels_json()

        logger.debug(
            'Processing Fog JSON channels\nFile name => %s',
            SmoothStreamsConstants.FOG_CHANNELS_JSON_FILE_NAME,
        )

        key = None

        channel_number = None
        channel_name = None
        channel_xmltv_id = None
        channel_icon_source = None

        try:
            ijson_parser = ijson.parse(epg_json_stream)

            for (prefix, event, value) in ijson_parser:
                if prefix.isdigit() and (event, value) == ('start_map', None):
                    key = prefix

                    channel_number = None
                    channel_name = None
                    channel_xmltv_id = None
                    channel_icon_source = None
                elif (prefix, event) == ('{0}.channum'.format(key), 'string'):
                    channel_number = int(value.strip())
                elif (prefix, event) == ('{0}.channame'.format(key), 'string'):
                    channel_name = html.unescape(value.strip())
                elif (prefix, event) == ('{0}.xmltvid'.format(key), 'string'):
                    channel_xmltv_id = html.unescape(value.strip())
                elif (prefix, event) == ('{0}.icon'.format(key), 'string'):
                    channel_icon_source = value.strip()
                elif (prefix, event) == (key, 'end_map'):
                    channel = XMLTVChannel(
                        provider='SmoothStreams',
                        m3u8_group='SmoothStreams',
                        xmltv_id=channel_xmltv_id,
                        number=channel_number,
                        display_names=[
                            XMLTVDisplayName(language=None, text=channel_name)
                        ],
                        icons=[
                            XMLTVIcon(
                                source=channel_icon_source, width=None, height=None
                            )
                        ],
                        urls=[],
                    )
                    cls._apply_channel_transformations(
                        channel, channel_name_map, not do_use_provider_icons
                    )

                    parsed_channel_xmltv_id_to_channel[channel_xmltv_id] = channel

                    db_session.add(
                        SmoothStreamsChannel(
                            id_=channel.xmltv_id,
                            m3u8_group='SmoothStreams',
                            number=channel.number,
                            name=channel.display_names[0].text,
                            pickle=pickle.dumps(
                                channel, protocol=pickle.HIGHEST_PROTOCOL
                            ),
                            complete_xmltv=channel.format(minimal_xmltv=False),
                            minimal_xmltv=channel.format(),
                        )
                    )

            db_session.flush()

            logger.debug(
                'Processed Fog JSON channels\nFile name => %s',
                SmoothStreamsConstants.FOG_CHANNELS_JSON_FILE_NAME,
            )
        except Exception:
            logger.error(
                'Failed to process Fog JSON channels\nFile name => %s',
                SmoothStreamsConstants.FOG_CHANNELS_JSON_FILE_NAME,
            )

            raise

    @classmethod
    def _parse_fog_epg_xml(cls, db_session, parsed_channel_xmltv_id_to_channel):
        epg_xml_stream = cls._request_fog_epg_xml()

        logger.debug(
            'Processing Fog XML EPG\nFile name => %s',
            SmoothStreamsConstants.FOG_EPG_XML_FILE_NAME,
        )

        number_of_objects_added_to_db_session = 0

        tv_element = None
        tv_date = None

        try:
            for (event, element) in etree.iterparse(
                epg_xml_stream,
                events=('start', 'end'),
                tag=('channel', 'programme', 'tv'),
            ):
                if event == 'end':
                    if element.tag == 'channel':
                        element.clear()
                        tv_element.clear()
                    elif element.tag == 'programme':
                        program_start = datetime.strptime(
                            element.get('start'), '%Y%m%d%H%M%S %z'
                        ).astimezone(pytz.utc)
                        program_stop = datetime.strptime(
                            element.get('stop'), '%Y%m%d%H%M%S %z'
                        ).astimezone(pytz.utc)
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
                                program_titles.append(
                                    XMLTVTitle(
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )
                            elif sub_element.tag == 'sub-title':
                                program_sub_titles.append(
                                    XMLTVSubTitle(
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )
                            elif sub_element.tag == 'desc':
                                program_descriptions.append(
                                    XMLTVDescription(
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )
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
                                        credits_actors.append(
                                            XMLTVActor(
                                                sub_sub_element.get('role'),
                                                sub_sub_element.text,
                                            )
                                        )
                                    elif sub_sub_element.tag == 'adapter':
                                        credits_adapters.append(
                                            XMLTVAdapter(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'commentator':
                                        credits_commentators.append(
                                            XMLTVCommentator(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'composer':
                                        credits_composers.append(
                                            XMLTVComposer(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'director':
                                        credits_directors.append(
                                            XMLTVDirector(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'editor':
                                        credits_editors.append(
                                            XMLTVEditor(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'guest':
                                        credits_guests.append(
                                            XMLTVGuest(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'presenter':
                                        credits_presenters.append(
                                            XMLTVPresenter(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'producer':
                                        credits_producers.append(
                                            XMLTVProducer(sub_sub_element.text)
                                        )
                                    elif sub_sub_element.tag == 'writer':
                                        credits_writers.append(
                                            XMLTVWriter(sub_sub_element.text)
                                        )

                                program_credits = XMLTVCredits(
                                    actors=credits_actors,
                                    adapters=credits_adapters,
                                    commentators=credits_commentators,
                                    composers=credits_composers,
                                    directors=credits_directors,
                                    editors=credits_editors,
                                    guests=credits_guests,
                                    presenters=credits_presenters,
                                    producers=credits_producers,
                                    writers=credits_writers,
                                )
                            elif sub_element.tag == 'date':
                                program_date = XMLTVDate(text=sub_element.text)
                            elif sub_element.tag == 'category':
                                program_categories.append(
                                    XMLTVCategory(
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )
                            elif sub_element.tag == 'keyword':
                                program_keywords.append(
                                    XMLTVKeyword(
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )
                            elif sub_element.tag == 'language':
                                program_language = XMLTVLanguage(
                                    language=sub_element.get('lang'),
                                    text=sub_element.text,
                                )
                            elif sub_element.tag == 'orig-language':
                                program_original_language = XMLTVOriginalLanguage(
                                    language=sub_element.get('lang'),
                                    text=sub_element.text,
                                )
                            elif sub_element.tag == 'length':
                                program_length = XMLTVLength(
                                    units=sub_element.get('units'),
                                    text=sub_element.text,
                                )
                            elif sub_element.tag == 'icon':
                                program_icons.append(
                                    XMLTVIcon(
                                        source=sub_element.get('src'),
                                        width=sub_element.get('width'),
                                        height=sub_element.get('height'),
                                    )
                                )
                            elif sub_element.tag == 'url':
                                program_urls.append(XMLTVURL(text=sub_element.text))
                            elif sub_element.tag == 'country':
                                program_countries.append(
                                    XMLTVCountry(
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )
                            elif sub_element.tag == 'episode-num':
                                program_episode_numbers.append(
                                    XMLTVEpisodeNumber(
                                        system=sub_element.get('system'),
                                        text=sub_element.text,
                                    )
                                )
                            elif sub_element.tag == 'video':
                                video_present = None
                                video_colour = None
                                video_aspect = None
                                video_quality = None

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'present':
                                        video_present = XMLTVPresent(
                                            sub_sub_element.text
                                        )
                                    elif sub_sub_element.tag == 'colour':
                                        video_colour = XMLTVColour(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'aspect':
                                        video_aspect = XMLTVAspect(sub_sub_element.text)
                                    elif sub_sub_element.tag == 'quality':
                                        video_quality = XMLTVQuality(
                                            sub_sub_element.text
                                        )

                                if (
                                    video_present is not None
                                    or video_colour is not None
                                    or video_aspect is not None
                                    or video_quality is not None
                                ):
                                    program_video = XMLTVVideo(
                                        present=video_present,
                                        colour=video_colour,
                                        aspect=video_aspect,
                                        quality=video_quality,
                                    )
                            elif sub_element.tag == 'audio':
                                audio_present = None
                                audio_stereo = None

                                for sub_sub_element in list(sub_element):
                                    if sub_sub_element.tag == 'present':
                                        audio_present = XMLTVPresent(
                                            sub_sub_element.text
                                        )
                                    elif sub_sub_element.tag == 'stereo':
                                        audio_stereo = XMLTVStereo(sub_sub_element.text)

                                if (
                                    audio_present is not None
                                    or audio_stereo is not None
                                ):
                                    program_audio = XMLTVAudio(
                                        present=audio_present, stereo=audio_stereo
                                    )
                            elif sub_element.tag == 'previously-shown':
                                program_previously_shown = XMLTVPreviouslyShown(
                                    start=sub_element.get('start'),
                                    channel=sub_element.get('channel'),
                                )
                            elif sub_element.tag == 'premiere':
                                program_premiere = XMLTVPremiere(
                                    language=sub_element.get('lang'),
                                    text=sub_element.text,
                                )
                            elif sub_element.tag == 'last-chance':
                                program_last_chance = XMLTVLastChance(
                                    language=sub_element.get('lang'),
                                    text=sub_element.text,
                                )
                            elif sub_element.tag == 'new':
                                program_new = XMLTVNew()
                            elif sub_element.tag == 'subtitles':
                                subtitles_type = sub_element.get('type')
                                subtitles_language = None

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'language':
                                        subtitles_language = XMLTVLanguage(
                                            language=sub_sub_element.get('lang'),
                                            text=sub_sub_element.text,
                                        )

                                program_subtitles.append(
                                    XMLTVSubtitles(
                                        type_=subtitles_type,
                                        language=subtitles_language,
                                    )
                                )
                            elif sub_element.tag == 'rating':
                                rating_system = sub_element.get('system')
                                rating_value = None
                                rating_icons = []

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'value':
                                        rating_value = XMLTVValue(
                                            text=sub_sub_element.text
                                        )
                                    elif sub_sub_element.tag == 'icon':
                                        rating_icons.append(
                                            XMLTVIcon(
                                                source=sub_sub_element.get('src'),
                                                width=sub_sub_element.get('width'),
                                                height=sub_sub_element.get('height'),
                                            )
                                        )

                                program_ratings.append(
                                    XMLTVRating(
                                        system=rating_system,
                                        value=rating_value,
                                        icons=rating_icons,
                                    )
                                )
                            elif sub_element.tag == 'star-rating':
                                star_rating_system = sub_element.get('system')
                                star_rating_value = None
                                star_rating_icons = []

                                for sub_sub_element in sub_element:
                                    if sub_sub_element.tag == 'value':
                                        star_rating_value = XMLTVValue(
                                            text=sub_sub_element.text
                                        )
                                    elif sub_sub_element.tag == 'icon':
                                        star_rating_icons.append(
                                            XMLTVIcon(
                                                source=sub_sub_element.get('src'),
                                                width=sub_sub_element.get('width'),
                                                height=sub_sub_element.get('height'),
                                            )
                                        )

                                program_star_ratings.append(
                                    XMLTVStarRating(
                                        system=star_rating_system,
                                        value=star_rating_value,
                                        icons=star_rating_icons,
                                    )
                                )
                            elif sub_element.tag == 'review':
                                program_reviews.append(
                                    XMLTVReview(
                                        type_=sub_element.get('type'),
                                        source=sub_element.get('source'),
                                        reviewer=sub_element.get('reviewer'),
                                        language=sub_element.get('lang'),
                                        text=sub_element.text,
                                    )
                                )

                        channel = parsed_channel_xmltv_id_to_channel[
                            program_channel_xmltv_id
                        ]
                        program = XMLTVProgram(
                            provider='SmoothStreams',
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
                            reviews=program_reviews,
                        )

                        db_session.add(
                            SmoothStreamsProgram(
                                id_='{0}'.format(uuid.uuid4()),
                                start=program.start,
                                stop=program.stop,
                                channel_xmltv_id=channel.xmltv_id,
                                channel_number=channel.number,
                                pickle=pickle.dumps(
                                    program, protocol=pickle.HIGHEST_PROTOCOL
                                ),
                                complete_xmltv=program.format(minimal_xmltv=False),
                                minimal_xmltv=program.format(),
                            )
                        )
                        number_of_objects_added_to_db_session += 1

                        element.clear()
                        tv_element.clear()
                elif event == 'start':
                    if element.tag == 'tv':
                        tv_element = element

                        tv_date = datetime.strptime(
                            element.get('date'), '%Y%m%d%H%M%S %z'
                        ).replace(tzinfo=pytz.utc)

                if (
                    number_of_objects_added_to_db_session
                    and number_of_objects_added_to_db_session % 1000 == 0
                ):
                    db_session.flush()

            db_session.flush()

            logger.debug(
                'Processed Fog XML EPG\nFile name    => %s\nGenerated on => %s',
                SmoothStreamsConstants.FOG_EPG_XML_FILE_NAME,
                tv_date,
            )
        except Exception:
            logger.error(
                'Failed to process Fog XML EPG\nFile name    => %s',
                SmoothStreamsConstants.FOG_EPG_XML_FILE_NAME,
            )

            raise

    @classmethod
    def _parse_smoothstreams_epg_json(
        cls, db_session, channel_name_map, do_use_provider_icons
    ):
        epg_json_stream = cls._request_smoothstreams_epg_json()

        logger.debug(
            'Processing SmoothStreams JSON EPG\nFile name => %s',
            SmoothStreamsConstants.EPG_FILE_NAME,
        )

        number_of_objects_added_to_db_session = 0

        data_id = None
        events_id = None

        generated_on = None

        channel_number = None
        channel_name = None
        channel_icon_source = None

        programs = []

        program_title = None
        program_description = None
        program_start = None
        program_runtime = None

        try:
            ijson_parser = ijson.parse(epg_json_stream)

            for (prefix, event, value) in ijson_parser:
                if (prefix, event) == ('generated_on', 'string'):
                    generated_on = datetime.fromtimestamp(int(value), pytz.utc)
                elif (prefix, event) == ('data', 'map_key'):
                    data_id = value
                elif (prefix, event) == ('data.{0}.events'.format(data_id), 'map_key'):
                    events_id = value
                elif (prefix, event) == ('data.{0}.number'.format(data_id), 'string'):
                    channel_number = int(value.strip())
                elif (prefix, event) == ('data.{0}.name'.format(data_id), 'string'):
                    channel_name = html.unescape(value.strip())
                elif (prefix, event) == ('data.{0}.img'.format(data_id), 'string'):
                    channel_icon_source = value.strip()
                elif (prefix, event) == (
                    'data.{0}.events.{1}'.format(data_id, events_id),
                    'end_map',
                ):
                    program_stop = program_start + timedelta(minutes=program_runtime)

                    programs.append(
                        XMLTVProgram(
                            provider='SmoothStreams',
                            start=program_start,
                            stop=program_stop,
                            pdc_start=None,
                            vps_start=None,
                            show_view=None,
                            video_plus=None,
                            channel_xmltv_id=None,
                            clump_index=None,
                            titles=[XMLTVTitle(language=None, text=program_title)],
                            sub_titles=[],
                            descriptions=[
                                XMLTVDescription(
                                    language=None, text=program_description
                                )
                            ],
                            credits_=None,
                            date=None,
                            categories=[],
                            keywords=[],
                            language=None,
                            original_language=None,
                            length=None,
                            icons=[],
                            urls=[],
                            countries=[],
                            episode_numbers=[],
                            video=None,
                            audio=None,
                            previously_shown=None,
                            premiere=None,
                            last_chance=None,
                            new=None,
                            subtitles=[],
                            ratings=[],
                            star_ratings=[],
                            reviews=[],
                        )
                    )

                    program_title = None
                    program_description = None
                    program_start = None
                    program_runtime = None
                elif (prefix, event) == (
                    'data.{0}.events.{1}.description'.format(data_id, events_id),
                    'string',
                ):
                    program_description = html.unescape(value)
                elif (prefix, event) == (
                    'data.{0}.events.{1}.name'.format(data_id, events_id),
                    'string',
                ):
                    program_title = html.unescape(value)
                elif (prefix, event) == (
                    'data.{0}.events.{1}.runtime'.format(data_id, events_id),
                    'number',
                ):
                    program_runtime = value
                elif (prefix, event) == (
                    'data.{0}.events.{1}.runtime'.format(data_id, events_id),
                    'string',
                ):
                    program_runtime = int(value)
                elif (prefix, event) == (
                    'data.{0}.events.{1}.time'.format(data_id, events_id),
                    'string',
                ):
                    program_start = datetime.fromtimestamp(int(value), pytz.utc)
                elif (prefix, event) == ('data.{0}'.format(data_id), 'end_map'):
                    channel = XMLTVChannel(
                        provider='SmoothStreams',
                        m3u8_group='SmoothStreams',
                        xmltv_id=None,
                        number=channel_number,
                        display_names=[
                            XMLTVDisplayName(language=None, text=channel_name)
                        ],
                        icons=[
                            XMLTVIcon(
                                source=channel_icon_source, width=None, height=None
                            )
                        ],
                        urls=[],
                    )
                    cls._apply_channel_transformations(
                        channel, channel_name_map, not do_use_provider_icons
                    )

                    db_session.add(
                        SmoothStreamsChannel(
                            id_=channel.xmltv_id,
                            m3u8_group='SmoothStreams',
                            number=channel.number,
                            name=channel.display_names[0].text,
                            pickle=pickle.dumps(
                                channel, protocol=pickle.HIGHEST_PROTOCOL
                            ),
                            complete_xmltv=channel.format(minimal_xmltv=False),
                            minimal_xmltv=channel.format(),
                        )
                    )
                    number_of_objects_added_to_db_session += 1

                    if (
                        number_of_objects_added_to_db_session
                        and number_of_objects_added_to_db_session % 1000 == 0
                    ):
                        db_session.flush()

                    for program in programs:
                        program.channel_xmltv_id = channel.xmltv_id

                        db_session.add(
                            SmoothStreamsProgram(
                                id_='{0}'.format(uuid.uuid4()),
                                start=program.start,
                                stop=program.stop,
                                channel_xmltv_id=channel.xmltv_id,
                                channel_number=channel.number,
                                pickle=pickle.dumps(
                                    program, protocol=pickle.HIGHEST_PROTOCOL
                                ),
                                complete_xmltv=program.format(minimal_xmltv=False),
                                minimal_xmltv=program.format(),
                            )
                        )
                        number_of_objects_added_to_db_session += 1

                        if (
                            number_of_objects_added_to_db_session
                            and number_of_objects_added_to_db_session % 1000 == 0
                        ):
                            db_session.flush()

                    channel_number = None
                    channel_name = None
                    channel_icon_source = None

                    programs = []

            db_session.flush()

            logger.debug(
                'Processed SmoothStreams JSON EPG\n'
                'File name    => %s\n'
                'Generated on => %s',
                SmoothStreamsConstants.EPG_FILE_NAME,
                generated_on,
            )
        except Exception:
            logger.error(
                'Failed to process SmoothStreams JSON EPG\nFile name    => %s',
                SmoothStreamsConstants.EPG_FILE_NAME,
            )

            raise

    @classmethod
    def _request_fog_channels_json(cls):
        url = '{0}{1}'.format(
            SmoothStreamsConstants.FOG_EPG_BASE_URL,
            SmoothStreamsConstants.FOG_CHANNELS_JSON_FILE_NAME,
        )

        logger.debug(
            'Downloading %s\nURL => %s',
            SmoothStreamsConstants.FOG_CHANNELS_JSON_FILE_NAME,
            url,
        )

        requests_session = requests.Session()
        response = Utility.make_http_request(
            requests_session.get, url, headers=requests_session.headers, stream=True
        )

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw

        logger.error(Utility.assemble_response_from_log_message(response))

        response.raise_for_status()

    @classmethod
    def _request_fog_epg_xml(cls):
        url = '{0}{1}'.format(
            SmoothStreamsConstants.FOG_EPG_BASE_URL,
            SmoothStreamsConstants.FOG_EPG_XML_FILE_NAME,
        )

        logger.debug(
            'Downloading %s\nURL => %s',
            SmoothStreamsConstants.FOG_EPG_XML_FILE_NAME,
            url,
        )

        requests_session = requests.Session()
        response = Utility.make_http_request(
            requests_session.get, url, headers=requests_session.headers, stream=True
        )

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw

        logger.error(Utility.assemble_response_from_log_message(response))

        response.raise_for_status()

    @classmethod
    def _request_smoothstreams_epg_json(cls):
        url = '{0}{1}'.format(
            SmoothStreamsConstants.EPG_BASE_URL, SmoothStreamsConstants.EPG_FILE_NAME
        )

        logger.debug(
            'Downloading %s\nURL => %s', SmoothStreamsConstants.EPG_FILE_NAME, url
        )

        requests_session = requests.Session()
        response = Utility.make_http_request(
            requests_session.get, url, headers=requests_session.headers, stream=True
        )

        if response.status_code == requests.codes.OK:
            response.raw.decode_content = True

            logger.trace(Utility.assemble_response_from_log_message(response))

            return response.raw

        logger.error(Utility.assemble_response_from_log_message(response))

        response.raise_for_status()

    @classmethod
    def _update_epg(cls, **kwargs):
        with cls._lock:
            super()._update_epg()

            channel_name_map = kwargs['channel_name_map']
            do_use_provider_icons = kwargs['do_use_provider_icons']

            was_exception_raised = False

            SmoothStreamsDatabase.initialize_temporary()

            db_session = SmoothStreamsDatabase.create_temporary_session()

            try:
                if (
                    Configuration.get_configuration_parameter(
                        'SMOOTHSTREAMS_EPG_SOURCE'
                    )
                    == SmoothStreamsEPGSource.FOG.value
                ):
                    parsed_channel_xmltv_id_to_channel = {}

                    cls._parse_fog_channels_json(
                        db_session,
                        channel_name_map,
                        do_use_provider_icons,
                        parsed_channel_xmltv_id_to_channel,
                    )
                    cls._parse_fog_epg_xml(
                        db_session, parsed_channel_xmltv_id_to_channel
                    )
                elif (
                    Configuration.get_configuration_parameter(
                        'SMOOTHSTREAMS_EPG_SOURCE'
                    )
                    == SmoothStreamsEPGSource.OTHER.value
                ):
                    cls._parse_external_epg_xml(
                        db_session,
                        channel_name_map=channel_name_map,
                        do_use_provider_icons=do_use_provider_icons,
                    )
                elif (
                    Configuration.get_configuration_parameter(
                        'SMOOTHSTREAMS_EPG_SOURCE'
                    )
                    == SmoothStreamsEPGSource.PROVIDER.value
                ):
                    cls._parse_smoothstreams_epg_json(
                        db_session, channel_name_map, do_use_provider_icons
                    )

                db_session.add(
                    SmoothStreamsSetting(
                        'epg_settings_md5', cls._calculate_epg_settings_md5(**kwargs)
                    )
                )
                db_session.add(
                    SmoothStreamsSetting(
                        'last_epg_refresh_date_time_in_utc',
                        datetime.strftime(
                            datetime.now(pytz.utc), '%Y-%m-%d %H:%M:%S%z'
                        ),
                    )
                )

                db_session.commit()
            except Exception:
                was_exception_raised = True

                db_session.rollback()

                raise
            finally:
                cls._initialize_refresh_epg_timer(
                    do_set_timer_for_retry=was_exception_raised
                )

                db_session.close()

                if not was_exception_raised:
                    try:
                        SmoothStreamsDatabase.migrate()
                    except Exception:
                        cls._initialize_refresh_epg_timer(do_set_timer_for_retry=True)

                        raise

    @classmethod
    def _terminate(cls, **kwargs):
        pass
