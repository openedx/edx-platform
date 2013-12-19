"""
Very simple test case to verify bok-choy integration.
"""

from bok_choy.web_app_test import WebAppTest
from edxapp_pages.lms.info import InfoPage


class InfoPageTest(WebAppTest):
    """
    Test that the top-level pages in the LMS load.
    """

    @property
    def page_object_classes(self):
        return [InfoPage]

    def test_info(self):
        for section_name in InfoPage.sections():
            self.ui.visit('lms.info', section=section_name)
