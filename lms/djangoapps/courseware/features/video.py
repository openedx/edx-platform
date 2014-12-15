# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring

from lettuce import world, step, before, after
import json
import os
import time
import requests
from nose.tools import assert_less, assert_equal, assert_true, assert_false
from common import i_am_registered_for_the_course, visit_scenario_item
from django.utils.translation import ugettext as _
from django.conf import settings
from cache_toolbox.core import del_cached_content
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore


TEST_ROOT = settings.COMMON_TEST_DATA_ROOT
LANGUAGES = settings.ALL_LANGUAGES
VIDEO_SOURCE_PORT = settings.VIDEO_SOURCE_PORT

############### ACTIONS ####################

HTML5_SOURCES = [
    'http://localhost:{0}/gizmo.mp4'.format(VIDEO_SOURCE_PORT),
    'http://localhost:{0}/gizmo.webm'.format(VIDEO_SOURCE_PORT),
    'http://localhost:{0}/gizmo.ogv'.format(VIDEO_SOURCE_PORT),
]

FLASH_SOURCES = {
    'youtube_id_1_0': 'OEoXaMPEzfM',
    'youtube_id_0_75': 'JMD_ifUUfsU',
    'youtube_id_1_25': 'AKqURZnYqpk',
    'youtube_id_1_5': 'DYpADpL7jAY',
}

HTML5_SOURCES_INCORRECT = [
    'http://localhost:{0}/gizmo.mp99'.format(VIDEO_SOURCE_PORT),
]

VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
    'fullscreen': '.add-fullscreen',
    'download_transcript': '.video-tracks > a',
    'quality': '.quality-control',
}

VIDEO_MENUS = {
    'language': '.lang .menu',
    'speed': '.speed .menu',
    'download_transcript': '.video-tracks .a11y-menu-list',
}

coursenum = 'test_course'


@before.each_scenario
def setUp(scenario):
    world.video_sequences = {}


@after.each_scenario
def tearDown(scenario):
    world.browser.cookies.delete('edX_video_player_mode')


class RequestHandlerWithSessionId(object):
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


def get_metadata(parent_location, player_mode, data, display_name='Video'):
    kwargs = {
        'parent_location': parent_location,
        'category': 'video',
        'display_name': display_name,
        'metadata': {},
    }

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

    if player_mode == 'flash':
        kwargs['metadata'].update(FLASH_SOURCES)
        world.browser.cookies.add({'edX_video_player_mode': 'flash'})

    if data:
        conversions = {
            'transcripts': json.loads,
            'download_track': json.loads,
            'download_video': json.loads,
        }

        for key in data:
            if key in conversions:
                data[key] = conversions[key](data[key])

        kwargs['metadata'].update(data)

    return kwargs


def add_videos_to_course(course, player_mode=None, display_names=None, hashes=None):
    parent_location = add_vertical_to_course(course)
    kwargs = {
        'course': course,
        'parent_location': parent_location,
        'player_mode': player_mode,
        'display_name': display_names[0],
    }

    if hashes:
        for index, item_data in enumerate(hashes):
            kwargs.update({
                'display_name': display_names[index],
                'data': item_data,
            })
            add_video_to_course(**kwargs)
    else:
        add_video_to_course(**kwargs)


def add_video_to_course(course, parent_location=None, player_mode=None, data=None, display_name='Video'):

    if not parent_location:
        parent_location = add_vertical_to_course(course)
    kwargs = get_metadata(parent_location, player_mode, data, display_name=display_name)
    world.scenario_dict['VIDEO'] = world.ItemFactory.create(**kwargs)


def add_vertical_to_course(course_num):
    world.scenario_dict['LAST_VERTICAL'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['SECTION'].location,
        category='vertical',
        display_name='Test Vertical-{}'.format(len(set(world.video_sequences.values()))),
    )

    return last_vertical_location(course_num)


def last_vertical_location(course_num):
    return world.scenario_dict['LAST_VERTICAL'].location.replace(course=course_num)


def upload_file(filename, location):
    path = os.path.join(TEST_ROOT, 'uploads/', filename)
    f = open(os.path.abspath(path))
    mime_type = "application/json"

    content_location = StaticContent.compute_location(
        location.course_key, filename
    )
    content = StaticContent(content_location, filename, mime_type, f.read())
    contentstore().save(content)
    del_cached_content(content.location)


def navigate_to_an_item_in_a_sequence(number):
    sequence_css = '#sequence-list a[data-element="{0}"]'.format(number)
    world.css_click(sequence_css)


def change_video_speed(speed):
    world.browser.execute_script("$('.speeds').addClass('is-opened')")
    speed_css = 'li[data-speed="{0}"] a'.format(speed)
    world.wait_for_visible('.speeds')
    world.css_click(speed_css)


def open_menu(menu):
    world.browser.execute_script("$('{selector}').parent().addClass('is-opened')".format(
        selector=VIDEO_MENUS[menu]
    ))


def get_all_dimensions():
    video = get_dimensions('.video-player iframe, .video-player video')
    wrapper = get_dimensions('.tc-wrapper')
    controls = get_dimensions('.video-controls')
    progress_slider = get_dimensions('.video-controls > .slider')

    expected = dict(wrapper)
    expected['height'] -= controls['height'] + 0.5 * progress_slider['height']

    return (video, expected)


def get_dimensions(selector):
    element = world.css_find(selector).first
    return element._element.size


def get_window_dimensions():
    return world.browser.driver.get_window_size()


def set_window_dimensions(width, height):
    world.browser.driver.set_window_size(width, height)
    # Wait 200 ms when JS finish resizing
    world.wait(0.2)


def duration():
    """
    Total duration of the video, in seconds.
    """
    elapsed_time, duration = video_time()
    return duration


def elapsed_time():
    """
    Elapsed time of the video, in seconds.
    """
    elapsed_time, duration = video_time()
    return elapsed_time


def video_time():
    """
    Return a tuple `(elapsed_time, duration)`, each in seconds.
    """
    # The full time has the form "0:32 / 3:14"
    full_time = world.css_text('div.vidtime')

    # Split the time at the " / ", to get ["0:32", "3:14"]
    elapsed_str, duration_str = full_time.split(' / ')

    # Convert each string to seconds
    return (parse_time_str(elapsed_str), parse_time_str(duration_str))


def parse_time_str(time_str):
    """
    Parse a string of the form 1:23 into seconds (int).
    """
    time_obj = time.strptime(time_str, '%M:%S')
    return time_obj.tm_min * 60 + time_obj.tm_sec


def find_caption_line_by_data_index(index):
    SELECTOR = ".subtitles > li[data-index='{index}']".format(index=index)
    return world.css_find(SELECTOR).first


def wait_for_video():
    world.wait_for_present('.is-initialized')
    world.wait_for_present('div.vidtime')
    world.wait_for_invisible('.video-wrapper .spinner')
    world.wait_for_ajax_complete()


@step("I reload the page with video$")
def reload_the_page_with_video(_step):
    _step.given('I reload the page')
    wait_for_video()


@step('youtube stub server (.*) YouTube API')
def configure_youtube_api(_step, action):
    action = action.strip()
    if action == 'proxies':
        world.youtube.config['youtube_api_blocked'] = False
    elif action == 'blocks':
        world.youtube.config['youtube_api_blocked'] = True
    else:
        raise ValueError('Parameter `action` should be one of "proxies" or "blocks".')


@step('when I view the (.*) it does not have autoplay enabled$')
def does_not_autoplay(_step, video_type):
    actual = world.css_find('.%s' % video_type)[0]['data-autoplay']
    expected = [u'False', u'false', False]
    assert actual in expected


@step('the course has a Video component in "([^"]*)" mode(?:\:)?$')
def view_video(_step, player_mode):
    i_am_registered_for_the_course(_step, coursenum)
    data = _step.hashes[0] if _step.hashes else None
    add_video_to_course(coursenum, player_mode=player_mode.lower(), data=data)
    visit_scenario_item('SECTION')
    wait_for_video()


@step('a video in "([^"]*)" mode(?:\:)?$')
def add_video(_step, player_mode):
    data = _step.hashes[0] if _step.hashes else None
    add_video_to_course(coursenum, player_mode=player_mode.lower(), data=data)
    visit_scenario_item('SECTION')
    wait_for_video()


@step('video(?:s)? "([^"]*)" in "([^"]*)" mode in position "([^"]*)" of sequential(?:\:)?$')
def add_video_in_position(_step, video_ids, player_mode, position):
    sequences = {video_id.strip(): position for video_id in video_ids.split(',')}
    add_videos_to_course(coursenum, player_mode=player_mode.lower(), display_names=sequences.keys(), hashes=_step.hashes)
    world.video_sequences.update(sequences)


@step('I open the section with videos$')
def visit_video_section(_step):
    visit_scenario_item('SECTION')
    wait_for_video()


@step('I select the "([^"]*)" speed$')
def i_select_video_speed(_step, speed):
    change_video_speed(speed)


@step('I select the "([^"]*)" speed on video "([^"]*)"$')
def change_video_speed_on_video(_step, speed, player_id):
    navigate_to_an_item_in_a_sequence(world.video_sequences[player_id])
    change_video_speed(speed)


@step('I open video "([^"]*)"$')
def open_video(_step, player_id):
    navigate_to_an_item_in_a_sequence(world.video_sequences[player_id])


@step('video "([^"]*)" should start playing at speed "([^"]*)"$')
def check_video_speed(_step, player_id, speed):
    speed_css = '.speeds .value'
    assert world.css_has_text(speed_css, '{0}x'.format(speed))


@step('youtube server is up and response time is (.*) seconds$')
def set_youtube_response_timeout(_step, time):
    world.youtube.config['time_to_response'] = float(time)


@step('the video has rendered in "([^"]*)" mode$')
def video_is_rendered(_step, mode):
    modes = {
        'html5': 'video',
        'youtube': 'iframe',
        'flash': 'iframe',
    }
    html_tag = modes[mode.lower()]
    assert world.css_find('.video {0}'.format(html_tag)).first


@step('videos have rendered in "([^"]*)" mode$')
def videos_are_rendered(_step, mode):
    modes = {
        'html5': 'video',
        'youtube': 'iframe',
        'flash': 'iframe',
    }
    html_tag = modes[mode.lower()]

    actual = len(world.css_find('.video {0}'.format(html_tag)))
    expected = len(world.css_find('.xmodule_VideoModule'))
    assert actual == expected


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
            world.css_click('.hide-subtitles')
    else:
        if captions_state != 'closed':
            world.css_click('.hide-subtitles')


@step('I see video menu "([^"]*)" with correct items$')
def i_see_menu(_step, menu):
    open_menu(menu)
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
    world.wait_for_present('.video.is-captions-rendered')
    world.wait_for(lambda _: world.css_text('.subtitles'))
    actual_text = world.css_text('.subtitles')
    assert (text in actual_text)


@step('I see text in the captions:')
def check_captions(_step):
    world.wait_for_present('.video.is-captions-rendered')
    for index, video in enumerate(_step.hashes):
        assert (video.get('text') in world.css_text('.subtitles', index=index))


@step('I select language with code "([^"]*)"$')
def select_language(_step, code):
    world.wait_for_visible('.video-controls')
    # Make sure that all ajax requests that affects the language menu are finished.
    # For example, request to get new translation etc.
    world.wait_for_ajax_complete()
    selector = VIDEO_MENUS["language"] + ' li[data-lang-code="{code}"]'.format(
        code=code
    )

    world.css_find(VIDEO_BUTTONS["CC"])[0].mouse_over()
    world.wait_for_present('.lang.open')
    world.css_click(selector)

    assert world.css_has_class(selector, 'is-active')
    assert len(world.css_find(VIDEO_MENUS["language"] + ' li.is-active')) == 1

    # Make sure that all ajax requests that affects the display of captions are finished.
    # For example, request to get new translation etc.
    world.wait_for_ajax_complete()
    world.wait_for_visible('.subtitles')
    world.wait_for_present('.video.is-captions-rendered')


@step('I click video button "([^"]*)"$')
def click_button(_step, button):
    world.css_click(VIDEO_BUTTONS[button])
    if button == "play":
        # Needs to wait for video buffrization
        world.wait_for(
            func=lambda _: world.css_has_class('.video', 'is-playing') and world.is_css_present(VIDEO_BUTTONS['pause']),
            timeout=30
        )

    world.wait_for_ajax_complete()


@step('I see video slider at "([^"]*)" position$')
def start_playing_video_from_n_seconds(_step, time_str):
    position = parse_time_str(time_str)
    actual_position = elapsed_time()
    assert_equal(actual_position, int(position), "Current position is {}, but should be {}".format(actual_position, position))


@step('I see duration "([^"]*)"$')
def i_see_duration(_step, position):
    world.wait_for(
        func=lambda _: duration() > 0,
        timeout=30
    )

    assert duration() == parse_time_str(position)


@step('I wait for video controls appear$')
def controls_appear(_step):
    world.wait_for_visible('.video-controls')


@step('I seek video to "([^"]*)" position$')
def seek_video_to_n_seconds(_step, time_str):
    time = parse_time_str(time_str)
    jsCode = "$('.video').data('video-player-state').videoPlayer.onSlideSeek({{time: {0}}})".format(time)
    world.browser.execute_script(jsCode)
    world.wait_for(
        func=lambda _: world.retry_on_exception(lambda: elapsed_time() == time and not world.css_has_class('.video', 'is-buffering')),
        timeout=30
    )
    _step.given('I see video slider at "{0}" position'.format(time_str))


@step('I have a "([^"]*)" transcript file in assets$')
def upload_to_assets(_step, filename):
    upload_file(filename, world.scenario_dict['COURSE'].location)


@step('menu "([^"]*)" doesn\'t exist$')
def is_hidden_menu(_step, menu):
    assert world.is_css_not_present(VIDEO_MENUS[menu])


@step('I see video aligned correctly (with(?:out)?) enabled transcript$')
def video_alignment(_step, transcript_visibility):
    # Width of the video container in css equal 75% of window if transcript enabled
    wrapper_width = 75 if transcript_visibility == "with" else 100
    initial = get_window_dimensions()

    set_window_dimensions(300, 600)
    real, expected = get_all_dimensions()
    width = round(100 * real['width'] / expected['width']) == wrapper_width

    set_window_dimensions(600, 300)
    real, expected = get_all_dimensions()
    height = abs(expected['height'] - real['height']) <= 5
    # Restore initial window size
    set_window_dimensions(initial['width'], initial['height'])

    assert all([width, height])


@step('I can download transcript in "([^"]*)" format that has text "([^"]*)"$')
def i_can_download_transcript(_step, format, text):
    assert world.css_has_text('.video-tracks .a11y-menu-button', '.' + format, strip=True)

    formats = {
        'srt': 'application/x-subrip',
        'txt': 'text/plain',
    }

    url = world.css_find(VIDEO_BUTTONS['download_transcript'])[0]['href']
    request = RequestHandlerWithSessionId()
    assert request.get(url).is_success()
    assert request.check_header('content-type', formats[format])
    assert (text.encode('utf-8') in request.content)


@step('I select the transcript format "([^"]*)"$')
def select_transcript_format(_step, format):
    button_selector = '.video-tracks .a11y-menu-button'
    menu_selector = VIDEO_MENUS['download_transcript']

    button = world.css_find(button_selector).first

    height = button._element.location_once_scrolled_into_view['y']
    world.browser.driver.execute_script("window.scrollTo(0, {});".format(height))

    button.mouse_over()
    assert world.css_has_text(button_selector, '...', strip=True)

    menu_items = world.css_find(menu_selector + ' a')
    for item in menu_items:
        if item['data-value'] == format:
            item.click()
            world.wait_for_ajax_complete()
            break

    world.browser.driver.execute_script("window.scrollTo(0, 0);")

    assert world.css_find(menu_selector + ' .active a')[0]['data-value'] == format
    assert world.css_has_text(button_selector, '.' + format, strip=True)


@step('video (.*) show the captions$')
def shows_captions(_step, show_captions):
    if 'not' in show_captions or 'n\'t' in show_captions:
        assert world.is_css_present('div.video.closed')
    else:
        assert world.is_css_not_present('div.video.closed')


@step('I click on caption line "([^"]*)", video module shows elapsed time "([^"]*)"$')
def click_on_the_caption(_step, index, expected_time):
    world.wait_for_present('.video.is-captions-rendered')
    find_caption_line_by_data_index(int(index)).click()
    actual_time = elapsed_time()
    assert int(expected_time) == actual_time


@step('button "([^"]*)" is (hidden|visible)$')
def is_hidden_button(_step, button, state):
    selector = VIDEO_BUTTONS[button]
    if state == 'hidden':
        world.wait_for_invisible(selector)
        assert_false(
            world.css_visible(selector),
            'Button {0} is invisible, but should be visible'.format(button)
        )
    else:
        world.wait_for_visible(selector)
        assert_true(
            world.css_visible(selector),
            'Button {0} is visible, but should be invisible'.format(button)
        )


@step('button "([^"]*)" is (active|inactive)$')
def i_see_active_button(_step, button, state):
    selector = VIDEO_BUTTONS[button]
    if state == 'active':
        assert world.css_has_class(selector, 'active')
    else:
        assert not world.css_has_class(selector, 'active')
