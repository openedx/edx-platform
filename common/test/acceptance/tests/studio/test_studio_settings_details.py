"""
Acceptance tests for Studio's Settings Details pages
"""
from datetime import datetime, timedelta
from nose.plugins.attrib import attr
from unittest import skip

from .base_studio_test import StudioCourseTest
from ...fixtures.config import ConfigModelFixture
from ...fixtures.course import CourseFixture
from ...pages.studio.settings import SettingsPage
from ...pages.studio.overview import CourseOutlinePage
from ...tests.studio.base_studio_test import StudioCourseTest
from ..helpers import (
    generate_course_key,
    select_option_by_value,
    is_option_value_selected,
    element_has_text,
)


@attr('shard_4')
class StudioSettingsDetailsTest(StudioCourseTest):
    """Base class for settings and details page tests."""

    def setUp(self, is_staff=True):
        super(StudioSettingsDetailsTest, self).setUp(is_staff=is_staff)
        self.settings_detail = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Before every test, make sure to visit the page first
        self.settings_detail.visit()
        self.assertTrue(self.settings_detail.is_browser_on_page())


@attr('shard_4')
class SettingsMilestonesTest(StudioSettingsDetailsTest):
    """
    Tests for milestones feature in Studio's settings tab
    """
    def test_page_has_prerequisite_field(self):
        """
        Test to make sure page has pre-requisite course field if milestones app is enabled.
        """

        self.assertTrue(self.settings_detail.pre_requisite_course_options)

    def test_prerequisite_course_save_successfully(self):
        """
         Scenario: Selecting course from Pre-Requisite course drop down save the selected course as pre-requisite
         course.
            Given that I am on the Schedule & Details page on studio
            When I select an item in pre-requisite course drop down and click Save Changes button
            Then My selected item should be saved as pre-requisite course
            And My selected item should be selected after refreshing the page.'
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

        # Refresh the page to load the new course fixture and populate the prrequisite course dropdown
        # Then select the prerequisite course and save the changes
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        select_option_by_value(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        )
        self.settings_detail.save_changes()
        self.assertEqual(
            'Your changes have been saved.',
            self.settings_detail.alert_confirmation_title.text
        )

        # Refresh the page again and confirm the prerequisite course selection is properly reflected
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        self.assertTrue(is_option_value_selected(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        ))

        # Set the prerequisite course back to None and save the changes
        select_option_by_value(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=''
        )
        self.settings_detail.save_changes()
        self.assertEqual(
            'Your changes have been saved.',
            self.settings_detail.alert_confirmation_title.text
        )

        # Refresh the page again to confirm the None selection is properly reflected
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        self.assertTrue(is_option_value_selected(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=''
        ))

        # Re-pick the prerequisite course and confirm no errors are thrown (covers a discovered bug)
        select_option_by_value(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        )
        self.settings_detail.save_changes()
        self.assertEqual(
            'Your changes have been saved.',
            self.settings_detail.alert_confirmation_title.text
        )

        # Refresh the page again to confirm the prerequisite course selection is properly reflected
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        dropdown_status = is_option_value_selected(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        )
        self.assertTrue(dropdown_status)

    def test_page_has_enable_entrance_exam_field(self):
        """
        Test to make sure page has 'enable entrance exam' field.
        """
        self.assertTrue(self.settings_detail.entrance_exam_field)

    @skip('Passes in devstack, passes individually in Jenkins, fails in suite in Jenkins.')
    def test_enable_entrance_exam_for_course(self):
        """
        Test that entrance exam should be created after checking the 'enable entrance exam' checkbox.
        And also that the entrance exam is destroyed after deselecting the checkbox.
        """
        self.settings_detail.require_entrance_exam(required=True)
        self.settings_detail.save_changes()

        # getting the course outline page.
        course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
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

    def test_entrance_exam_has_unit_button(self):
        """
        Test that entrance exam should be created after checking the 'enable entrance exam' checkbox.
        And user has option to add units only instead of any Subsection.
        """
        self.settings_detail.require_entrance_exam(required=True)
        self.settings_detail.save_changes()

        # getting the course outline page.
        course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )
        course_outline_page.visit()
        course_outline_page.wait_for_ajax()

        # button with text 'New Unit' should be present.
        self.assertTrue(element_has_text(
            page=course_outline_page,
            css_selector='.add-item a.button-new',
            text='New Unit'
        ))

        # button with text 'New Subsection' should not be present.
        self.assertFalse(element_has_text(
            page=course_outline_page,
            css_selector='.add-item a.button-new',
            text='New Subsection'
        ))


@attr('shard_4')
class CoursePacingTest(StudioSettingsDetailsTest):
    """Tests for setting a course to self-paced."""

    def populate_course_fixture(self, __):
        ConfigModelFixture('/config/self_paced', {'enabled': True}).install()
        # Set the course start date to tomorrow in order to allow setting pacing
        self.course_fixture.add_course_details({'start_date': datetime.now() + timedelta(days=1)})

    def test_default_instructor_paced(self):
        """
        Test that the 'instructor paced' button is checked by default.
        """
        self.assertEqual(self.settings_detail.course_pacing, 'Instructor-Paced')

    def test_self_paced(self):
        """
        Test that the 'self-paced' button is checked for a self-paced
        course.
        """
        self.course_fixture.add_course_details({
            'self_paced': True
        })
        self.course_fixture.configure_course()
        self.settings_detail.refresh_page()
        self.assertEqual(self.settings_detail.course_pacing, 'Self-Paced')

    def test_set_self_paced(self):
        """
        Test that the self-paced option is persisted correctly.
        """
        self.settings_detail.course_pacing = 'Self-Paced'
        self.settings_detail.save_changes()
        self.settings_detail.refresh_page()
        self.assertEqual(self.settings_detail.course_pacing, 'Self-Paced')

    def test_toggle_pacing_after_course_start(self):
        """
        Test that course authors cannot toggle the pacing of their course
        while the course is running.
        """
        self.course_fixture.add_course_details({'start_date': datetime.now()})
        self.course_fixture.configure_course()
        self.settings_detail.refresh_page()
        self.assertTrue(self.settings_detail.course_pacing_disabled())
        self.assertIn('Course pacing cannot be changed', self.settings_detail.course_pacing_disabled_text)
