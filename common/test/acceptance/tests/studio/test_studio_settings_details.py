"""
Acceptance tests for Studio's Settings Details pages
"""
from acceptance.tests.studio.base_studio_test import StudioCourseTest
from ...fixtures.course import CourseFixture
from ..helpers import (
    generate_course_key,
    select_ddl_by_value,
    is_ddl_value_selected
)

from ...pages.studio.settings import SettingsPage


class SettingsMilestonesTest(StudioCourseTest):
    """
    Tests for milestones feature in Studio's settings tab
    """
    def setUp(self):
        super(SettingsMilestonesTest, self).setUp(is_staff=True)
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

    def test_prerequisite_course_save_successfully(self):
        """
        Test to make sure pre-requisite course field successfully saving the changes.
        """
        course_number = self.unique_id
        CourseFixture(
            org='test_org',
            number=course_number,
            run='test_run',
            display_name='Test Course' + course_number
        ).install()

        pre_requisite_course_key = generate_course_key(
            org='test_org',
            number=course_number,
            run='test_run'
        )
        pre_requisite_course_id = unicode(pre_requisite_course_key)

        # refreshing the page after creating a course fixture, in order reload the pre requisite course drop down.
        self.settings_detail.refresh_page()
        select_ddl_by_value(browser_query=self.settings_detail.pre_requisite_course, value=pre_requisite_course_id)

        # trigger the save changes button.
        self.settings_detail.save_changes()

        self.assertTrue('Your changes have been saved.' in self.settings_detail.browser.page_source)
        self.settings_detail.refresh_page()
        self.assertTrue(is_ddl_value_selected(browser_query=self.settings_detail.pre_requisite_course, value=pre_requisite_course_id))

        # now reset/update the pre requisite course to none
        select_ddl_by_value(browser_query=self.settings_detail.pre_requisite_course, value='')

        # trigger the save changes button.
        self.settings_detail.save_changes()
        self.assertTrue('Your changes have been saved.' in self.settings_detail.browser.page_source)
        self.assertTrue(is_ddl_value_selected(browser_query=self.settings_detail.pre_requisite_course, value=''))
