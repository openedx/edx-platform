"""
Acceptance tests for Studio's Settings Details pages
"""

from ...pages.studio.settings import SettingsPage
from ...pages.studio.overview import CourseOutlinePage
from ...tests.studio.base_studio_test import StudioCourseTest
from ..helpers import (
    element_has_text,
)


class SettingsMilestonesTest(StudioCourseTest):
    """
    Tests for milestones feature in Studio's settings tab
    """
    def setUp(self, is_staff=True):
        super(SettingsMilestonesTest, self).setUp(is_staff=True)
        self.number = self.course_info['number']
        self.settings_detail = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.number,
            self.course_info['run']
        )

        # Before every test, make sure to visit the page first
        self.settings_detail.visit()
        self.assertTrue(self.settings_detail.is_browser_on_page())

    def test_page_has_enable_entrance_exam_field(self):
        """
        Test to make sure page has 'enable entrance exam' field.
        """
        self.assertTrue(self.settings_detail.entrance_exam_field.present)

    def test_enable_entrance_exam_for_course(self):
        """
        Test that entrance exam should be created after checking the 'enable entrance exam' checkbox.
        """
        self.settings_detail.entrance_exam_field.click()
        self.settings_detail.save_changes()

        # getting the course outline page.
        course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.number, self.course_info['run']
        )
        course_outline_page.visit()
        course_outline_page.wait_for_page()
        self.assertTrue(course_outline_page.is_browser_on_page())

        # title with text 'Entrance Exam' should be present on page.
        self.assertTrue(element_has_text(
            page=course_outline_page,
            css_selector='span.section-title',
            text='Entrance Exam'
        ))

        # Delete the currently created entrance exam.
        self.settings_detail.visit()
        self.settings_detail.entrance_exam_field.click()
        self.settings_detail.save_changes()

        course_outline_page.visit()
        course_outline_page.wait_for_page()
        self.assertTrue(course_outline_page.is_browser_on_page())

        self.assertFalse(element_has_text(
            page=course_outline_page,
            css_selector='span.section-title',
            text='Entrance Exam'
        ))
