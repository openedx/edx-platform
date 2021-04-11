"""
Video player in the courseware.
"""


import logging

from bok_choy.javascript import js_defined, wait_for_js
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise

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
    'captions_text': '.subtitles li span',
    'captions_text_getter': u'.subtitles li span[role="link"][data-index="{}"]',
    'closed_captions': '.closed-captions',
    'error_message': '.video .video-player .video-error',
    'video_container': '.video',
    'video_sources': '.video-player video source',
    'video_spinner': '.video-wrapper .spinner',
    'video_xmodule': '.xmodule_VideoBlock',
    'video_init': '.is-initialized',
    'video_time': '.vidtime',
    'video_display_name': '.vert h3',
    'captions_lang_list': '.langs-list li',
    'video_speed': '.speeds .value',
    'poster': '.poster',
    'active_caption_text': '.subtitles-menu > li.current span',
}

VIDEO_MODES = {
    'html5': '.video video',
    'youtube': '.video iframe',
    'hls': '.video video',
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


@js_defined('window.Video', 'window.jQuery', 'window.MathJax')
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
            self.wait_for_element_visibility(VIDEO_BUTTONS[button], u'{} button is visible'.format(button))

        def _is_finished_loading():
            """
            Check if video loading completed.

            Returns:
                bool: Tells Video Finished Loading.

            """
            return not self.q(css=CSS_CLASS_NAMES['video_spinner']).visible

        EmptyPromise(_is_finished_loading, 'Finished loading the video', timeout=200).fulfill()

        self.wait_for_ajax()

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
                raise ValueError(u"Incorrect Video Display Name: '{0}'".format(video_display_name))
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
            return u'{vertical} {video_element}'.format(
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

    def is_captions_visible(self):
        """
        Get current visibility sate of captions.

        Returns:
            bool: True means captions are visible, False means captions are not visible

        """
        self.wait_for_ajax()
        caption_state_selector = self.get_element_selector(CSS_CLASS_NAMES['captions'])
        return self.q(css=caption_state_selector).visible

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
                         u"Transcripts are {state}".format(state=state)).fulfill()
