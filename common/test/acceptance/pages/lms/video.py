"""
Video player in the courseware.
"""

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
    'captions': '.subtitles',
    'error_message': '.video .video-player h3',
    'video_container': 'div.video',
    'video_sources': '.video-player video source',
    'video_spinner': '.video-wrapper .spinner',
    'video_xmodule': '.xmodule_VideoModule'
}

VIDEO_MODES = {
    'html5': 'video',
    'youtube': 'iframe'
}


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
    def wait_for_video_class(self):
        """
        Wait until element with class name `video` appeared in DOM.
        """
        video_css = '{0}'.format(CSS_CLASS_NAMES['video_container'])

        wait_for_ajax(self.browser)
        return EmptyPromise(lambda: self.q(css=video_css).present, "Video is initialized").fulfill()

    @wait_for_js
    def wait_for_video_player_render(self):
        """
        Wait until Video Player Rendered Completely.
        """
        def _is_finished_loading():
            return not self.q(css=CSS_CLASS_NAMES['video_spinner']).visible

        self.wait_for_video_class()
        return EmptyPromise(_is_finished_loading, 'Finished loading the video', try_limit=10, timeout=60,
                            try_interval=10).fulfill()

    def is_video_rendered(self, mode):
        """
        Check that if video is rendered in `mode`.
        :param mode: Video mode, `html5` or `youtube`
        """
        html_tag = VIDEO_MODES[mode]
        css = '{0} {1}'.format(CSS_CLASS_NAMES['video_container'], html_tag)

        def _is_element_present():
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
        return self.q(css=VIDEO_BUTTONS[button_id]).visible

    @wait_for_js
    def show_captions(self):
        """
        Show the video captions.
        """
        def _is_subtitles_open():
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
        captions_css = CSS_CLASS_NAMES['captions']

        def _captions_text():
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

    def _get_element_dimensions(self, selector):
        """
        Gets the width and height of element specifies by `selector`
        :param selector: str, css selector of a web element
        :return: dict
        """
        element = self.q(css=selector).results[0]
        return element.size

    def _get_all_dimensions(self):
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
        real, expected = self._get_all_dimensions()

        width = round(100 * real['width'] / expected['width']) == wrapper_width

        self.browser.set_window_size(600, 300)
        real, expected = self._get_all_dimensions()

        height = abs(expected['height'] - real['height']) <= 5

        # Restore initial window size
        self.browser.set_window_size(
            initial['width'], initial['height']
        )

        return all([width, height])

