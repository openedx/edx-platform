"""
CMS Video
"""

import os
import requests
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined
from ....tests.helpers import YouTubeStubConfig
from ...lms.video.video import VideoPage
from selenium.webdriver.common.keys import Keys


CLASS_SELECTORS = {
    'video_container': 'div.video',
    'video_init': '.is-initialized',
    'video_xmodule': '.xmodule_VideoModule',
    'video_spinner': '.video-wrapper .spinner',
    'video_controls': 'section.video-controls',
    'attach_handout': '.upload-dialog > input[type="file"]',
    'upload_dialog': '.wrapper-modal-window-assetupload',
    'xblock': '.add-xblock-component',
    'slider_range': '.slider-range',
}

BUTTON_SELECTORS = {
    'create_video': 'a[data-category="video"]',
    'handout_download': '.video-handout.video-download-button a',
    'handout_download_editor': '.wrapper-comp-setting.file-uploader .download-action',
    'upload_handout': '.upload-action',
    'handout_submit': '.action-upload',
    'handout_clear': '.wrapper-comp-setting.file-uploader .setting-clear',
}


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery', 'window.XModule', 'window.XBlock',
            'window.MathJax.isReady')
class VideoComponentPage(VideoPage):
    """
    CMS Video Component Page
    """

    url = None

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='div{0}'.format(CLASS_SELECTORS['video_xmodule'])).present or self.q(
            css='div{0}'.format(CLASS_SELECTORS['xblock'])).present

    def get_element_selector(self, class_name, vertical=False):
        return super(VideoComponentPage, self).get_element_selector(class_name, vertical=vertical)

    def _wait_for(self, check_func, desc, result=False, timeout=30):
        """
        Calls the method provided as an argument until the Promise satisfied or BrokenPromise

        Arguments:
            check_func (callable): Promise function to be fulfilled.
            desc (str): Description of the Promise, used in log messages.
            result (bool): Indicates whether we need result from Promise or not
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out.

        """
        if result:
            return Promise(check_func, desc, timeout=timeout).fulfill()
        else:
            return EmptyPromise(check_func, desc, timeout=timeout).fulfill()

    def wait_for_video_component_render(self):
        """
        Wait until video component rendered completely
        """
        if not YouTubeStubConfig.get_configuration().get('youtube_api_blocked'):
            self._wait_for(lambda: self.q(css=CLASS_SELECTORS['video_init']).present, 'Video Player Initialized')
            self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['video_spinner']).visible, 'Video Buffering Completed')
            self._wait_for(lambda: self.q(css=CLASS_SELECTORS['video_controls']).visible, 'Player Controls are Visible')

    def click_button(self, button_name):
        """
        Click on a button as specified by `button_name`

        Arguments:
            button_name (str): button name

        """
        self.q(css=BUTTON_SELECTORS[button_name]).first.click()
        self.wait_for_ajax()

    @staticmethod
    def file_path(filename):
        """
        Construct file path to be uploaded to assets.

        Arguments:
            filename (str): asset filename

        """
        return os.sep.join(__file__.split(os.sep)[:-5]) + '/data/uploads/' + filename

    def upload_handout(self, handout_filename):
        """
        Upload a handout file to assets

        Arguments:
            handout_filename (str): handout file name

        """
        handout_path = self.file_path(handout_filename)

        self.click_button('upload_handout')

        self.q(css=CLASS_SELECTORS['attach_handout']).results[0].send_keys(handout_path)

        self.click_button('handout_submit')

        # confirm upload completion
        self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['upload_dialog']).present, 'Upload Handout Completed')

    def clear_handout(self):
        """
        Clear handout from settings
        """
        self.click_button('handout_clear')

    def _get_handout(self, url):
        """
        Download handout at `url`
        """
        kwargs = dict()

        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        return response.status_code < 400, response.headers

    def download_handout(self, mime_type, is_editor=False):
        """
        Download handout with mime type specified by `mime_type`

        Arguments:
            mime_type (str): mime type of handout file

        Returns:
            tuple: Handout download result.

        """
        selector = BUTTON_SELECTORS['handout_download_editor'] if is_editor else BUTTON_SELECTORS['handout_download']

        handout_url = self.q(css=selector).attrs('href')[0]
        result, headers = self._get_handout(handout_url)

        return result, headers['content-type'] == mime_type

    @property
    def is_handout_button_visible(self):
        """
        Check if handout download button is visible
        """
        return self.q(css=BUTTON_SELECTORS['handout_download']).visible

    def create_video(self):
        """
        Create a Video Component by clicking on Video button and wait for rendering to complete.
        """
        # Create video
        self.click_button('create_video')
        self.wait_for_video_component_render()

    def xblocks(self):
        """
        Tells the total number of video xblocks present on current unit page.

        Returns:
            (int): total video xblocks

        """
        return len(self.q(css='.xblock-header').filter(
            lambda el: 'xblock-header-video' in el.get_attribute('class')).results)

    def focus_caption_line(self, line_number):
        """
        Focus a caption line as specified by `line_number`

        Arguments:
            line_number (int): caption line number

        """
        caption_line_selector = ".subtitles > li[data-index='{index}']".format(index=line_number - 1)
        self.q(css=caption_line_selector).results[0].send_keys(Keys.ENTER)

    def is_caption_line_focused(self, line_number):
        """
        Check if a caption line focused

        Arguments:
            line_number (int): caption line number

        """
        caption_line_selector = ".subtitles > li[data-index='{index}']".format(index=line_number - 1)
        attributes = self.q(css=caption_line_selector).attrs('class')

        return 'focused' in attributes

    def set_settings_field_value(self, field, value):
        """
        In Advanced Tab set `field` with `value`

        Arguments:
            field (str): field name
            value (str): field value

        """
        query = '.wrapper-comp-setting > label:nth-child(1)'
        field_id = ''

        for index, _ in enumerate(self.q(css=query)):
            if field in self.q(css=query).nth(index).text[0]:
                field_id = self.q(css=query).nth(index).attrs('for')[0]
                break

        self.q(css='#{}'.format(field_id)).fill(value)

    @property
    def is_slider_range_visible(self):
        """
        Check if slider range visible.

        Returns:
            bool: slider range is visible or not

        """
        return self.q(css=CLASS_SELECTORS['slider_range']).visible
