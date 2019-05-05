import logging
from xml.sax import saxutils

logger = logging.getLogger(__name__)


class XMLTVActor(object):
    def __init__(self, role, text):
        self._role = role
        self._text = text

    def format(self):
        return '    <actor{0}>{1}</actor>'.format(
            ' role="{0}"'.format(saxutils.escape(self._role)) if self._role is not None
            else '',
            saxutils.escape(self._text))

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVAdapter(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <adapter>{0}</adapter>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVAspect(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <aspect>{0}</aspect>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVAudio(object):
    def __init__(self, present, stereo):
        self._present = present
        self._stereo = stereo

    def format(self):
        audio_element = ['  <audio>']

        if self._present is not None and self._present.text is not None:
            audio_element.append(self._present.format())

        if self._stereo is not None and self._stereo.text is not None:
            audio_element.append(self._stereo.format())

        audio_element.append('  </audio>')

        return '\n'.join(audio_element)

    @property
    def present(self):
        return self._present

    @present.setter
    def present(self, present):
        self._present = present

    @property
    def stereo(self):
        return self._stereo

    @stereo.setter
    def stereo(self, stereo):
        self._stereo = stereo


class XMLTVCategory(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <category{0}>{1}</category>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVChannel(object):
    def __init__(self, provider, m3u8_group, xmltv_id, number, display_names, icons, urls):
        self._provider = provider
        self._m3u8_group = m3u8_group
        self._xmltv_id = xmltv_id
        self._number = number
        self._display_names = display_names
        self._icons = icons
        self._urls = urls

    def format(self, minimal_xmltv=True):
        channel_element = ['<channel id="{0}">'.format(saxutils.escape(self._xmltv_id))]

        for display_name in self._display_names:
            if display_name.text is not None:
                channel_element.append(display_name.format())

                if minimal_xmltv:
                    break

        for icon in self._icons:
            if icon.source is not None:
                channel_element.append(icon.format())

                if minimal_xmltv:
                    break

        for url in self._urls:
            if url.text is not None:
                channel_element.append(url.format())

                if minimal_xmltv:
                    break

        channel_element.append('</channel>\n')

        return '\n'.join(channel_element)

    @property
    def display_names(self):
        return tuple(self._display_names)

    @display_names.setter
    def display_names(self, display_names):
        self._display_names = display_names

    @property
    def icons(self):
        return tuple(self._icons)

    @icons.setter
    def icons(self, icons):
        self._icons = icons

    @property
    def m3u8_group(self):
        return self._m3u8_group

    @m3u8_group.setter
    def m3u8_group(self, m3u8_group):
        self._m3u8_group = m3u8_group

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, number):
        self._number = number

    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, provider):
        self._provider = provider

    @property
    def urls(self):
        return tuple(self._urls)

    @urls.setter
    def urls(self, urls):
        self._urls = urls

    @property
    def xmltv_id(self):
        return self._xmltv_id

    @xmltv_id.setter
    def xmltv_id(self, xmltv_id):
        self._xmltv_id = xmltv_id


class XMLTVColour(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <colour>{0}</colour>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVCommentator(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <commentator>{0}</commentator>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVComposer(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <composer>{0}</composer>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVCountry(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <country{0}>{1}</country>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @property
    def text(self):
        return self._text


class XMLTVCredits(object):
    def __init__(self, actors, adapters, commentators, composers, directors, editors, guests, presenters, producers,
                 writers):
        self._actors = actors
        self._adapters = adapters
        self._commentators = commentators
        self._composers = composers
        self._directors = directors
        self._editors = editors
        self._guests = guests
        self._presenters = presenters
        self._producers = producers
        self._writers = writers

    def format(self):
        credits_element = ['  <credits>']

        for director in self._directors:
            if director.text is not None:
                credits_element.append(director.format())

        for actor in self._actors:
            if actor.text is not None:
                credits_element.append(actor.format())

        for writer in self._writers:
            if writer.text is not None:
                credits_element.append(writer.format())

        for adapter in self._adapters:
            if adapter.text is not None:
                credits_element.append(adapter.format())

        for producer in self._producers:
            if producer.text is not None:
                credits_element.append(producer.format())

        for composer in self._composers:
            if composer.text is not None:
                credits_element.append(composer.format())

        for editor in self._editors:
            if editor.text is not None:
                credits_element.append(editor.format())

        for presenter in self._presenters:
            if presenter.text is not None:
                credits_element.append(presenter.format())

        for commentator in self._commentators:
            if commentator.text is not None:
                credits_element.append(commentator.format())

        for guest in self._guests:
            if guest.text is not None:
                credits_element.append(guest.format())

        credits_element.append('  </credits>')

        return '\n'.join(credits_element)

    @property
    def actors(self):
        return tuple(self._actors)

    @actors.setter
    def actors(self, actors):
        self._actors = actors

    @property
    def adapters(self):
        return tuple(self._adapters)

    @adapters.setter
    def adapters(self, adapters):
        self._adapters = adapters

    @property
    def commentators(self):
        return tuple(self._commentators)

    @commentators.setter
    def commentators(self, commentators):
        self._commentators = commentators

    @property
    def composers(self):
        return tuple(self._composers)

    @composers.setter
    def composers(self, composers):
        self._composers = composers

    @property
    def directors(self):
        return tuple(self._directors)

    @directors.setter
    def directors(self, directors):
        self._directors = directors

    @property
    def editors(self):
        return tuple(self._editors)

    @editors.setter
    def editors(self, editors):
        self._editors = editors

    @property
    def guests(self):
        return tuple(self._guests)

    @guests.setter
    def guests(self, guests):
        self._guests = guests

    @property
    def presenters(self):
        return tuple(self._presenters)

    @presenters.setter
    def presenters(self, presenters):
        self._presenters = presenters

    @property
    def producers(self):
        return tuple(self._producers)

    @producers.setter
    def producers(self, producers):
        self._producers = producers

    @property
    def writers(self):
        return tuple(self._writers)

    @writers.setter
    def writers(self, writers):
        self._writers = writers


class XMLTVDate(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '  <date>{0}</date>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVDescription(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <desc{0}>{1}</desc>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVDirector(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <director>{0}</director>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVDisplayName(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <display-name{0}>{1}</display-name>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVEditor(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <editor>{0}</editor>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVEpisodeNumber(object):
    def __init__(self, system, text):
        self._system = system
        self._text = text

    def format(self):
        return '  <episode-num{0}>{1}</episode-num>'.format(
            ' system="{0}"'.format(saxutils.escape(self._system)) if self._system is not None
            else '',
            saxutils.escape(self._text))

    @property
    def system(self):
        return self._system

    @system.setter
    def system(self, system):
        self._system = system

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVGuest(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <guest>{0}</guest>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVIcon(object):
    def __init__(self, source, width, height):
        self._source = source
        self._width = width
        self._height = height

    def format(self):
        return '  <icon src="{0}"{1}{2} />'.format(
            saxutils.escape(self._source),
            ' width="{0}"'.format(saxutils.escape(self._width)) if self._width is not None
            else '',
            ' height="{0}"'.format(saxutils.escape(self._height)) if self._height is not None
            else '')

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        self._height = height

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self._source = source

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        self._width = width


class XMLTVKeyword(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <keyword{0}>{1}</keyword>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @property
    def text(self):
        return self._text


class XMLTVLanguage(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <language{0}>{1}</language>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @property
    def text(self):
        return self._text


class XMLTVLastChance(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <last-chance{0}>{1}</last-chance>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @property
    def text(self):
        return self._text


class XMLTVLength(object):
    def __init__(self, units, text):
        self._units = units
        self._text = text

    def format(self):
        return '  <length units="{0}">{1}</length>'.format(saxutils.escape(self._units), saxutils.escape(self._text))

    @property
    def units(self):
        return self._units

    @property
    def text(self):
        return self._text


class XMLTVOriginalLanguage(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <orig-language{0}>{1}</orig-language>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @property
    def text(self):
        return self._text


class XMLTVNew(object):
    def format(self):
        return '  <new />'


class XMLTVPremiere(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <premiere{0}{1}>{2}{3}'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            '' if self._text is not None
            else ' /',
            saxutils.escape(self._text) if self._text is not None
            else '',
            '</premiere>' if self._text is not None
            else '')

    @property
    def language(self):
        return self._language

    @property
    def text(self):
        return self._text


class XMLTVPresent(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <present>{0}</present>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVPresenter(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <presenter>{0}</presenter>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVPreviouslyShown(object):
    def __init__(self, start, channel):
        self._start = start
        self._channel = channel

    def format(self):
        return '  <previously-shown{0}{1} />'.format(
            ' start="{0}"'.format(saxutils.escape(self._start)) if self._start is not None
            else '',
            ' channel="{0}"'.format(saxutils.escape(self._channel)) if self._channel is not None
            else '')

    @property
    def start(self):
        return self._start

    @property
    def channel(self):
        return self._channel


class XMLTVProducer(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <producer>{0}</producer>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVProgram(object):
    def __init__(self, provider, start, stop, pdc_start, vps_start, show_view, video_plus, channel_xmltv_id,
                 clump_index, new, titles, sub_titles, descriptions, credits_, date, categories, keywords, language,
                 original_language, length, icons, urls, countries, episode_numbers, video, audio, previously_shown,
                 premiere, last_chance, subtitles, ratings, star_ratings, reviews):
        self._provider = provider
        self._start = start
        self._stop = stop
        self._pdc_start = pdc_start
        self._vps_start = vps_start
        self._show_view = show_view
        self._video_plus = video_plus
        self._channel_xmltv_id = channel_xmltv_id
        self._clump_index = clump_index
        self._new = new
        self._titles = titles
        self._sub_titles = sub_titles
        self._descriptions = descriptions
        self._credits = credits_
        self._date = date
        self._categories = categories
        self._keywords = keywords
        self._language = language
        self._original_language = original_language
        self._length = length
        self._icons = icons
        self._urls = urls
        self._countries = countries
        self._episode_numbers = episode_numbers
        self._video = video
        self._audio = audio
        self._previously_shown = previously_shown
        self._premiere = premiere
        self._last_chance = last_chance
        self._subtitles = subtitles
        self._ratings = ratings
        self._star_ratings = star_ratings
        self._reviews = reviews

    def format(self, minimal_xmltv=True):
        program_element = ['<programme start="{0}"{1}{2}{3}{4}{5} channel="{6}"{7}>'.format(
            self._start.strftime('%Y%m%d%H%M%S %z'),
            ' stop="{0}"'.format(self._stop.strftime('%Y%m%d%H%M%S %z')) if self._stop is not None
            else '',
            ' pdc-start="{0}"'.format(saxutils.escape(self._pdc_start)) if self._pdc_start is not None
            else '',
            ' vps-start="{0}"'.format(saxutils.escape(self._vps_start)) if self._vps_start is not None
            else '',
            ' showview="{0}"'.format(saxutils.escape(self._show_view)) if self._show_view is not None
            else '',
            ' videoplus="{0}"'.format(saxutils.escape(self._video_plus)) if self._video_plus is not None
            else '',
            saxutils.escape(self._channel_xmltv_id),
            ' clumpidx="{0}"'.format(saxutils.escape(self._clump_index)) if self._clump_index is not None
            else '')]

        if minimal_xmltv:
            if self._sub_titles and self._sub_titles[0].text is not None:
                self._titles[0].text = '{0}: {1}'.format(self._titles[0].text, self._sub_titles[0].text)

            program_element.append(self._titles[0].format())
        else:
            for title in self._titles:
                if title.text is not None:
                    program_element.append(title.format())

            for sub_title in self._sub_titles:
                if sub_title.text is not None:
                    program_element.append(sub_title.format())

        for description in self._descriptions:
            if description.text is not None:
                program_element.append(description.format())

                if minimal_xmltv:
                    break

        if not minimal_xmltv:
            if self._credits is not None:
                program_element.append(self._credits.format())

            if self._date is not None and self._date.text is not None:
                program_element.append(self._date.format())

        for category in self._categories:
            if category.text is not None:
                program_element.append(category.format())

                if minimal_xmltv:
                    break

        if not minimal_xmltv:
            for keyword in self.keywords:
                if keyword.text is not None:
                    program_element.append(keyword.format())

            if self._language is not None and self._language.text is not None:
                program_element.append(self._language.format())

            if self._original_language is not None and self._original_language.text is not None:
                program_element.append(self._original_language.format())

            if self._length is not None and self._length.text is not None:
                program_element.append(self._length.format())

            for icon in self._icons:
                if icon.source is not None:
                    program_element.append(icon.format())

            for url in self._urls:
                if url.text is not None:
                    program_element.append(url.format())

            for country in self._countries:
                if country.text is not None:
                    program_element.append(country.format())

            for episode_number in self._episode_numbers:
                if episode_number.text is not None:
                    program_element.append(episode_number.format())

            if self._video is not None and \
                    ((self._video.present is not None and self._video.present.text is not None) or
                     (self._video.colour is not None and self._video.colour.text is not None) or
                     (self._video.aspect is not None and self._video.aspect.text is not None) or
                     (self._video.quality is not None and self._video.quality.text is not None)):
                program_element.append(self._video.format())

            if self._audio is not None and \
                    ((self._audio.present is not None and self._audio.present.text is not None) or
                     (self._audio.stereo is not None and self._audio.stereo.text is not None)):
                program_element.append(self._audio.format())

            if self._previously_shown is not None:
                program_element.append(self._previously_shown.format())

            if self._premiere is not None:
                program_element.append(self._premiere.format())

            if self._last_chance is not None:
                program_element.append(self._last_chance.format())

            if self._new is not None:
                program_element.append(self._new.format())

            for subtitles in self._subtitles:
                if subtitles.language is not None and subtitles.language.text is not None:
                    program_element.append(subtitles.format())

            for rating in self._ratings:
                if rating.value is not None and rating.value.text is not None:
                    program_element.append(rating.format())

            for star_rating in self._star_ratings:
                if star_rating.value is not None and star_rating.value.text is not None:
                    program_element.append(star_rating.format())

            for review in self._reviews:
                if review.text is not None:
                    program_element.append(review.format())

        program_element.append('</programme>\n')

        return '\n'.join(program_element)

    @property
    def audio(self):
        return self._audio

    @audio.setter
    def audio(self, audio):
        self._audio = audio

    @property
    def channel_xmltv_id(self):
        return self._channel_xmltv_id

    @channel_xmltv_id.setter
    def channel_xmltv_id(self, channel_xmltv_id):
        self._channel_xmltv_id = channel_xmltv_id

    @property
    def categories(self):
        return tuple(self._categories)

    @categories.setter
    def categories(self, categories):
        self._categories = categories

    @property
    def clump_index(self):
        return self._clump_index

    @clump_index.setter
    def clump_index(self, clump_index):
        self._clump_index = clump_index

    @property
    def credits(self):
        return type(self._credits)

    @credits.setter
    def credits(self, credits_):
        self._credits = credits_

    @property
    def countries(self):
        return tuple(self._countries)

    @countries.setter
    def countries(self, countries):
        self._countries = countries

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        self._date = date

    @property
    def descriptions(self):
        return tuple(self._descriptions)

    @descriptions.setter
    def descriptions(self, descriptions):
        self._descriptions = descriptions

    @property
    def episode_numbers(self):
        return tuple(self._episode_numbers)

    @episode_numbers.setter
    def episode_numbers(self, episode_numbers):
        self._episode_numbers = episode_numbers

    @property
    def icons(self):
        return tuple(self._icons)

    @icons.setter
    def icons(self, icons):
        self._icons = icons

    @property
    def keywords(self):
        return tuple(self._keywords)

    @keywords.setter
    def keywords(self, keywords):
        self._keywords = keywords

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def last_chance(self):
        return self._last_chance

    @last_chance.setter
    def last_chance(self, last_chance):
        self._last_chance = last_chance

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, length):
        self._length = length

    @property
    def new(self):
        return self._new

    @new.setter
    def new(self, new):
        self._new = new

    @property
    def original_language(self):
        return self._original_language

    @original_language.setter
    def original_language(self, original_language):
        self._original_language = original_language

    @property
    def pdc_start(self):
        return self._pdc_start

    @pdc_start.setter
    def pdc_start(self, pdc_start):
        self._pdc_start = pdc_start

    @property
    def premiere(self):
        return self._premiere

    @premiere.setter
    def premiere(self, premiere):
        self._premiere = premiere

    @property
    def previously_shown(self):
        return self._previously_shown

    @previously_shown.setter
    def previously_shown(self, previously_shown):
        self._previously_shown = previously_shown

    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, provider):
        self._provider = provider

    @property
    def ratings(self):
        return tuple(self._ratings)

    @ratings.setter
    def ratings(self, ratings):
        self._ratings = ratings

    @property
    def reviews(self):
        return type(self._reviews)

    @reviews.setter
    def reviews(self, reviews):
        self._reviews = reviews

    @property
    def show_view(self):
        return self._show_view

    @show_view.setter
    def show_view(self, show_view):
        self._show_view = show_view

    @property
    def star_ratings(self):
        return type(self._star_ratings)

    @star_ratings.setter
    def star_ratings(self, star_ratings):
        self._star_ratings = star_ratings

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, stop):
        self._stop = stop

    @property
    def sub_titles(self):
        return tuple(self._sub_titles)

    @sub_titles.setter
    def sub_titles(self, sub_titles):
        self._sub_titles = sub_titles

    @property
    def subtitles(self):
        return tuple(self._subtitles)

    @subtitles.setter
    def subtitles(self, subtitles):
        self._subtitles = subtitles

    @property
    def titles(self):
        return tuple(self._titles)

    @titles.setter
    def titles(self, titles):
        self._titles = titles

    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, video):
        self._video = video

    @property
    def video_plus(self):
        return self._video_plus

    @video_plus.setter
    def video_plus(self, video_plus):
        self._video_plus = video_plus

    @property
    def vps_start(self):
        return self._vps_start

    @vps_start.setter
    def vps_start(self, vps_start):
        self._vps_start = vps_start


class XMLTVQuality(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <quality>{0}</quality>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVRating(object):
    def __init__(self, system, value, icons):
        self._system = system
        self._value = value
        self._icons = icons

    def format(self):
        rating_element = [
            '  <rating{0}>'.format(' system="{0}"'.format(saxutils.escape(self._system)) if self._system is not None
                                   else '')]

        if self._value is not None:
            rating_element.append(self._value.format())

        for icon in self._icons:
            if icon.source is not None:
                rating_element.append(icon.format())

        rating_element.append('  </rating>')

        return '\n'.join(rating_element)

    @property
    def icons(self):
        return tuple(self._icons)

    @icons.setter
    def icons(self, icons):
        self._icons = icons

    @property
    def system(self):
        return self._system

    @system.setter
    def system(self, system):
        self._system = system

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class XMLTVReview(object):
    def __init__(self, type_, source, reviewer, language, text):
        self._type = type_,
        self._source = source
        self._reviewer = reviewer
        self._language = language
        self._text = text

    def format(self):
        return '  <review type="{0}"{1}{2}{3}>{4}</review>'.format(
            saxutils.escape(self._type),
            ' source="{0}"'.format(saxutils.escape(self._source)) if self._source is not None
            else '',
            ' reviewer="{0}"'.format(saxutils.escape(self._reviewer)) if self._reviewer is not None
            else '',
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def reviewer(self):
        return self._reviewer

    @reviewer.setter
    def reviewer(self, reviewer):
        self._reviewer = reviewer

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self._source = source

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type_):
        self._type = type_


class XMLTVStarRating(object):
    def __init__(self, system, value, icons):
        self._system = system
        self._value = value
        self._icons = icons

    def format(self):
        star_rating_element = ['  <star-rating{0}>'.format(
            ' system="{0}"'.format(saxutils.escape(self._system)) if self._system is not None
            else '')]

        if self._value is not None:
            star_rating_element.append(self._value.format())

        for icon in self._icons:
            if icon.source is not None:
                star_rating_element.append(icon.format())

        star_rating_element.append('  </star-rating>')

        return '\n'.join(star_rating_element)

    @property
    def icons(self):
        return tuple(self._icons)

    @icons.setter
    def icons(self, icons):
        self._icons = icons

    @property
    def system(self):
        return self._system

    @system.setter
    def system(self, system):
        self._system = system

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class XMLTVStereo(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <stereo>{0}</stereo>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVSubTitle(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <sub-title{0}>{1}</sub-title>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVSubtitles(object):
    def __init__(self, type_, language):
        self._type = type_
        self._language = language

    def format(self):
        return '  <subtitles{0}{1}>{2}{3}'.format(
            ' type="{0}"'.format(saxutils.escape(self._type)) if self._type is not None
            else '',
            '' if self._language is not None
            else ' /',
            self._language.format() if self._language is not None
            else '',
            '</subtitles>' if self._language is not None
            else '')

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def type_(self):
        return self._type

    @type_.setter
    def type_(self, type_):
        self._type = type_


class XMLTVTitle(object):
    def __init__(self, language, text):
        self._language = language
        self._text = text

    def format(self):
        return '  <title{0}>{1}</title>'.format(
            ' lang="{0}"'.format(saxutils.escape(self._language)) if self._language is not None
            else '',
            saxutils.escape(self._text))

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVURL(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '  <url>{0}</url>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVValue(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <value>{0}</value>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text


class XMLTVVideo(object):
    def __init__(self, present, colour, aspect, quality):
        self._present = present
        self._colour = colour
        self._aspect = aspect
        self._quality = quality

    def format(self):
        video_element = ['  <video>']

        if self._present is not None and self._present.text is not None:
            video_element.append(self._present.format())

        if self._colour is not None and self._colour.text is not None:
            video_element.append(self._colour.format())

        if self._aspect is not None and self._aspect.text is not None:
            video_element.append(self._aspect.format())

        if self._quality is not None and self._quality.text is not None:
            video_element.append(self._quality.format())

        video_element.append('  </video>')

        return '\n'.join(video_element)

    @property
    def aspect(self):
        return self._aspect

    @aspect.setter
    def aspect(self, aspect):
        self._aspect = aspect

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, colour):
        self._colour = colour

    @property
    def present(self):
        return self._present

    @present.setter
    def present(self, present):
        self._present = present

    @property
    def quality(self):
        return self._quality

    @quality.setter
    def quality(self, quality):
        self._quality = quality


class XMLTVWriter(object):
    def __init__(self, text):
        self._text = text

    def format(self):
        return '    <writer>{0}</writer>'.format(saxutils.escape(self._text))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
