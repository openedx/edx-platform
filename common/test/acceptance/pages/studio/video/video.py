"""
CMS Video
"""
import time
import os
import requests
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined
from ....tests.helpers import YouTubeStubConfig
from ...lms.video.video import VideoPage
from ...common.utils import wait_for_notification
from selenium.webdriver.common.keys import Keys


CLASS_SELECTORS = {
    'video_container': '.video',
    'video_init': '.is-initialized',
    'video_xmodule': '.xmodule_VideoModule',
    'video_spinner': '.video-wrapper .spinner',
    'video_controls': '.video-controls',
    'attach_asset': '.upload-dialog > input[type="file"]',
    'upload_dialog': '.wrapper-modal-window-assetupload',
    'xblock': '.add-xblock-component',
    'slider_range': '.slider-range',
    'error': '.transcripts-error-message',
    'url_inputs': '.videolist-settings-item input.input',
    'collapse_bar': '.videolist-extra-videos',
    'status': '.transcripts-message-status',
    'attach_transcript': '.file-chooser > input[type="file"]',
}

BUTTON_SELECTORS = {
    'create_video': 'button[data-category="video"]',
    'handout_download': '.video-handout.video-download-button a',
    'handout_download_editor': '.wrapper-comp-setting.file-uploader .download-action',
    'upload_asset': '.upload-action',
    'asset_submit': '.action-upload',
    'handout_clear': '.wrapper-comp-setting.file-uploader .setting-clear',
    'translations_clear': '.metadata-video-translations .setting-clear',
    'translation_add': '.wrapper-translations-settings > a',
    'import': '.setting-import',
    'download_to_edit': '.setting-download',
    'disabled_download_to_edit': '.setting-download.is-disabled',
    'upload_new_timed_transcripts': '.setting-upload',
    'replace': '.setting-replace',
    'choose': '.setting-choose',
    'use_existing': '.setting-use-existing',
    'collapse_link': '.collapse-action.collapse-setting',
}

DISPLAY_NAME = "Component Display Name"

DEFAULT_SETTINGS = [
    # basic
    [DISPLAY_NAME, 'Video', False],
    ['Default Video URL', 'http://youtu.be/3_yD_cEKoCk, , ', False],

    # advanced
    [DISPLAY_NAME, 'Video', False],
    ['Default Timed Transcript', '', False],
    ['Download Transcript Allowed', 'False', False],
    ['Downloadable Transcript URL', '', False],
    ['Show Transcript', 'True', False],
    ['Transcript Languages', '', False],
    ['Upload Handout', '', False],
    ['Video Available on Web Only', 'False', False],
    ['Video Download Allowed', 'False', False],
    ['Video File URLs', '', False],
    ['Video ID', '', False],
    ['Video Start Time', '00:00:00', False],
    ['Video Stop Time', '00:00:00', False],
    ['YouTube ID', '3_yD_cEKoCk', False],
    ['YouTube ID for .75x speed', '', False],
    ['YouTube ID for 1.25x speed', '', False],
    ['YouTube ID for 1.5x speed', '', False]
]


# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery', 'window.XModule', 'window.XBlock',
            'window.MathJax', 'window.MathJax.isReady')
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
            self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['video_spinner']).visible,
                           'Video Buffering Completed')
            self._wait_for(self.is_controls_visible, 'Player Controls are Visible')

    @wait_for_js
    def is_controls_visible(self):
        """
        Get current visibility sate of all video controls.

        Returns:
            bool: True means video controls are visible for all videos, False means video controls are not visible
            for one or more videos

        """
        return self.q(css=CLASS_SELECTORS['video_controls']).visible

    def click_button(self, button_name, index=0, require_notification=False):
        """
        Click on a button as specified by `button_name`

        Arguments:
            button_name (str): button name
            index (int): query index

        """
        self.q(css=BUTTON_SELECTORS[button_name]).nth(index).click()
        if require_notification:
            wait_for_notification(self)
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
        self.upload_asset(handout_filename)

    def upload_asset(self, asset_filename, asset_type='handout', index=0):
        """
        Upload a asset file to assets

        Arguments:
            asset_filename (str): asset file name
            asset_type (str): one of `handout`, `transcript`
            index (int): query index

        """
        asset_file_path = self.file_path(asset_filename)
        self.click_button('upload_asset', index)
        self.q(css=CLASS_SELECTORS['attach_asset']).results[0].send_keys(asset_file_path)
        # Only srt format transcript files can be uploaded, If an error
        # occurs due to incorrect transcript file we will return from here
        if asset_type == 'transcript' and self.q(css='#upload_error').present:
            return
        self.click_button('asset_submit')
        # confirm upload completion
        self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['upload_dialog']).present, 'Upload Completed')

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
        Create a Video Component by clicking on Video button and wait for rendering completion.
        """
        # Create video
        self.click_button('create_video', require_notification=True)
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
        caption_line_selector = ".subtitles li[data-index='{index}']".format(index=line_number - 1)
        self.q(css=caption_line_selector).results[0].send_keys(Keys.ENTER)

    def is_caption_line_focused(self, line_number):
        """
        Check if a caption line focused

        Arguments:
            line_number (int): caption line number

        """
        caption_line_selector = ".subtitles li[data-index='{index}']".format(index=line_number - 1)
        attributes = self.q(css=caption_line_selector).attrs('class')

        return 'focused' in attributes

    @property
    def is_slider_range_visible(self):
        """
        Return True if slider range is visible.
        """
        return self.q(css=CLASS_SELECTORS['slider_range']).visible

    def verify_settings(self):
        """
        Verify that video component has correct default settings.
        """
        query = '.wrapper-comp-setting'
        settings = self.q(css=query).results
        if len(DEFAULT_SETTINGS) != len(settings):
            return False

        for counter, setting in enumerate(settings):
            is_verified = self._verify_setting_entry(setting,
                                                     DEFAULT_SETTINGS[counter][0],
                                                     DEFAULT_SETTINGS[counter][1])

            if not is_verified:
                return is_verified

        return True

    @staticmethod
    def _verify_setting_entry(setting, field_name, field_value):
        """
        Verify a `setting` entry.

        Arguments:
            setting (WebElement): Selenium WebElement
            field_name (str): Name of field
            field_value (str): Value of field

        Returns:
            bool: Does `setting` have correct value.

        """
        if field_name != setting.find_element_by_class_name('setting-label').get_attribute('innerHTML'):
            return False

        # Get class attribute values
        classes = setting.get_attribute('class').split()
        list_type_classes = ['metadata-list-enum', 'metadata-dict', 'metadata-video-translations']
        is_list_type = any(list_type in classes for list_type in list_type_classes)

        if is_list_type:
            current_value = ', '.join(
                ele.get_attribute('value') for ele in setting.find_elements_by_class_name('list-settings-item'))
        elif 'metadata-videolist-enum' in setting.get_attribute('class'):
            current_value = ', '.join(item.find_element_by_tag_name('input').get_attribute('value') for item in
                                      setting.find_elements_by_class_name('videolist-settings-item'))
        else:
            current_value = setting.find_element_by_class_name('setting-input').get_attribute('value')

        if field_value != current_value:
            return False

        # Clear button should be visible(active class is present) for
        # every setting that don't have 'metadata-videolist-enum' class
        if 'metadata-videolist-enum' not in setting.get_attribute('class'):
            setting_clear_button = setting.find_elements_by_class_name('setting-clear')[0]
            if 'active' not in setting_clear_button.get_attribute('class'):
                return False

        return True

    def set_field_value(self, field_name, field_value, field_type='input'):
        """
        Set settings input `field` with `value`

        Arguments:
            field_name (str): Name of field
            field_value (str): Name of value
            field_type (str): `input`, `select` etc(more to be added later)

        """
        query = '.wrapper-comp-setting > label:nth-child(1)'
        field_id = ''

        if field_type == 'input':
            for index, _ in enumerate(self.q(css=query)):
                if field_name in self.q(css=query).nth(index).text[0]:
                    field_id = self.q(css=query).nth(index).attrs('for')[0]
                    break

            self.q(css='#{}'.format(field_id)).fill(field_value)
        elif field_type == 'select':
            self.q(css='select[name="{0}"] option[value="{1}"]'.format(field_name, field_value)).first.click()

    def verify_field_value(self, field_name, field_value):
        """
        Get settings value of `field_name`

        Arguments:
            field_name (str): Name of field
            field_value (str): Name of value

        Returns:
            bool: If `field_name` has `field_value`

        """
        _, setting = self._get_setting_entry(field_name)
        return self._verify_setting_entry(setting, field_name, field_value)

    def _get_setting_entry(self, field_name):
        """
        Get setting entry of `field_name`

        Arguments:
            field_name (str): Name of field

        Returns:
            setting (WebElement): Selenium WebElement

        """
        for index, setting in enumerate(self.q(css='.wrapper-comp-setting').results):
            if setting.find_element_by_class_name('setting-label').get_attribute('innerHTML') == field_name:
                return index, setting

    def translations_count(self):
        """
        Get count of translations.
        """
        return len(self.q(css='.wrapper-translations-settings .list-settings-item').results)

    def select_translation_language(self, language_code, index=0):
        """
        Select translation language as specified by `language_code`

        Arguments:
            language_code (str):
            index (int): query index

        """
        translations_items = '.wrapper-translations-settings .list-settings-item'
        language_selector = translations_items + ' select option[value="{}"]'.format(language_code)
        self.q(css=language_selector).nth(index).click()

    def upload_translation(self, transcript_name, language_code):
        """
        Upload a translation file.

        Arguments:
            transcript_name (str):
            language_code (str):

        """
        self.click_button('translation_add')
        translations_count = self.translations_count()
        self.select_translation_language(language_code, translations_count - 1)
        self.upload_asset(transcript_name, asset_type='transcript', index=translations_count - 1)

    def replace_translation(self, old_lang_code, new_lang_code, transcript_name):
        """
        Replace a translation.

        Arguments:
            old_lang_code (str):
            new_lang_code (str):
            transcript_name (str):

        """
        language_codes = self.translations()
        index = language_codes.index(old_lang_code)
        self.select_translation_language(new_lang_code, index)
        self.upload_asset(transcript_name, asset_type='transcript', index=index)

    def translations(self):
        """
        Extract translations

        Returns:
            list: list of translation language codes

        """
        translations_selector = '.metadata-video-translations .remove-setting'
        return self.q(css=translations_selector).attrs('data-lang')

    def download_translation(self, language_code, text_to_search):
        """
        Download a translation having `language_code` and containing `text_to_search`

        Arguments:
            language_code (str): language code
            text_to_search (str): text to search in translation

        Returns:
            bool: whether download was successful

        """
        mime_type = 'application/x-subrip'
        lang_code = '/{}?'.format(language_code)
        link = [link for link in self.q(css='.download-action').attrs('href') if lang_code in link]
        result, headers, content = self._get_transcript(link[0])

        return result is True and mime_type in headers['content-type'] and text_to_search in content.decode('utf-8')

    def remove_translation(self, language_code):
        """
        Remove a translation having `language_code`

        Arguments:
            language_code (str): language code

        """
        self.q(css='.remove-action').filter(lambda el: language_code == el.get_attribute('data-lang')).click()

    @property
    def upload_status_message(self):
        """
        Get asset upload status message
        """
        return self.q(css='#upload_error').text[0]

    def captions_lines(self):
        """
        Extract partial caption lines.

        As all the captions lines are exactly same so only getting partial lines will work.
        """
        self.wait_for_captions()
        selector = '.subtitles li:nth-child({})'
        return ' '.join([self.q(css=selector.format(i)).text[0] for i in range(1, 6)])

    def set_url_field(self, url, field_number):
        """
        Set video url field in basic settings tab.

        Arguments:
            url (str): video url
            field_number (int): video url field number

        """
        if self.q(css=CLASS_SELECTORS['collapse_bar']).visible is False:
            self.click_button('collapse_link')

        self.q(css=CLASS_SELECTORS['url_inputs']).nth(field_number - 1).fill(url)
        time.sleep(DELAY)
        self.wait_for_ajax()

    def message(self, message_type):
        """
        Get video url field status/error message.

        Arguments:
            message_type(str): type(status, error) of message

        Returns:
            str: status/error message

        """
        if message_type == 'status':
            self.wait_for_element_visibility(CLASS_SELECTORS[message_type],
                                             '{} message is Visible'.format(message_type.title()))

        return self.q(css=CLASS_SELECTORS[message_type]).text[0]

    def url_field_status(self, *field_numbers):
        """
        Get video url field status(enable/disable).

        Arguments:
            url (str): video url
            field_numbers (tuple or None): field numbers to check status for, None means get status for all.
                                           tuple items will be integers and must start from 1

        Returns:
            dict: field numbers as keys and field status(bool) as values, False means a field is disabled

        """
        if field_numbers:
            index_list = [number - 1 for number in field_numbers]
        else:
            index_list = range(3)  # maximum three fields

        statuses = {}
        for index in index_list:
            status = 'is-disabled' not in self.q(css=CLASS_SELECTORS['url_inputs']).nth(index).attrs('class')[0]
            statuses[index + 1] = status

        return statuses

    def clear_field(self, index):
        """
        Clear a video url field at index specified by `index`.
        """
        self.q(css=CLASS_SELECTORS['url_inputs']).nth(index - 1).fill('')

        # Trigger an 'input' event after filling the field with an empty value.
        self.browser.execute_script(
            "$('{}:eq({})').trigger('{}')".format(CLASS_SELECTORS['url_inputs'], index, 'input'))

        time.sleep(DELAY)
        self.wait_for_ajax()

    def clear_fields(self):
        """
        Clear video url fields.
        """
        script = """
        $('{selector}')
            .prop('disabled', false)
            .removeClass('is-disabled')
            .val('')
            .trigger('input');
        """.format(selector=CLASS_SELECTORS['url_inputs'])
        self.browser.execute_script(script)
        time.sleep(DELAY)
        self.wait_for_ajax()

    def revert_field(self, field_name):
        """
        Revert a field.
        """
        _, setting = self._get_setting_entry(field_name)
        setting.find_element_by_class_name('setting-clear').click()

    def is_transcript_button_visible(self, button_name, index=0, button_text=None):
        """
        Check if a transcript related button is visible.

        Arguments:
            button_name (str): name of button
            index (int): query index
            button_text (str or None): text to match with text on a button, if None then don't match texts

        Returns:
            bool: is button visible

        """
        is_visible = self.q(css=BUTTON_SELECTORS[button_name]).nth(index).visible

        is_text_matched = True
        if button_text and button_text != self.q(css=BUTTON_SELECTORS[button_name]).nth(index).text[0]:
            is_text_matched = False

        return is_visible and is_text_matched

    def upload_transcript(self, transcript_filename):
        """
        Upload a Transcript

        Arguments:
            transcript_filename (str): name of transcript file

        """
        # Show the Browse Button
        self.browser.execute_script("$('form.file-chooser').show()")
        asset_file_path = self.file_path(transcript_filename)
        self.q(css=CLASS_SELECTORS['attach_transcript']).results[0].send_keys(asset_file_path)
        # confirm upload completion
        self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['attach_transcript']).visible, 'Upload Completed')
