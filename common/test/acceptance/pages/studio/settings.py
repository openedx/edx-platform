# coding: utf-8
"""
Course Schedule and Details Settings page.
"""


from bok_choy.javascript import requirejs

from common.test.acceptance.pages.studio.course_page import CoursePage
from common.test.acceptance.pages.studio.users import wait_for_ajax_or_reload


@requirejs('js/factories/settings')
class SettingsPage(CoursePage):
    """
    Course Schedule and Details Settings page.
    """

    url_path = "settings/details"
    upload_image_browse_button_selector = 'form.upload-dialog input[type=file]'
    upload_image_upload_button_selector = '.modal-actions li:nth-child(1) a'
    upload_image_popup_window_selector = '.assetupload-modal'

    ################
    # Helpers
    ################
    def is_browser_on_page(self):
        wait_for_ajax_or_reload(self.browser)
        return self.q(css='body.view-settings').visible
