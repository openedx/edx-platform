"""
Video player in the courseware.
"""

import time
import json
import requests
from selenium.webdriver.common.action_chains import ActionChains
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined

import logging
log = logging.getLogger('VideoPage')

VIDEO_BUTTONS = {
    'transcript': '.language-menu',
    'transcript_button': '.toggle-transcript',
    'cc_button': '.toggle-captions',
    'volume': '.volume',
    'play': '.video_control.play',
    'pause': '.video_control.pause',
    'fullscreen': '.add-fullscreen',
    'download_transcript': '.video-tracks > a',
    'speed': '.speeds',
    'quality': '.quality-control',
    'do_not_show_again': '.skip-control',
    'skip_bumper': '.play-skip-control',
}

CSS_CLASS_NAMES = {
    'captions_closed': '.video.closed',
    'captions_rendered': '.video.is-captions-rendered',
    'captions': '.subtitles',
    'captions_text': '.subtitles li',
    'captions_text_getter': '.subtitles li[role="link"][data-index="1"]',
    'closed_captions': '.closed-captions',
    'error_message': '.video .video-player .video-error',
    'video_container': '.video',
    'video_sources': '.video-player video source',
    'video_spinner': '.video-wrapper .spinner',
    'video_xmodule': '.xmodule_VideoModule',
    'video_init': '.is-initialized',
    'video_time': '.vidtime',
    'video_display_name': '.vert h3',
    'captions_lang_list': '.langs-list li',
    'video_speed': '.speeds .value',
    'poster': '.poster',
}

VIDEO_MODES = {
    'html5': '.video video',
    'youtube': '.video iframe'
}

VIDEO_MENUS = {
    'language': '.lang .menu',
    'speed': '.speed .menu',
    'download_transcript': '.video-tracks .a11y-menu-list',
    'transcript-format': {
        'srt': '.wrapper-download-transcripts .list-download-transcripts .btn-link[data-value="srt"]',
        'txt': '.wrapper-download-transcripts .list-download-transcripts .btn-link[data-value="txt"]'
    },
    'transcript-skip': '.sr-is-focusable.transcript-start',
}


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery',
            'window.MathJax', 'window.MathJax.isReady')
class VideoPage(PageObject):
    """
    Video player in the courseware.
    """

    url = None
    current_video_display_name = None

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='div{0}'.format(CSS_CLASS_NAMES['video_xmodule'])).present

    @wait_for_js
    def wait_for_video_class(self):
        """
        Wait until element with class name `video` appeared in DOM.

        """
        self.wait_for_ajax()

        video_selector = '{0}'.format(CSS_CLASS_NAMES['video_container'])
        self.wait_for_element_presence(video_selector, 'Video is initialized')

    @wait_for_js
    def wait_for_video_player_render(self, autoplay=False):
        """
        Wait until Video Player Rendered Completely.

        """
        self.wait_for_video_class()
        self.wait_for_element_presence(CSS_CLASS_NAMES['video_init'], 'Video Player Initialized')
        self.wait_for_element_presence(CSS_CLASS_NAMES['video_time'], 'Video Player Initialized')

        video_player_buttons = ['volume', 'fullscreen', 'speed']
        if autoplay:
            video_player_buttons.append('pause')
        else:
            video_player_buttons.append('play')

        for button in video_player_buttons:
            self.wait_for_element_visibility(VIDEO_BUTTONS[button], '{} button is visible'.format(button))

        def _is_finished_loading():
            """
            Check if video loading completed.

            Returns:
                bool: Tells Video Finished Loading.

            """
            return not self.q(css=CSS_CLASS_NAMES['video_spinner']).visible

        EmptyPromise(_is_finished_loading, 'Finished loading the video', timeout=200).fulfill()

        self.wait_for_ajax()

    @wait_for_js
    def wait_for_video_bumper_render(self):
        """
        Wait until Poster, Video Pre-Roll and main Video Player are Rendered Completely.
        """
        self.wait_for_video_class()
        self.wait_for_element_presence(CSS_CLASS_NAMES['video_init'], 'Video Player Initialized')
        self.wait_for_element_presence(CSS_CLASS_NAMES['video_time'], 'Video Player Initialized')

        video_player_buttons = ['do_not_show_again', 'skip_bumper', 'volume']
        for button in video_player_buttons:
            self.wait_for_element_visibility(VIDEO_BUTTONS[button], '{} button is visible'.format(button))

    @property
    def is_poster_shown(self):
        """
        Check whether a poster is show.
        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['poster'])
        return self.q(css=selector).visible

    def click_on_poster(self):
        """
        Click on the video poster.
        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['poster'])
        self.q(css=selector).click()

    def get_video_vertical_selector(self, video_display_name=None):
        """
        Get selector for a video vertical with display name specified by `video_display_name`.

        Arguments:
            video_display_name (str or None): Display name of a Video. Default vertical selector if None.

        Returns:
            str: Vertical Selector for video.

        """
        if video_display_name:
            video_display_names = self.q(css=CSS_CLASS_NAMES['video_display_name']).text
            if video_display_name not in video_display_names:
                raise ValueError("Incorrect Video Display Name: '{0}'".format(video_display_name))
            return '.vert.vert-{}'.format(video_display_names.index(video_display_name))
        else:
            return '.vert.vert-0'

    def get_element_selector(self, class_name, vertical=True):
        """
        Construct unique element selector.

        Arguments:
            class_name (str): css class name for an element.
            vertical (bool): do we need vertical css selector or not. vertical css selector is not present in Studio

        Returns:
            str: Element Selector.

        """
        if vertical:
            return '{vertical} {video_element}'.format(
                vertical=self.get_video_vertical_selector(self.current_video_display_name),
                video_element=class_name)
        else:
            return class_name

    def use_video(self, video_display_name):
        """
        Set current video display name.

        Arguments:
            video_display_name (str): Display name of a Video.

        """
        self.current_video_display_name = video_display_name

    def is_video_rendered(self, mode):
        """
        Check that if video is rendered in `mode`.

        Arguments:
            mode (str): Video mode, `html5` or `youtube`.

        Returns:
            bool: Tells if video is rendered in `mode`.

        """
        selector = self.get_element_selector(VIDEO_MODES[mode])

        def _is_element_present():
            """
            Check if a web element is present in DOM.

            Returns:
                tuple: (is_satisfied, result)`, where `is_satisfied` is a boolean indicating whether the promise was
                satisfied, and `result` is a value to return from the fulfilled `Promise`.

            """
            is_present = self.q(css=selector).present
            return is_present, is_present

        return Promise(_is_element_present, 'Video Rendering Failed in {0} mode.'.format(mode)).fulfill()

    @property
    def is_autoplay_enabled(self):
        """
        Extract autoplay value of `data-metadata` attribute to check video autoplay is enabled or disabled.

        Returns:
            bool: Tells if autoplay enabled/disabled.
        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['video_container'])
        auto_play = json.loads(self.q(css=selector).attrs('data-metadata')[0])['autoplay']
        return auto_play

    @property
    def is_error_message_shown(self):
        """
        Checks if video player error message shown.

        Returns:
            bool: Tells about error message visibility.

        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['error_message'])
        return self.q(css=selector).visible

    @property
    def is_spinner_shown(self):
        """
        Checks if video spinner shown.

        Returns:
            bool: Tells about spinner visibility.

        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['video_spinner'])
        return self.q(css=selector).visible

    @property
    def error_message_text(self):
        """
        Extract video player error message text.

        Returns:
            str: Error message text.

        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['error_message'])
        return self.q(css=selector).text[0]

    def is_button_shown(self, button_id):
        """
        Check if a video button specified by `button_id` is visible.

        Arguments:
            button_id (str): key in VIDEO_BUTTONS dictionary, its value will give us the css selector for button.

        Returns:
            bool: Tells about a buttons visibility.

        """
        selector = self.get_element_selector(VIDEO_BUTTONS[button_id])
        return self.q(css=selector).visible

    def show_captions(self):
        """
        Make Captions Visible.
        """
        self._captions_visibility(True)

    def hide_captions(self):
        """
        Make Captions Invisible.
        """
        self._captions_visibility(False)

    def show_closed_captions(self):
        """
        Make closed captions visible.
        """
        self._closed_captions_visibility(True)

    def hide_closed_captions(self):
        """
        Make closed captions invisible.
        """
        self._closed_captions_visibility(False)

    def is_captions_visible(self):
        """
        Get current visibility sate of captions.

        Returns:
            bool: True means captions are visible, False means captions are not visible

        """
        self.wait_for_ajax()
        caption_state_selector = self.get_element_selector(CSS_CLASS_NAMES['captions'])
        return self.q(css=caption_state_selector).visible

    def is_closed_captions_visible(self):
        """
        Get current visibility sate of closed captions.

        Returns:
            bool: True means captions are visible, False means captions are not visible

        """
        self.wait_for_ajax()
        closed_caption_state_selector = self.get_element_selector(CSS_CLASS_NAMES['closed_captions'])
        return self.q(css=closed_caption_state_selector).visible

    @wait_for_js
    def _captions_visibility(self, captions_new_state):
        """
        Set the video captions visibility state.

        Arguments:
            captions_new_state (bool): True means show captions, False means hide captions

        """
        states = {True: 'Shown', False: 'Hidden'}
        state = states[captions_new_state]

        # Make sure that the transcript button is there
        EmptyPromise(lambda: self.is_button_shown('transcript_button'),
                     "transcript button is shown").fulfill()

        # toggle captions visibility state if needed
        if self.is_captions_visible() != captions_new_state:
            self.click_player_button('transcript_button')

            # Verify that captions state is toggled/changed
            EmptyPromise(lambda: self.is_captions_visible() == captions_new_state,
                         "Transcripts are {state}".format(state=state)).fulfill()

    @wait_for_js
    def _closed_captions_visibility(self, closed_captions_new_state):
        """
        Set the video closed captioning visibility state.

        Arguments:
            closed_captions_new_state (bool): True means show closed captioning
        """
        states = {True: 'shown', False: 'hidden'}
        state = states[closed_captions_new_state]

        self.click_player_button('cc_button')

        # Make sure that the captions are visible
        EmptyPromise(lambda: self.is_closed_captions_visible() == closed_captions_new_state,
                     "Closed captions are {state}".format(state=state)).fulfill()

    @property
    def captions_text(self):
        """
        Extract captions text.

        Returns:
            str: Captions Text.

        """
        self.wait_for_captions()

        captions_selector = self.get_element_selector(CSS_CLASS_NAMES['captions_text'])
        subs = self.q(css=captions_selector).html

        return ' '.join(subs)

    @property
    def closed_captions_text(self):
        """
        Extract closed captioning text.

        Returns:
            str: closed captions Text.

        """
        self.wait_for_closed_captions()

        closed_captions_selector = self.get_element_selector(CSS_CLASS_NAMES['closed_captions'])
        subs = self.q(css=closed_captions_selector).html

        return ' '.join(subs)

    def click_first_line_in_transcript(self):
        """
        Clicks a line in the transcript updating the current caption.
        """

        self.wait_for_captions()
        captions_selector = self.q(css=CSS_CLASS_NAMES['captions_text_getter'])
        captions_selector.click()

    @property
    def speed(self):
        """
        Get current video speed value.

        Return:
            str: speed value

        """
        speed_selector = self.get_element_selector(CSS_CLASS_NAMES['video_speed'])
        return self.q(css=speed_selector).text[0]

    @speed.setter
    def speed(self, speed):
        """
        Change the video play speed.

        Arguments:
            speed (str): Video speed value

        """
        # mouse over to video speed button
        speed_menu_selector = self.get_element_selector(VIDEO_BUTTONS['speed'])
        element_to_hover_over = self.q(css=speed_menu_selector).results[0]
        hover = ActionChains(self.browser).move_to_element(element_to_hover_over)
        hover.perform()

        speed_selector = self.get_element_selector('li[data-speed="{speed}"] .control'.format(speed=speed))
        self.q(css=speed_selector).first.click()
        # Click triggers an ajax event
        self.wait_for_ajax()

    def verify_speed_changed(self, expected_speed):
        """
        Wait for the video to change its speed to the expected value. If it does not change,
        the wait call will fail the test.
        """
        self.wait_for(lambda: self.speed == expected_speed, "Video speed changed")

    def click_player_button(self, button):
        """
        Click on `button`.

        Arguments:
            button (str): key in VIDEO_BUTTONS dictionary, its value will give us the css selector for `button`

        """
        button_selector = self.get_element_selector(VIDEO_BUTTONS[button])

        # If we are going to click pause button, Ensure that player is not in buffering state
        if button == 'pause':
            self.wait_for(lambda: self.state != 'buffering', 'Player is Ready for Pause')

        self.q(css=button_selector).first.click()

        self.wait_for_ajax()

    def _get_element_dimensions(self, selector):
        """
        Gets the width and height of element specified by `selector`

        Arguments:
            selector (str): css selector of a web element

        Returns:
            dict: Dimensions of a web element.

        """
        element = self.q(css=selector).results[0]
        return element.size

    @property
    def _dimensions(self):
        """
        Gets the video player dimensions.

        Returns:
            tuple: Dimensions

        """
        iframe_selector = self.get_element_selector('.video-player iframe,')
        video_selector = self.get_element_selector(' .video-player video')
        video = self._get_element_dimensions(iframe_selector + video_selector)
        wrapper = self._get_element_dimensions(self.get_element_selector('.tc-wrapper'))
        controls = self._get_element_dimensions(self.get_element_selector('.video-controls'))
        progress_slider = self._get_element_dimensions(
            self.get_element_selector('.video-controls > .slider'))

        expected = dict(wrapper)
        expected['height'] -= controls['height'] + 0.5 * progress_slider['height']

        return video, expected

    def is_aligned(self, is_transcript_visible):
        """
        Check if video is aligned properly.

        Arguments:
            is_transcript_visible (bool): Transcript is visible or not.

        Returns:
            bool: Alignment result.

        """
        # Width of the video container in css equal 75% of window if transcript enabled
        wrapper_width = 75 if is_transcript_visible else 100
        initial = self.browser.get_window_size()

        self.browser.set_window_size(300, 600)

        # Wait for browser to resize completely
        # Currently there is no other way to wait instead of explicit wait
        time.sleep(0.2)

        real, expected = self._dimensions

        width = round(100 * real['width'] / expected['width']) == wrapper_width

        self.browser.set_window_size(600, 300)

        # Wait for browser to resize completely
        # Currently there is no other way to wait instead of explicit wait
        time.sleep(0.2)

        real, expected = self._dimensions

        height = abs(expected['height'] - real['height']) <= 5

        # Restore initial window size
        self.browser.set_window_size(
            initial['width'], initial['height']
        )

        return all([width, height])

    def _get_transcript(self, url):
        """
        Download Transcript from `url`

        """
        kwargs = dict()

        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        return response.status_code < 400, response.headers, response.content

    def get_cookie(self, cookie_name):
        """
        Searches for and returns `cookie_name`
        """
        return self.browser.get_cookie(cookie_name)

    def downloaded_transcript_contains_text(self, transcript_format, text_to_search):
        """
        Download the transcript in format `transcript_format` and check that it contains the text `text_to_search`

        Arguments:
            transcript_format (str): Transcript file format `srt` or `txt`
            text_to_search (str): Text to search in Transcript.

        Returns:
            bool: Transcript download result.

        """
        transcript_selector = self.get_element_selector(VIDEO_MENUS['transcript-format'][transcript_format])

        # check if we have a transcript with correct format
        if '.' + transcript_format not in self.q(css=transcript_selector).text[0]:
            return False

        formats = {
            'srt': 'application/x-subrip',
            'txt': 'text/plain',
        }

        link = self.q(css=transcript_selector)
        url = link.attrs('href')[0]
        link.click()

        result, headers, content = self._get_transcript(url)

        if result is False:
            return False

        if text_to_search not in content.decode('utf-8'):
            return False

        return True

    def current_language(self):
        """
        Get current selected video transcript language.
        """
        selector = self.get_element_selector(VIDEO_MENUS["language"] + ' li.is-active')
        return self.q(css=selector).first.attrs('data-lang-code')[0]

    def select_language(self, code):
        """
        Select captions for language `code`.

        Arguments:
            code (str): two character language code like `en`, `zh`.

        """
        self.wait_for_ajax()

        # mouse over to transcript button
        cc_button_selector = self.get_element_selector(VIDEO_BUTTONS["transcript"])
        element_to_hover_over = self.q(css=cc_button_selector).results[0]
        ActionChains(self.browser).move_to_element(element_to_hover_over).perform()

        language_selector = VIDEO_MENUS["language"] + ' li[data-lang-code="{code}"]'.format(code=code)
        language_selector = self.get_element_selector(language_selector)
        self.wait_for_element_visibility(language_selector, 'language menu is visible')
        self.q(css=language_selector).first.click()

        # Sometimes language is not clicked correctly. So, if the current language code
        # differs form the expected, we try to change it again.
        if self.current_language() != code:
            self.select_language(code)

        if 'is-active' != self.q(css=language_selector).attrs('class')[0]:
            return False

        active_lang_selector = self.get_element_selector(VIDEO_MENUS["language"] + ' li.is-active')
        if len(self.q(css=active_lang_selector).results) != 1:
            return False

        # Make sure that all ajax requests that affects the display of captions are finished.
        # For example, request to get new translation etc.
        self.wait_for_ajax()

        captions_selector = self.get_element_selector(CSS_CLASS_NAMES['captions'])
        EmptyPromise(lambda: self.q(css=captions_selector).visible, 'Subtitles Visible').fulfill()

        self.wait_for_captions()

        return True

    def is_menu_present(self, menu_name):
        """
        Check if menu `menu_name` exists.

        Arguments:
            menu_name (str): Menu key from VIDEO_MENUS.

        Returns:
            bool: Menu existence result

        """
        selector = self.get_element_selector(VIDEO_MENUS[menu_name])
        return self.q(css=selector).present

    @property
    def sources(self):
        """
        Extract all video source urls on current page.

        Returns:
            list: Video Source URLs.

        """
        sources_selector = self.get_element_selector(CSS_CLASS_NAMES['video_sources'])
        return self.q(css=sources_selector).map(lambda el: el.get_attribute('src').split('?')[0]).results

    @property
    def caption_languages(self):
        """
        Get caption languages available for a video.

        Returns:
            dict: Language Codes('en', 'zh' etc) as keys and Language Names as Values('English', 'Chinese' etc)

        """
        languages_selector = self.get_element_selector(CSS_CLASS_NAMES['captions_lang_list'])
        language_codes = self.q(css=languages_selector).attrs('data-lang-code')
        language_names = self.q(css=languages_selector).attrs('textContent')

        return dict(zip(language_codes, language_names))

    @property
    def position(self):
        """
        Gets current video slider position.

        Returns:
            str: current seek position in format min:sec.

        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['video_time'])
        current_seek_position = self.q(css=selector).text[0]
        return current_seek_position.split('/')[0].strip()

    @property
    def seconds(self):
        """
        Extract seconds part from current video slider position.

        Returns:
            str

        """
        return int(self.position.split(':')[1])

    @property
    def state(self):
        """
        Extract the current state (play, pause etc) of video.

        Returns:
            str: current video state

        """
        state_selector = self.get_element_selector(CSS_CLASS_NAMES['video_container'])
        current_state = self.q(css=state_selector).attrs('class')[0]

        # For troubleshooting purposes show what the current state is.
        # The debug statements will only be displayed in the event of a failure.
        logging.debug("Current state of '{}' element is '{}'".format(state_selector, current_state))

        # See the JS video player's onStateChange function
        if 'is-playing' in current_state:
            return 'playing'
        elif 'is-paused' in current_state:
            return 'pause'
        elif 'is-buffered' in current_state:
            return 'buffering'
        elif 'is-ended' in current_state:
            return 'finished'

    def _wait_for(self, check_func, desc, result=False, timeout=200, try_interval=0.2):
        """
        Calls the method provided as an argument until the Promise satisfied or BrokenPromise

        Arguments:
            check_func (callable): Function that accepts no arguments and returns a boolean indicating whether the promise is fulfilled.
            desc (str): Description of the Promise, used in log messages.
            result (bool): Indicates whether we need a results from Promise or not
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out.

        """
        if result:
            return Promise(check_func, desc, timeout=timeout, try_interval=try_interval).fulfill()
        else:
            return EmptyPromise(check_func, desc, timeout=timeout, try_interval=try_interval).fulfill()

    def wait_for_state(self, state):
        """
        Wait until `state` occurs.

        Arguments:
            state (str): State we wait for.

        """
        self._wait_for(
            lambda: self.state == state,
            'State is {state}'.format(state=state)
        )

    def seek(self, seek_value):
        """
        Seek the video to position specified by `seek_value`.

        Arguments:
            seek_value (str): seek value

        """
        seek_time = _parse_time_str(seek_value)
        seek_selector = self.get_element_selector(' .video')
        js_code = "$('{seek_selector}').data('video-player-state').videoPlayer.onSlideSeek({{time: {seek_time}}})".format(
            seek_selector=seek_selector, seek_time=seek_time)
        self.browser.execute_script(js_code)

        # after seek, player goes into `is-buffered` state. we need to get
        # out of this state before doing any further operation/action.
        def _is_buffering_completed():
            """
            Check if buffering completed
            """
            return self.state != 'buffering'

        self._wait_for(_is_buffering_completed, 'Buffering completed after Seek.')
        self.wait_for_position(seek_value)

    def reload_page(self):
        """
        Reload/Refresh the current video page.
        """
        self.browser.refresh()
        self.wait_for_video_player_render()

    @property
    def duration(self):
        """
        Extract video duration.

        Returns:
            str: duration in format min:sec

        """
        selector = self.get_element_selector(CSS_CLASS_NAMES['video_time'])

        # The full time has the form "0:32 / 3:14" elapsed/duration
        all_times = self.q(css=selector).text[0]

        duration_str = all_times.split('/')[1]

        return duration_str.strip()

    def wait_for_position(self, position):
        """
        Wait until current will be equal to `position`.

        Arguments:
            position (str): position we wait for.

        """
        self._wait_for(
            lambda: self.position == position,
            'Position is {position}'.format(position=position)
        )

    @property
    def is_quality_button_visible(self):
        """
        Get the visibility state of quality button

        Returns:
            bool: visibility status

        """
        selector = self.get_element_selector(VIDEO_BUTTONS['quality'])
        return self.q(css=selector).visible

    @property
    def is_quality_button_active(self):
        """
        Check if quality button is active or not.

        Returns:
            bool: active status

        """
        selector = self.get_element_selector(VIDEO_BUTTONS['quality'])

        classes = self.q(css=selector).attrs('class')[0].split()
        return 'active' in classes

    @property
    def is_transcript_skip_visible(self):
        """
        Checks if the skip-to containers in transcripts are present and visible.

        Returns:
            bool
        """
        selector = self.get_element_selector(VIDEO_MENUS['transcript-skip'])
        return self.q(css=selector).visible

    def wait_for_captions(self):
        """
        Wait until captions rendered completely.
        """
        captions_rendered_selector = self.get_element_selector(CSS_CLASS_NAMES['captions_rendered'])
        self.wait_for_element_presence(captions_rendered_selector, 'Captions Rendered')

    def wait_for_closed_captions(self):
        """
        Wait until closed captions are rendered completely.
        """
        cc_rendered_selector = self.get_element_selector(CSS_CLASS_NAMES['closed_captions'])
        self.wait_for_element_visibility(cc_rendered_selector, 'Closed captions rendered')

    def wait_for_closed_captions_to_be_hidden(self):
        """
        Waits for the closed captions to be turned off completely.
        """
        cc_rendered_selector = self.get_element_selector(CSS_CLASS_NAMES['closed_captions'])
        self.wait_for_element_invisibility(cc_rendered_selector, 'Closed captions hidden')


def _parse_time_str(time_str):
    """
    Parse a string of the form 1:23 into seconds (int).

    Arguments:
        time_str (str): seek value

    Returns:
        int: seek value in seconds

    """
    time_obj = time.strptime(time_str, '%M:%S')
    return time_obj.tm_min * 60 + time_obj.tm_sec
