# -*- coding: utf-8 -*-
# pylint: disable=C0111

from lettuce import world, step
import os
import json
import time
import requests
from common import i_am_registered_for_the_course, section_location, visit_scenario_item
from django.utils.translation import ugettext as _
from django.conf import settings
from cache_toolbox.core import del_cached_content
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT
LANGUAGES = settings.ALL_LANGUAGES


############### ACTIONS ####################

HTML5_SOURCES = [
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.mp4',
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.webm',
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.ogv',
]

HTML5_SOURCES_INCORRECT = [
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.mp99',
]

VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
    'fullscreen': '.add-fullscreen',
    'download_transcript': '.video-tracks > a',
}

VIDEO_MENUS = {
    'language': '.lang .menu',
    'speed': '.speed .menu',
    'download_transcript': '.video-tracks .a11y-menu-list',
}

coursenum = 'test_course'
sequence = {}


class ReuqestHandlerWithSessionId(object):
    def get(self, url):
        """
        Sends a request.
        """
        kwargs = dict()

        session_id = [{i['name']:i['value']} for i in world.browser.cookies.all() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.content = response.content

        return self

    def is_success(self):
        """
        Returns `True` if the response was succeed, otherwise, returns `False`.
        """
        if self.status_code < 400:
            return True
        return False

    def check_header(self, name, value):
        """
        Returns `True` if the response header exist and has appropriate value,
        otherwise, returns `False`.
        """
        if value in self.headers.get(name, ''):
            return True
        return False

def add_video_to_course(course, player_mode, hashes, display_name='Video'):
    category = 'video'

    kwargs = {
        'parent_location': section_location(course),
        'category': category,
        'display_name': display_name,
        'metadata': {},
    }

    if hashes:
        kwargs['metadata'].update(hashes[0])

    conversions = {
        'transcripts': json.loads,
        'download_track': json.loads,
        'download_video': json.loads,
    }

    for key in kwargs['metadata']:
        if key in conversions:
            kwargs['metadata'][key] = conversions[key](kwargs['metadata'][key])

    if player_mode == 'html5':
        kwargs['metadata'].update({
            'youtube_id_1_0': '',
            'youtube_id_0_75': '',
            'youtube_id_1_25': '',
            'youtube_id_1_5': '',
            'html5_sources': HTML5_SOURCES
        })
    if player_mode == 'youtube_html5':
        kwargs['metadata'].update({
            'html5_sources': HTML5_SOURCES,
        })
    if player_mode == 'youtube_html5_unsupported_video':
        kwargs['metadata'].update({
            'html5_sources': HTML5_SOURCES_INCORRECT
        })
    if player_mode == 'html5_unsupported_video':
        kwargs['metadata'].update({
            'youtube_id_1_0': '',
            'youtube_id_0_75': '',
            'youtube_id_1_25': '',
            'youtube_id_1_5': '',
            'html5_sources': HTML5_SOURCES_INCORRECT
        })

    world.scenario_dict['VIDEO'] = world.ItemFactory.create(**kwargs)


def _get_sjson_filename(videoId, lang):
    if lang == 'en':
        return 'subs_{0}.srt.sjson'.format(videoId)
    else:
        return '{0}_subs_{1}.srt.sjson'.format(lang, videoId)


def _upload_file(filename, location):
    path = os.path.join(TEST_ROOT, 'uploads/', filename)
    f = open(os.path.abspath(path))
    mime_type = "application/json"

    content_location = StaticContent.compute_location(
        location.org, location.course, filename
    )
    content = StaticContent(content_location, filename, mime_type, f.read())
    contentstore().save(content)
    del_cached_content(content.location)


def _navigate_to_an_item_in_a_sequence(number):
    sequence_css = '#sequence-list a[data-element="{0}"]'.format(number)
    world.css_click(sequence_css)


def _change_video_speed(speed):
    world.browser.execute_script("$('.speeds').addClass('open')")
    speed_css = 'li[data-speed="{0}"] a'.format(speed)
    world.css_click(speed_css)

def _open_menu(menu):
    world.browser.execute_script("$('{selector}').parent().addClass('open')".format(
        selector=VIDEO_MENUS[menu]
    ))


def _get_all_dimensions():
    video = _get_dimensions('.video-player iframe, .video-player video')
    wrapper = _get_dimensions('.tc-wrapper')
    controls = _get_dimensions('.video-controls')
    progress_slider = _get_dimensions('.video-controls > .slider')

    expected = dict(wrapper)
    expected['height'] -= controls['height'] + 0.5 * progress_slider['height']

    return (video, expected)


def _get_dimensions(selector):
    element = world.css_find(selector).first
    return element._element.size


def _get_window_dimensions():
    return world.browser.driver.get_window_size()


def _set_window_dimensions(width, height):
    world.browser.driver.set_window_size(width, height)
    # Wait 200 ms when JS finish resizing
    world.wait(0.2)


def _duration():
        """
        Total duration of the video, in seconds.
        """
        elapsed_time, duration = _video_time()
        return duration


def _video_time():
        """
        Return a tuple `(elapsed_time, duration)`, each in seconds.
        """
        # The full time has the form "0:32 / 3:14"
        full_time = world.css_text('div.vidtime')

        # Split the time at the " / ", to get ["0:32", "3:14"]
        elapsed_str, duration_str = full_time.split(' / ')

        # Convert each string to seconds
        return (_parse_time_str(elapsed_str), _parse_time_str(duration_str))


def _parse_time_str(time_str):
    """
    Parse a string of the form 1:23 into seconds (int).
    """
    time_obj = time.strptime(time_str, '%M:%S')
    return time_obj.tm_min * 60 + time_obj.tm_sec


@step('when I view the (.*) it does not have autoplay enabled$')
def does_not_autoplay(_step, video_type):
    assert(world.css_find('.%s' % video_type)[0]['data-autoplay'] == 'False')


@step('the course has a Video component in (.*) mode(?:\:)?$')
def view_video(_step, player_mode):
    i_am_registered_for_the_course(_step, coursenum)
    add_video_to_course(coursenum, player_mode.lower(), _step.hashes)
    visit_scenario_item('SECTION')


@step('a video in "([^"]*)" mode(?:\:)?$')
def add_video(_step, player_mode):
    add_video_to_course(coursenum, player_mode.lower(), _step.hashes)
    visit_scenario_item('SECTION')


@step('a video "([^"]*)" in "([^"]*)" mode in position "([^"]*)" of sequential(?:\:)?$')
def add_video_in_position(_step, player_id, player_mode, position):
    sequence[player_id] = position
    add_video_to_course(coursenum, player_mode.lower(), _step.hashes, display_name=player_id)


@step('I open the section with videos$')
def visit_video_section(_step):
    visit_scenario_item('SECTION')


@step('I select the "([^"]*)" speed$')
def change_video_speed(_step, speed):
      _change_video_speed(speed)


@step('I select the "([^"]*)" speed on video "([^"]*)"$')
def change_video_speed_on_video(_step, speed, player_id):
      _navigate_to_an_item_in_a_sequence(sequence[player_id])
      _change_video_speed(speed)


@step('I open video "([^"]*)"$')
def open_video(_step, player_id):
    _navigate_to_an_item_in_a_sequence(sequence[player_id])


@step('video "([^"]*)" should start playing at speed "([^"]*)"$')
def check_video_speed(_step, player_id, speed):
    speed_css = '.speeds p.active'
    assert world.css_has_text(speed_css, '{0}x'.format(speed))


@step('youtube server is up and response time is (.*) seconds$')
def set_youtube_response_timeout(_step, time):
    world.youtube.config['time_to_response'] = float(time)


@step('when I view the video it has rendered in (.*) mode$')
def video_is_rendered(_step, mode):
    modes = {
        'html5': 'video',
        'youtube': 'iframe'
    }
    html_tag = modes[mode.lower()]
    assert world.css_find('.video {0}'.format(html_tag)).first
    assert world.is_css_present('.speed_link')


@step('all sources are correct$')
def all_sources_are_correct(_step):
    elements = world.css_find('.video-player video source')
    sources = [source['src'].split('?')[0] for source in elements]

    assert set(sources) == set(HTML5_SOURCES)


@step('error message is shown$')
def error_message_is_shown(_step):
    selector = '.video .video-player h3'
    assert world.css_visible(selector)


@step('error message has correct text$')
def error_message_has_correct_text(_step):
    selector = '.video .video-player h3'
    text = _('ERROR: No playable video sources found!')
    assert world.css_has_text(selector, text)


@step('I make sure captions are (.+)$')
def set_captions_visibility_state(_step, captions_state):
    SELECTOR = '.closed .subtitles'
    if world.is_css_not_present(SELECTOR):
        if captions_state == 'closed':
            world.css_find('.hide-subtitles').click()
    else:
        if captions_state != 'closed':
            world.css_find('.hide-subtitles').click()


@step('I see video menu "([^"]*)" with correct items$')
def i_see_menu(_step, menu):
    _open_menu(menu)
    menu_items = world.css_find(VIDEO_MENUS[menu] + ' li')
    video = world.scenario_dict['VIDEO']
    transcripts = dict(video.transcripts)
    if video.sub:
        transcripts.update({
            'en': video.sub
        })

    languages = {i[0]: i[1] for i in LANGUAGES}
    transcripts = {k: languages[k] for k in transcripts}

    for code, label in transcripts.items():
        assert any([i.text == label for i in menu_items])
        assert any([i['data-lang-code'] == code for i in menu_items])


@step('I see "([^"]*)" text in the captions$')
def check_text_in_the_captions(_step, text):
    assert world.browser.is_text_present(text.strip())


@step('I select language with code "([^"]*)"$')
def select_language(_step, code):
    _open_menu("language")
    selector = VIDEO_MENUS["language"] + ' li[data-lang-code={code}]'.format(
        code=code
    )

    world.css_click(selector)

    assert world.css_has_class(selector, 'active')
    assert len(world.css_find(VIDEO_MENUS["language"] + ' li.active')) == 1
    assert world.css_visible('.subtitles')
    world.wait_for_ajax_complete()


@step('I click video button "([^"]*)"$')
def click_button(_step, button):
    world.css_click(VIDEO_BUTTONS[button])


@step('I see video starts playing from "([^"]*)" position$')
def start_playing_video_from_n_seconds(_step, position):
    world.wait_for(
        func=lambda _: world.css_html('.vidtime')[:4] == position.strip(),
        timeout=5
    )


@step('I see duration "([^"]*)"$')
def i_see_duration(_step, position):
    world.wait_for(
        func=lambda _: _duration() == _parse_time_str(position),
        timeout=5
    )


@step('I seek video to "([^"]*)" seconds$')
def seek_video_to_n_seconds(_step, seconds):
    time = float(seconds.strip())
    jsCode = "$('.video').data('video-player-state').videoPlayer.onSlideSeek({{time: {0:f}}})".format(time)
    world.browser.execute_script(jsCode)


@step('I have a "([^"]*)" transcript file in assets$')
def upload_to_assets(_step, filename):
    _upload_file(filename, world.scenario_dict['COURSE'].location)


@step('button "([^"]*)" is hidden$')
def is_hidden_button(_step, button):
    assert not world.css_visible(VIDEO_BUTTONS[button])


@step('menu "([^"]*)" doesn\'t exist$')
def is_hidden_menu(_step, menu):
    assert world.is_css_not_present(VIDEO_MENUS[menu])


@step('I see video aligned correctly (with(?:out)?) enabled transcript$')
def video_alignment(_step, transcript_visibility):
    # Width of the video container in css equal 75% of window if transcript enabled
    wrapper_width = 75 if transcript_visibility == "with" else 100
    initial = _get_window_dimensions()

    _set_window_dimensions(300, 600)
    real, expected = _get_all_dimensions()

    width = round(100 * real['width']/expected['width']) == wrapper_width

    _set_window_dimensions(600, 300)
    real, expected = _get_all_dimensions()

    height = abs(expected['height'] - real['height']) <= 5

    # Restore initial window size
    _set_window_dimensions(
        initial['width'], initial['height']
    )

    assert all([width, height])


@step('I can download transcript in "([^"]*)" format and has text "([^"]*)"$')
def i_can_download_transcript(_step, format, text):
    assert world.css_has_text('.video-tracks .a11y-menu-button', '.' + format, strip=True)

    formats = {
        'srt': 'application/x-subrip',
        'txt': 'text/plain',
    }

    url = world.css_find(VIDEO_BUTTONS['download_transcript'])[0]['href']
    request = ReuqestHandlerWithSessionId()
    assert request.get(url).is_success()
    assert request.check_header('content-type', formats[format])
    assert (text.encode('utf-8') in request.content)


@step('I select the transcript format "([^"]*)"$')
def select_transcript_format(_step, format):
    button_selector = '.video-tracks .a11y-menu-button'
    menu_selector = VIDEO_MENUS['download_transcript']

    button = world.css_find(button_selector).first
    button.mouse_over()
    assert world.css_has_text(button_selector, '...', strip=True)

    menu_items = world.css_find(menu_selector + ' a')
    for item in menu_items:
        if item['data-value'] == format:
            item.click()
            world.wait_for_ajax_complete()
            break

    assert world.css_find(menu_selector + ' .active a')[0]['data-value'] == format
    assert world.css_has_text(button_selector, '.' + format, strip=True)
