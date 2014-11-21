"""
Acceptance tests for Studio's Settings Details pages
"""
from acceptance.tests.studio.base_studio_test import StudioCourseTest

from ...pages.studio.settings import SettingsPage


class SettingsMilestonesTest(StudioCourseTest):
    """
    Tests for milestones feature in Studio's settings tab
    """
    def setUp(self):
        super(SettingsMilestonesTest, self).setUp()
        self.settings_detail = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Before every test, make sure to visit the page first
        self.settings_detail.visit()
        self.assertTrue(self.settings_detail.is_browser_on_page())

    def test_page_has_prerequisite_field(self):
        """
        Test to make sure page has pre-requisite course field if milestones app is enabled.
        """

        self.assertTrue(self.settings_detail.pre_requisite_course.present)
