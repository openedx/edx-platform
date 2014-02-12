#pylint: disable=C0111

from lettuce import world, step
from common import i_am_registered_for_the_course, section_location, visit_scenario_item
from django.utils.translation import ugettext as _

############### ACTIONS ####################

HTML5_SOURCES = [
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.mp4',
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.webm',
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.ogv'
]
HTML5_SOURCES_INCORRECT = [
    'https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.mp99'
]

VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
}

# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5

coursenum = 'test_course'
sequence = {}

@step('when I view the (.*) it does not have autoplay enabled$')
def does_not_autoplay(_step, video_type):
    assert(world.css_find('.%s' % video_type)[0]['data-autoplay'] == 'False')


@step('the course has a Video component in (.*) mode$')
def view_video(_step, player_mode):

    i_am_registered_for_the_course(_step, coursenum)

    # Make sure we have a video
    add_video_to_course(coursenum, player_mode.lower())
    visit_scenario_item('SECTION')


@step('a video "([^"]*)" in "([^"]*)" mode in position "([^"]*)" of sequential$')
def add_video(_step, player_id, player_mode, position):
    sequence[player_id] = position
    add_video_to_course(coursenum, player_mode.lower(), display_name=player_id)


@step('I open the section with videos$')
def visit_video_section(_step):
    visit_scenario_item('SECTION')


@step('I select the "([^"]*)" speed on video "([^"]*)"$')
def change_video_speed(_step, speed, player_id):
      _navigate_to_an_item_in_a_sequence(sequence[player_id])
      _change_video_speed(speed)


@step('I open video "([^"]*)"$')
def open_video(_step, player_id):
    _navigate_to_an_item_in_a_sequence(sequence[player_id])


@step('video "([^"]*)" should start playing at speed "([^"]*)"$')
def check_video_speed(_step, player_id, speed):
    speed_css = '.speeds p.active'
    assert world.css_has_text(speed_css, '{0}x'.format(speed))

def add_video_to_course(course, player_mode, display_name='Video'):
    category = 'video'

    kwargs = {
        'parent_location': section_location(course),
        'category': category,
        'display_name': display_name
    }

    if player_mode == 'html5':
        kwargs.update({
            'metadata': {
                'youtube_id_1_0': '',
                'youtube_id_0_75': '',
                'youtube_id_1_25': '',
                'youtube_id_1_5': '',
                'html5_sources': HTML5_SOURCES
            }
        })
    if player_mode == 'youtube_html5':
        kwargs.update({
            'metadata': {
                'html5_sources': HTML5_SOURCES
            }
        })
    if player_mode == 'youtube_html5_unsupported_video':
        kwargs.update({
            'metadata': {
                'html5_sources': HTML5_SOURCES_INCORRECT
            }
        })
    if player_mode == 'html5_unsupported_video':
        kwargs.update({
            'metadata': {
                'youtube_id_1_0': '',
                'youtube_id_0_75': '',
                'youtube_id_1_25': '',
                'youtube_id_1_5': '',
                'html5_sources': HTML5_SOURCES_INCORRECT
            }
        })

    world.ItemFactory.create(**kwargs)


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
    elements = world.css_find('.video video source')
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


def _navigate_to_an_item_in_a_sequence(number):
    sequence_css = 'a[data-element="{0}"]'.format(number)
    world.css_click(sequence_css)


def _change_video_speed(speed):
    world.browser.execute_script("$('.speeds').addClass('open')")
    speed_css = 'li[data-speed="{0}"] a'.format(speed)
    world.css_click(speed_css)


@step('I click video button "([^"]*)"$')
def click_button_video(_step, button_type):
    world.wait(DELAY)
    world.wait_for_ajax_complete()
    button = button_type.strip()
    world.css_click(VIDEO_BUTTONS[button])


@step('I see video starts playing from "([^"]*)" position$')
def start_playing_video_from_n_seconds(_step, position):
    world.wait_for(
        func=lambda _: world.css_html('.vidtime')[:4] == position.strip(),
        timeout=5
    )


@step('I seek video to "([^"]*)" seconds$')
def seek_video_to_n_seconds(_step, seconds):
    time = float(seconds.strip())
    jsCode = "$('.video').data('video-player-state').videoPlayer.onSlideSeek({{time: {0:f}}})".format(time)
    world.browser.execute_script(jsCode)
