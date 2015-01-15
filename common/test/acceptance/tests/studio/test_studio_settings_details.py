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

    def test_enable_entrance_exam_for_course(self):
        """
        Test that entrance exam should be created after checking the 'enable entrance exam' checkbox.
        And also that the entrance exam is destroyed after deselecting the checkbox.
        """
        self.settings_detail.require_entrance_exam(required=True)
        self.settings_detail.save_changes()

        # getting the course outline page.
        course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.number, self.course_info['run']
        )
        course_outline_page.visit()

        # title with text 'Entrance Exam' should be present on page.
        self.assertTrue(element_has_text(
            page=course_outline_page,
            css_selector='span.section-title',
            text='Entrance Exam'
        ))

        # Delete the currently created entrance exam.
        self.settings_detail.visit()
        self.settings_detail.require_entrance_exam(required=False)
        self.settings_detail.save_changes()

        course_outline_page.visit()
        self.assertFalse(element_has_text(
            page=course_outline_page,
            css_selector='span.section-title',
            text='Entrance Exam'
        ))
