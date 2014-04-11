"""
Video player in the courseware.
"""

import time
import requests
from selenium.webdriver.common.action_chains import ActionChains
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined
from ...tests.helpers import wait_for_ajax


VIDEO_BUTTONS = {
    'CC': '.hide-subtitles',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
    'fullscreen': '.add-fullscreen',
    'download_transcript': '.video-tracks > a',
}

CSS_CLASS_NAMES = {
    'closed_captions': '.closed .subtitles',
    'captions_rendered': '.video.is-captions-rendered',
    'captions': '.subtitles',
    'error_message': '.video .video-player h3',
    'video_container': 'div.video',
    'video_sources': '.video-player video source',
    'video_spinner': '.video-wrapper .spinner',
    'video_xmodule': '.xmodule_VideoModule',
    'video_init': '.is-initialized',
    'video_time': 'div.vidtime'
}

VIDEO_MODES = {
    'html5': 'video',
    'youtube': 'iframe'
}

VIDEO_MENUS = {
    'language': '.lang .menu',
    'speed': '.speed .menu',
    'download_transcript': '.video-tracks .a11y-menu-list',
}

WAIT_TIMEOUT = 60
WAIT_TRY_LIMIT = 10
WAIT_TRY_INTERVAL = 20


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery')
class VideoPage(PageObject):
    """
    Video player in the courseware.
    """

    url = None

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='div{0}'.format(CSS_CLASS_NAMES['video_xmodule'])).present

    @wait_for_js
    def _wait_for_element(self, element_css_selector, promise_desc, try_limit=WAIT_TRY_LIMIT, timeout=WAIT_TIMEOUT,
                          try_interval=WAIT_TRY_INTERVAL):
        """
        Wait for element specified by `element_css_selector` is present in DOM.
        :param element_css_selector: css selector
        :return:
        """

        def _is_element_present():
            """
            Check if web-element present in DOM
            :return: bool
            """
            return self.q(css=element_css_selector).present

        EmptyPromise(_is_element_present, promise_desc, try_limit=try_limit, timeout=timeout,
                     try_interval=try_interval).fulfill()

    @wait_for_js
    def wait_for_video_class(self):
        """
        Wait until element with class name `video` appeared in DOM.
        """
        wait_for_ajax(self.browser)

        video_css = '{0}'.format(CSS_CLASS_NAMES['video_container'])
        self._wait_for_element(video_css, 'Video is initialized')

    @wait_for_js
    def wait_for_video_player_render(self):
        """
        Wait until Video Player Rendered Completely.
        """
        self.wait_for_video_class()
        self._wait_for_element(CSS_CLASS_NAMES['video_init'], 'Video Player Initialized')
        self._wait_for_element(CSS_CLASS_NAMES['video_time'], 'Video Player Initialized')

        def _is_finished_loading():
            """
            Check if video loading completed
            :return: bool
            """
            return not self.q(css=CSS_CLASS_NAMES['video_spinner']).visible

        EmptyPromise(_is_finished_loading, 'Finished loading the video', try_limit=WAIT_TRY_LIMIT, timeout=WAIT_TIMEOUT,
                     try_interval=WAIT_TRY_INTERVAL).fulfill()

        wait_for_ajax(self.browser)

    def is_video_rendered(self, mode):
        """
        Check that if video is rendered in `mode`.
        :param mode: Video mode, `html5` or `youtube`
        """
        html_tag = VIDEO_MODES[mode]
        css = '{0} {1}'.format(CSS_CLASS_NAMES['video_container'], html_tag)

        def _is_element_present():
            """
            Check if a web element is present in DOM
            :return:
            """
            is_present = self.q(css=css).present
            return is_present, is_present

        return Promise(_is_element_present, 'Video Rendering Failed in {0} mode.'.format(mode)).fulfill()

    @property
    def all_video_sources(self):
        """
        Extract all video source urls on current page.
        """
        return self.q(css=CSS_CLASS_NAMES['video_sources']).map(
            lambda el: el.get_attribute('src').split('?')[0]).results

    @property
    def is_autoplay_enabled(self):
        """
        Extract `data-autoplay` attribute to check video autoplay is enabled or disabled.
        """
        auto_play = self.q(css=CSS_CLASS_NAMES['video_container']).attrs('data-autoplay')[0]

        if auto_play.lower() == 'false':
            return False

        return True

    @property
    def is_error_message_shown(self):
        """
        Checks if video player error message shown.
        :return: bool
        """
        return self.q(css=CSS_CLASS_NAMES['error_message']).visible

    @property
    def error_message_text(self):
        """
        Extract video player error message text.
        :return: str
        """
        return self.q(css=CSS_CLASS_NAMES['error_message']).text[0]

    def is_button_shown(self, button_id):
        """
        Check if a video button specified by `button_id` is visible
        :param button_id: button css selector
        :return: bool
        """
        return self.q(css=VIDEO_BUTTONS[button_id]).visible

    @wait_for_js
    def show_captions(self):
        """
        Show the video captions.
        """

        def _is_subtitles_open():
            """
            Check if subtitles are opened
            :return: bool
            """
            is_open = not self.q(css=CSS_CLASS_NAMES['closed_captions']).present
            return is_open

        # Make sure that the CC button is there
        EmptyPromise(lambda: self.is_button_shown('CC'),
                     "CC button is shown").fulfill()

        # Check if the captions are already open and click if not
        if _is_subtitles_open() is False:
            self.q(css=VIDEO_BUTTONS['CC']).first.click()

        # Verify that they are now open
        EmptyPromise(_is_subtitles_open,
                     "Subtitles are shown").fulfill()

    @property
    def captions_text(self):
        """
        Extract captions text.
        :return: str
        """
        # wait until captions rendered completely
        self._wait_for_element(CSS_CLASS_NAMES['captions_rendered'], 'Captions Rendered')

        captions_css = CSS_CLASS_NAMES['captions']

        # from nose.tools import set_trace; set_trace()

        def _captions_text():
            """
            Extract captions text.
            :return: tuple
            """
            is_present = self.q(css=captions_css).present
            result = None

            if is_present:
                result = self.q(css=captions_css).text[0]

            return is_present, result

        return Promise(_captions_text, 'Captions Text').fulfill()

    def set_speed(self, speed):
        """
        Change the video play speed.
        :param speed: speed value in str
        """
        self.browser.execute_script("$('.speeds').addClass('open')")
        speed_css = 'li[data-speed="{0}"] a'.format(speed)
        self.q(css=speed_css).first.click()

    def get_speed(self):
        """
        Get current video speed value.
        :return: str
        """
        speed_css = '.speeds p.active'
        return self.q(css=speed_css).text[0]

    speed = property(get_speed, set_speed)

    def reload_page(self):
        """
        Reload/Refresh the current video page.
        """
        self.browser.refresh()

        self.wait_for_video_player_render()

    def click_player_button(self, button):
        """
        Click on `button`.
        :param button: key in VIDEO_BUTTONS dictionary, its value will give us the css selector for `button`
        """
        self.q(css=VIDEO_BUTTONS[button]).first.click()

        wait_for_ajax(self.browser)

    def _get_element_dimensions(self, selector):
        """
        Gets the width and height of element specifies by `selector`
        :param selector: str, css selector of a web element
        :return: dict
        """
        element = self.q(css=selector).results[0]
        return element.size

    def _get_dimensions(self):
        """
        Gets the video player dimensions
        :return: tuple
        """
        video = self._get_element_dimensions('.video-player iframe, .video-player video')
        wrapper = self._get_element_dimensions('.tc-wrapper')
        controls = self._get_element_dimensions('.video-controls')
        progress_slider = self._get_element_dimensions('.video-controls > .slider')

        expected = dict(wrapper)
        expected['height'] -= controls['height'] + 0.5 * progress_slider['height']

        return video, expected

    def is_aligned(self, is_transcript_visible):
        """
        Check if video is aligned properly.
        :param is_transcript_visible: bool
        :return: bool
        """
        # Width of the video container in css equal 75% of window if transcript enabled
        wrapper_width = 75 if is_transcript_visible else 100
        initial = self.browser.get_window_size()

        self.browser.set_window_size(300, 600)
        real, expected = self._get_dimensions()

        width = round(100 * real['width'] / expected['width']) == wrapper_width

        self.browser.set_window_size(600, 300)
        real, expected = self._get_dimensions()

        height = abs(expected['height'] - real['height']) <= 5

        # Restore initial window size
        self.browser.set_window_size(
            initial['width'], initial['height']
        )

        return all([width, height])

    def _get_transcript(self, url):
        """
        Sends a http get request.
        """
        kwargs = dict()

        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        return response.status_code < 400, response.headers, response.content

    def can_we_download_transcript(self, transcript_format, text_to_search):
        """
        Check if we can download a transcript in format `transcript_format` having text `text_to_search`
        :param transcript_format: `srt` or `txt`
        :param text_to_search: str
        :return: bool
        """
        from nose.tools import set_trace; set_trace()
        # check if we have a transcript with correct format
        if '.' + transcript_format not in self.q(css='.video-tracks .a11y-menu-button').text[0]:
            return False

        formats = {
            'srt': 'application/x-subrip',
            'txt': 'text/plain',
        }

        url = self.q(css=VIDEO_BUTTONS['download_transcript']).attrs('href')[0]
        result, headers, content = self._get_transcript(url)

        if result is False:
            return False

        if formats[transcript_format] not in headers.get('content-type', ''):
            return False

        if text_to_search not in content.decode('utf-8'):
            return False

        return True

    def select_language(self, code):
        """
        Select captions for language `code`
        :param code: str, two character language code like `en`, `zh`
        :return: bool, True for Success, False for Failure or BrokenPromise
        """

        wait_for_ajax(self.browser)

        selector = VIDEO_MENUS["language"] + ' li[data-lang-code="{code}"]'.format(code=code)

        element_to_hover_over = self.q(css=VIDEO_BUTTONS["CC"]).results[0]
        hover = ActionChains(self.browser).move_to_element(element_to_hover_over)
        hover.perform()

        self.q(css=selector).first.click()

        if 'active' != self.q(css=selector).attrs('class')[0]:
            return False

        if len(self.q(css=VIDEO_MENUS["language"] + ' li.active').results) != 1:
            return False

        # Make sure that all ajax requests that affects the display of captions are finished.
        # For example, request to get new translation etc.
        wait_for_ajax(self.browser)

        EmptyPromise(lambda: self.q(css='.subtitles').visible, 'Subtitles Visible.').fulfill()

        return True

    @property
    def all_video_sources(self):
        """
        Extract all video source urls on current page.
        """
        return self.q(css='.video-player video source').map(lambda el: el.get_attribute('src').split('?')[0]).results

    def select_transcript_format(self, transcript_format):
        """
        Select transcript with format `transcript_format`
        :param transcript_format: `srt` or `txt`
        :return: bool
        """
        button_selector = '.video-tracks .a11y-menu-button'
        menu_selector = VIDEO_MENUS['download_transcript']

        button = self.q(css=button_selector).results[0]

        height = button.location_once_scrolled_into_view['y']
        self.browser.execute_script("window.scrollTo(0, {});".format(height))

        hover = ActionChains(self.browser).move_to_element(button)
        hover.perform()

        if '...' not in self.q(css=button_selector).text[0]:
            return False

        menu_items = self.q(css=menu_selector + ' a').results
        for item in menu_items:
            if item.get_attribute('data-value') == transcript_format:
                item.click()
                wait_for_ajax(self.browser)
                break

        self.browser.execute_script("window.scrollTo(0, 0);")

        if self.q(css=menu_selector + ' .active a').attrs('data-value')[0] != transcript_format:
            return False

        if '.' + transcript_format not in self.q(css=button_selector).text[0]:
            return False

        return True

    def is_menu_exist(self, menu_name):
        """
        Check if menu `menu_name` exists
        :param menu_name: menu name
        :return: bool
        :
        """
        return self.q(css=VIDEO_MENUS[menu_name]).present

    def _video_time(self):
        """
        Return a tuple `(elapsed_time, duration)`, each in seconds.
        """
        # The full time has the form "0:32 / 3:14"
        all_times = self.q(css='div.vidtime').text

        if len(all_times) == 0:
            self.warning('Could not find video time')

        else:
            full_time = all_times[0]

            # Split the time at the " / ", to get ["0:32", "3:14"]
            elapsed_str, duration_str = full_time.split(' / ')

            # Convert each string to seconds
            return self._parse_time_str(elapsed_str), self._parse_time_str(duration_str)

    @property
    def duration(self):
        """
        Total duration of the video, in seconds.
        """
        _, duration = self._video_time()
        return duration

    def _parse_time_str(self, time_str):
        """
        Parse a string of the form 1:23 into seconds (int).
        """
        time_obj = time.strptime(time_str, '%M:%S')
        return time_obj.tm_min * 60 + time_obj.tm_sec

    def is_duration_matches(self, time_str):
        """
        Checks if video duration equals to duration calculated from `time_str`
        :param time_str: time string in form 1:23
        :return: bool
        """
        duration_in_seconds = self._parse_time_str(time_str)

        if duration_in_seconds == self.duration:
            return True
        return False