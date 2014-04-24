"""
Video player in the courseware.
"""

from selenium.webdriver.common.action_chains import ActionChains
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined


SELECTORS = {
    'status': '.video-feedback',
    'progress': '.video-progress',
}


class VideoGradeMixin(object):
    """
    Video player in the courseware.
    """

    def is_status_message_shown(self, video_display_name=None):
        """
        Checks if video player status message shown.

        Arguments:
            video_display_name (str or None): Display name of a Video.

        Returns:
            bool: Tells about status message visibility.

        """
        selector = self.get_element_selector(video_display_name, SELECTORS['status'])
        return self.q(css=selector).present

    def status_message_text(self, video_display_name=None):
        """
        Extract video player status message text.

        Arguments:
            video_display_name (str or None): Display name of a Video.

        Returns:
            str: Status message text.

        """
        selector = self.get_element_selector(video_display_name, SELECTORS['status'])
        return self.q(css=selector).text[0]

    def is_progress_message_shown(self, video_display_name=None):
        """
        Checks if video player progress message shown.

        Arguments:
            video_display_name (str or None): Display name of a Video.

        Returns:
            bool: Tells about progress message visibility.

        """
        selector = self.get_element_selector(video_display_name, SELECTORS['progress'])
        return self.q(css=selector).visible

    def progress_message_text(self, video_display_name=None):
        """
        Extract video player progress message text.

        Arguments:
            video_display_name (str or None): Display name of a Video.

        Returns:
            str: Status message text.

        """
        selector = self.get_element_selector(video_display_name, SELECTORS['progress'])
        return self.q(css=selector).text[0]

    def wait_for_status_message(self, video_display_name=None):
        """
        Wait until status message occurs.

        Arguments:
            video_display_name (str or None): Display name of a Video.

        """
        def _check_message():
            """
            Event occurred promise check.

            Returns:
                bool: is event occurred.

            """
            return self.q(css=SELECTORS['status']).present

        EmptyPromise(_check_message, 'Message is shown', timeout=200).fulfill()
