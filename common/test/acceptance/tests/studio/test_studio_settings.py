# coding: utf-8
"""
Acceptance tests for Studio's Setting pages
"""


import os
from textwrap import dedent

from bok_choy.promise import EmptyPromise
from mock import patch

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.common.utils import add_enrollment_course_modes
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.studio.settings_group_configurations import GroupConfigurationsPage
from common.test.acceptance.pages.studio.utils import get_input_value
from common.test.acceptance.tests.helpers import create_user_partition_json, element_has_text
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from openedx.core.lib.tests import attr
from xmodule.partitions.partitions import Group


@attr(shard=19)
class ContentGroupConfigurationTest(StudioCourseTest):
    """
    Tests for content groups in the Group Configurations Page.
    There are tests for the experiment groups in test_studio_split_test.
    """
    def setUp(self):
        super(ContentGroupConfigurationTest, self).setUp()
        self.group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """
        Populates test course with chapter, sequential, and 1 problems.
        The problem is visible only to Group "alpha".
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def create_and_verify_content_group(self, name, existing_groups):
        """
        Creates a new content group and verifies that it was properly created.
        """
        self.assertEqual(existing_groups, len(self.group_configurations_page.content_groups))
        if existing_groups == 0:
            self.group_configurations_page.create_first_content_group()
        else:
            self.group_configurations_page.add_content_group()
        config = self.group_configurations_page.content_groups[existing_groups]
        config.name = name
        # Save the content group
        self.assertEqual(config.get_text('.action-primary'), "Create")
        self.assertFalse(config.delete_button_is_present)
        config.save()
        self.assertIn(name, config.name)
        return config

    def test_no_content_groups_by_default(self):
        """
        Scenario: Ensure that message telling me to create a new content group is
            shown when no content groups exist.
        Given I have a course without content groups
        When I go to the Group Configuration page in Studio
        Then I see "You have not created any content groups yet." message
        """
        self.group_configurations_page.visit()
        self.assertTrue(self.group_configurations_page.no_content_groups_message_is_present)
        self.assertIn(
            "You have not created any content groups yet.",
            self.group_configurations_page.no_content_groups_message_text
        )

    def test_can_create_and_edit_content_groups(self):
        """
        Scenario: Ensure that the content groups can be created and edited correctly.
        Given I have a course without content groups
        When I click button 'Add your first Content Group'
        And I set new the name and click the button 'Create'
        Then I see the new content is added and has correct data
        And I click 'New Content Group' button
        And I set the name and click the button 'Create'
        Then I see the second content group is added and has correct data
        When I edit the second content group
        And I change the name and click the button 'Save'
        Then I see the second content group is saved successfully and has the new name
        """
        self.group_configurations_page.visit()
        self.create_and_verify_content_group("New Content Group", 0)
        second_config = self.create_and_verify_content_group("Second Content Group", 1)

        # Edit the second content group
        second_config.edit()
        second_config.name = "Updated Second Content Group"
        self.assertEqual(second_config.get_text('.action-primary'), "Save")
        second_config.save()

        self.assertIn("Updated Second Content Group", second_config.name)

    def test_cannot_delete_used_content_group(self):
        """
        Scenario: Ensure that the user cannot delete used content group.
        Given I have a course with 1 Content Group
        And I go to the Group Configuration page
        When I try to delete the Content Group with name "New Content Group"
        Then I see the delete button is disabled.
        """
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Configuration alpha,',
                        'Content Group Partition',
                        [Group("0", 'alpha')],
                        scheme="cohort"
                    )
                ],
            },
        })
        problem_data = dedent("""
            <problem markdown="Simple Problem" max_attempts="" weight="">
              <p>Choose Yes.</p>
              <choiceresponse>
                <checkboxgroup>
                  <choice correct="true">Yes</choice>
                </checkboxgroup>
              </choiceresponse>
            </problem>
        """)
        vertical = self.course_fixture.get_nested_xblocks(category="vertical")[0]
        self.course_fixture.create_xblock(
            vertical.locator,
            XBlockFixtureDesc('problem', "VISIBLE TO ALPHA", data=problem_data, metadata={"group_access": {0: [0]}}),
        )
        self.group_configurations_page.visit()
        config = self.group_configurations_page.content_groups[0]
        self.assertTrue(config.delete_button_is_disabled)

    def test_can_delete_unused_content_group(self):
        """
        Scenario: Ensure that the user can delete unused content group.
        Given I have a course with 1 Content Group
        And I go to the Group Configuration page
        When I delete the Content Group with name "New Content Group"
        Then I see that there is no Content Group
        When I refresh the page
        Then I see that the content group has been deleted
        """
        self.group_configurations_page.visit()
        config = self.create_and_verify_content_group("New Content Group", 0)
        self.assertTrue(config.delete_button_is_present)

        self.assertEqual(len(self.group_configurations_page.content_groups), 1)

        # Delete content group
        config.delete()
        self.assertEqual(len(self.group_configurations_page.content_groups), 0)

        self.group_configurations_page.visit()
        self.assertEqual(len(self.group_configurations_page.content_groups), 0)

    def test_must_supply_name(self):
        """
        Scenario: Ensure that validation of the content group works correctly.
        Given I have a course without content groups
        And I create new content group without specifying a name click the button 'Create'
        Then I see error message "Content Group name is required."
        When I set a name and click the button 'Create'
        Then I see the content group is saved successfully
        """
        self.group_configurations_page.visit()
        self.group_configurations_page.create_first_content_group()
        config = self.group_configurations_page.content_groups[0]
        config.save()
        self.assertEqual(config.mode, 'edit')
        self.assertEqual("Group name is required", config.validation_message)
        config.name = "Content Group Name"
        config.save()
        self.assertIn("Content Group Name", config.name)

    def test_can_cancel_creation_of_content_group(self):
        """
        Scenario: Ensure that creation of a content group can be canceled correctly.
        Given I have a course without content groups
        When I click button 'Add your first Content Group'
        And I set new the name and click the button 'Cancel'
        Then I see that there is no content groups in the course
        """
        self.group_configurations_page.visit()
        self.group_configurations_page.create_first_content_group()
        config = self.group_configurations_page.content_groups[0]
        config.name = "Content Group"
        config.cancel()
        self.assertEqual(0, len(self.group_configurations_page.content_groups))

    def test_content_group_empty_usage(self):
        """
        Scenario: When content group is not used, ensure that the link to outline page works correctly.
        Given I have a course without content group
        And I create new content group
        Then I see a link to the outline page
        When I click on the outline link
        Then I see the outline page
        """
        self.group_configurations_page.visit()
        config = self.create_and_verify_content_group("New Content Group", 0)
        config.toggle()
        config.click_outline_anchor()

        # Waiting for the page load and verify that we've landed on course outline page
        self.outline_page.wait_for_page()


@attr(shard=17)
class EnrollmentTrackModeTest(StudioCourseTest):
    """
    Tests for the enrollment tracks section
    """

    def setUp(self, is_staff=True, test_xss=True):
        super(EnrollmentTrackModeTest, self).setUp(is_staff=is_staff)

        self.audit_track = "Audit"
        self.verified_track = "Verified"
        self.staff_user = self.user

    def test_all_course_modes_present(self):
        """
        This test is meant to ensure that all the course modes show up as groups
        on the Group configuration page within the Enrollment Tracks section.
        It also checks to make sure that the edit buttons are not available.
        """
        add_enrollment_course_modes(self.browser, self.course_id, ['audit', 'verified'])
        group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        group_configurations_page.visit()
        self.assertTrue(group_configurations_page.enrollment_track_section_present)

        # Make sure the edit buttons are not available.
        self.assertFalse(group_configurations_page.enrollment_track_edit_present)
        groups = group_configurations_page.get_enrollment_groups()
        for g in [self.audit_track, self.verified_track]:
            self.assertTrue(g in groups)

    def test_one_course_mode(self):
        """
        The purpose of this test is to ensure that when there is 1 or fewer course modes
        the enrollment track section is not shown.
        """
        add_enrollment_course_modes(self.browser, self.course_id, ['audit'])
        group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        group_configurations_page.visit()
        self.assertFalse(group_configurations_page.enrollment_track_section_present)
        groups = group_configurations_page.get_enrollment_groups()
        self.assertEqual(len(groups), 0)


@attr(shard=16)
class ContentLicenseTest(StudioCourseTest):
    """
    Tests for course-level licensing (that is, setting the license,
    for an entire course's content, to All Rights Reserved or Creative Commons)
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(ContentLicenseTest, self).setUp()
        self.outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.settings_page = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.lms_courseware = CoursewarePage(
            self.browser,
            self.course_id,
        )
        self.settings_page.visit()

    def test_empty_license(self):
        """
        When I visit the Studio settings page,
        I see that the course license is "All Rights Reserved" by default.
        Then I visit the LMS courseware page,
        and I see that the default course license is displayed.
        """
        self.assertEqual(self.settings_page.course_license, "All Rights Reserved")
        self.lms_courseware.visit()
        self.assertEqual(self.lms_courseware.course_license, "© All Rights Reserved")

    def test_arr_license(self):
        """
        When I visit the Studio settings page,
        and I set the course license to "All Rights Reserved",
        and I refresh the page,
        I see that the course license is "All Rights Reserved".
        Then I visit the LMS courseware page,
        and I see that the course license is "All Rights Reserved".
        """
        self.settings_page.course_license = "All Rights Reserved"
        self.settings_page.save_changes()
        self.settings_page.refresh_and_wait_for_load()
        self.assertEqual(self.settings_page.course_license, "All Rights Reserved")

        self.lms_courseware.visit()
        self.assertEqual(self.lms_courseware.course_license, "© All Rights Reserved")

    def test_cc_license(self):
        """
        When I visit the Studio settings page,
        and I set the course license to "Creative Commons",
        and I refresh the page,
        I see that the course license is "Creative Commons".
        Then I visit the LMS courseware page,
        and I see that the course license is "Some Rights Reserved".
        """
        self.settings_page.course_license = "Creative Commons"
        self.settings_page.save_changes()
        self.settings_page.refresh_and_wait_for_load()
        self.assertEqual(self.settings_page.course_license, "Creative Commons")

        self.lms_courseware.visit()
        # The course_license text will include a bunch of screen reader text to explain
        # the selected options
        self.assertIn("Some Rights Reserved", self.lms_courseware.course_license)


@attr('a11y')
class StudioSettingsA11yTest(StudioCourseTest):

    """
    Class to test Studio pages accessibility.
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super(StudioSettingsA11yTest, self).setUp()
        self.settings_page = SettingsPage(self.browser, self.course_info['org'], self.course_info['number'],
                                          self.course_info['run'])

    def test_studio_settings_page_a11y(self):
        """
        Check accessibility of SettingsPage.
        """
        self.settings_page.visit()
        self.settings_page.wait_for_page()

        self.settings_page.a11y_audit.config.set_rules({
            "ignore": [
                'link-href',  # TODO: AC-590
                'aria-allowed-role',  # TODO: AC-936
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'radiogroup',  # TODO:  AC-941
                'region',  # TODO: AC-932
            ],
        })

        self.settings_page.a11y_audit.check_for_accessibility_errors()


@attr('a11y')
class StudioSubsectionSettingsA11yTest(StudioCourseTest):
    """
    Class to test accessibility on the subsection settings modals.
    """

    def setUp(self):  # pylint: disable=arguments-differ
        browser = os.environ.get('SELENIUM_BROWSER', 'firefox')

        # This test will fail if run using phantomjs < 2.0, due to an issue with bind()
        # See https://github.com/ariya/phantomjs/issues/10522 for details.

        # The course_outline uses this function, and as such will not fully load when run
        # under phantomjs 1.9.8. So, to prevent this test from timing out at course_outline.visit(),
        # force the use of firefox vs the standard a11y test usage of phantomjs 1.9.8.

        # TODO: remove this block once https://openedx.atlassian.net/browse/TE-1047 is resolved.
        if browser == 'phantomjs':
            browser = 'firefox'

        with patch.dict(os.environ, {'SELENIUM_BROWSER': browser}):
            super(StudioSubsectionSettingsA11yTest, self).setUp(is_staff=True)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        course_fixture.add_advanced_settings({
            "enable_proctored_exams": {"value": "true"}
        })

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1')
                )
            )
        )

    def test_special_exams_menu_a11y(self):
        """
        Given that I am a staff member
        And I am editing settings on the special exams menu
        Then that menu is accessible
        """
        self.course_outline.visit()
        self.course_outline.open_subsection_settings_dialog()
        self.course_outline.select_advanced_tab()

        self.course_outline.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
            ],
        })
        # limit the scope of the audit to the special exams tab on the modal dialog
        self.course_outline.a11y_audit.config.set_scope(
            include=['section.edit-settings-timed-examination']
        )
        self.course_outline.a11y_audit.check_for_accessibility_errors()


@attr(shard=16)
class StudioSettingsImageUploadTest(StudioCourseTest):
    """
    Class to test course settings image uploads.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(StudioSettingsImageUploadTest, self).setUp()
        self.settings_page = SettingsPage(self.browser, self.course_info['org'], self.course_info['number'],
                                          self.course_info['run'])
        self.settings_page.visit()

        # Ensure jquery is loaded before running a jQuery
        self.settings_page.wait_for_ajax()
        # This text appears towards the end of the work that jQuery is performing on the page
        self.settings_page.wait_for_jquery_value('input#course-name:text', 'test_run')

    def test_upload_course_card_image(self):

        # upload image
        file_to_upload = 'image.jpg'
        self.settings_page.upload_image('#upload-course-image', file_to_upload)
        self.assertIn(file_to_upload, self.settings_page.get_uploaded_image_path('#course-image'))

    def test_upload_course_banner_image(self):

        # upload image
        file_to_upload = 'image.jpg'
        self.settings_page.upload_image('#upload-banner-image', file_to_upload)
        self.assertIn(file_to_upload, self.settings_page.get_uploaded_image_path('#banner-image'))

    def test_upload_course_video_thumbnail_image(self):

        # upload image
        file_to_upload = 'image.jpg'
        self.settings_page.upload_image('#upload-video-thumbnail-image', file_to_upload)
        self.assertIn(file_to_upload, self.settings_page.get_uploaded_image_path('#video-thumbnail-image'))


@attr(shard=16)
class CourseSettingsTest(StudioCourseTest):
    """
    Class to test course settings.
    """
    COURSE_START_DATE_CSS = "#course-start-date"
    COURSE_END_DATE_CSS = "#course-end-date"
    ENROLLMENT_START_DATE_CSS = "#course-enrollment-start-date"
    ENROLLMENT_END_DATE_CSS = "#course-enrollment-end-date"

    COURSE_START_TIME_CSS = "#course-start-time"
    COURSE_END_TIME_CSS = "#course-end-time"
    ENROLLMENT_START_TIME_CSS = "#course-enrollment-start-time"
    ENROLLMENT_END_TIME_CSS = "#course-enrollment-end-time"

    course_start_date = '12/20/2013'
    course_end_date = '12/26/2013'
    enrollment_start_date = '12/01/2013'
    enrollment_end_date = '12/10/2013'

    dummy_time = "15:30"

    def setUp(self, is_staff=False, test_xss=True):
        super(CourseSettingsTest, self).setUp()

        self.settings_page = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Before every test, make sure to visit the page first
        self.settings_page.visit()
        self.ensure_input_fields_are_loaded()

    def set_course_dates(self):
        """
        Set dates for the course.
        """
        dates_dictionary = {
            self.COURSE_START_DATE_CSS: self.course_start_date,
            self.COURSE_END_DATE_CSS: self.course_end_date,
            self.ENROLLMENT_START_DATE_CSS: self.enrollment_start_date,
            self.ENROLLMENT_END_DATE_CSS: self.enrollment_end_date
        }

        self.settings_page.set_element_values(dates_dictionary)

    def ensure_input_fields_are_loaded(self):
        """
        Ensures values in input fields are loaded.
        """
        EmptyPromise(
            lambda: self.settings_page.q(css='#course-organization').attrs('value')[0],
            "Waiting for input fields to be loaded"
        ).fulfill()

    def test_user_can_set_course_date(self):
        """
        Scenario: User can set course dates
        Given I have opened a new course in Studio
        When I select Schedule and Details
        And I set course dates
        And I press the "Save" notification button
        And I reload the page
        Then I see the set dates
        """

        # Set dates
        self.set_course_dates()
        # Set times
        time_dictionary = {
            self.COURSE_START_TIME_CSS: self.dummy_time,
            self.ENROLLMENT_END_TIME_CSS: self.dummy_time
        }
        self.settings_page.set_element_values(time_dictionary)
        # Save changes
        self.settings_page.save_changes()
        self.settings_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()
        css_selectors = [self.COURSE_START_DATE_CSS, self.COURSE_END_DATE_CSS,
                         self.ENROLLMENT_START_DATE_CSS, self.ENROLLMENT_END_DATE_CSS,
                         self.COURSE_START_TIME_CSS, self.ENROLLMENT_END_TIME_CSS]

        expected_values = [self.course_start_date, self.course_end_date,
                           self.enrollment_start_date, self.enrollment_end_date,
                           self.dummy_time, self.dummy_time]
        # Assert changes have been persistent.
        self.assertEqual(
            [get_input_value(self.settings_page, css_selector) for css_selector in css_selectors],
            expected_values
        )

    def test_clear_previously_set_course_dates(self):
        """
        Scenario: User can clear previously set course dates (except start date)
        Given I have set course dates
        And I clear all the dates except start
        And I press the "Save" notification button
        And I reload the page
        Then I see cleared dates
        """

        # Set dates
        self.set_course_dates()
        # Clear all dates except start date
        values_to_set = {
            self.COURSE_END_DATE_CSS: '',
            self.ENROLLMENT_START_DATE_CSS: '',
            self.ENROLLMENT_END_DATE_CSS: ''
        }
        self.settings_page.set_element_values(values_to_set)
        # Save changes and refresh the page
        self.settings_page.save_changes()
        self.settings_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()
        css_selectors = [self.COURSE_START_DATE_CSS, self.COURSE_END_DATE_CSS,
                         self.ENROLLMENT_START_DATE_CSS, self.ENROLLMENT_END_DATE_CSS]

        expected_values = [self.course_start_date, '', '', '']
        # Assert changes have been persistent.
        self.assertEqual(
            [get_input_value(self.settings_page, css_selector) for css_selector in css_selectors],
            expected_values
        )

    def test_cannot_clear_the_course_start_date(self):
        """
        Scenario: User cannot clear the course start date
        Given I have set course dates
        And I press the "Save" notification button
        And I clear the course start date
        Then I receive a warning about course start date
        And I reload the page
        And the previously set start date is shown
        """
        # Set dates
        self.set_course_dates()
        # Save changes
        self.settings_page.save_changes()
        # Get default start date
        default_start_date = get_input_value(self.settings_page, self.COURSE_START_DATE_CSS)
        # Set course start date to empty
        self.settings_page.set_element_values({self.COURSE_START_DATE_CSS: ''})
        # Make sure error message is show with appropriate message
        error_message_css = '.message-error'
        self.settings_page.wait_for_element_presence(error_message_css, 'Error message is present')
        self.assertEqual(element_has_text(self.settings_page, error_message_css,
                                          "The course must have an assigned start date."), True)
        # Refresh the page and assert start date has not changed.
        self.settings_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()
        self.assertEqual(
            get_input_value(self.settings_page, self.COURSE_START_DATE_CSS),
            default_start_date
        )

    def test_user_can_correct_course_start_date_warning(self):
        """
        Scenario: User can correct the course start date warning
        Given I have tried to clear the course start
        And I have entered a new course start date
        And I press the "Save" notification button
        Then The warning about course start date goes away
        And I reload the page
        Then my new course start date is shown
        """
        # Set course start date to empty
        self.settings_page.set_element_values({self.COURSE_START_DATE_CSS: ''})
        # Make sure we get error message
        error_message_css = '.message-error'
        self.settings_page.wait_for_element_presence(error_message_css, 'Error message is present')
        self.assertEqual(element_has_text(self.settings_page, error_message_css,
                                          "The course must have an assigned start date."), True)
        # Set new course start value
        self.settings_page.set_element_values({self.COURSE_START_DATE_CSS: self.course_start_date})
        self.settings_page.un_focus_input_field()
        # Error message disappears
        self.settings_page.wait_for_element_absence(error_message_css, 'Error message is not present')
        # Save the changes and refresh the page.
        self.settings_page.save_changes()
        self.settings_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()
        # Assert changes are persistent.
        self.assertEqual(
            get_input_value(self.settings_page, self.COURSE_START_DATE_CSS),
            self.course_start_date
        )

    def test_settings_are_only_persisted_when_saved(self):
        """
        Scenario: Settings are only persisted when saved
        Given I have set course dates
        And I press the "Save" notification button
        When I change fields
        And I reload the page
        Then I do not see the changes
        """
        # Set course dates.
        self.set_course_dates()
        # Save changes.
        self.settings_page.save_changes()
        default_value_enrollment_start_date = get_input_value(self.settings_page,
                                                              self.ENROLLMENT_START_TIME_CSS)
        # Set the value of enrollment start time and
        # reload the page without saving.
        self.settings_page.set_element_values({self.ENROLLMENT_START_TIME_CSS: self.dummy_time})
        self.settings_page.refresh_and_wait_for_load()
        self.ensure_input_fields_are_loaded()

        css_selectors = [self.COURSE_START_DATE_CSS, self.COURSE_END_DATE_CSS,
                         self.ENROLLMENT_START_DATE_CSS, self.ENROLLMENT_END_DATE_CSS,
                         self.ENROLLMENT_START_TIME_CSS]

        expected_values = [self.course_start_date, self.course_end_date,
                           self.enrollment_start_date, self.enrollment_end_date,
                           default_value_enrollment_start_date]
        # Assert that value of enrolment start time
        # is not saved.
        self.assertEqual(
            [get_input_value(self.settings_page, css_selector) for css_selector in css_selectors],
            expected_values
        )

    def test_settings_are_reset_on_cancel(self):
        """
        Scenario: Settings are reset on cancel
        Given I have set course dates
        And I press the "Save" notification button
        When I change fields
        And I press the "Cancel" notification button
        Then I do not see the changes
        """
        # Set course date
        self.set_course_dates()
        # Save changes
        self.settings_page.save_changes()
        default_value_enrollment_start_date = get_input_value(self.settings_page,
                                                              self.ENROLLMENT_START_TIME_CSS)
        # Set value but don't save it.
        self.settings_page.set_element_values({self.ENROLLMENT_START_TIME_CSS: self.dummy_time})
        self.settings_page.click_button("cancel")
        # Make sure changes are not saved after cancel.
        css_selectors = [self.COURSE_START_DATE_CSS, self.COURSE_END_DATE_CSS,
                         self.ENROLLMENT_START_DATE_CSS, self.ENROLLMENT_END_DATE_CSS,
                         self.ENROLLMENT_START_TIME_CSS]

        expected_values = [self.course_start_date, self.course_end_date,
                           self.enrollment_start_date, self.enrollment_end_date,
                           default_value_enrollment_start_date]

        self.assertEqual(
            [get_input_value(self.settings_page, css_selector) for css_selector in css_selectors],
            expected_values
        )

    def test_confirmation_is_shown_on_save(self):
        """
        Scenario: Confirmation is shown on save
        Given I have opened a new course in Studio
        When I select Schedule and Details
        And I change the "<field>" field to "<value>"
        And I press the "Save" notification button
        Then I see a confirmation that my changes have been saved
        """
        # Set date
        self.settings_page.set_element_values({self.COURSE_START_DATE_CSS: self.course_start_date})
        # Confirmation is showed upon save.
        # Save_changes function ensures that save
        # confirmation is shown.
        self.settings_page.save_changes()

    def test_changes_in_course_overview_show_a_confirmation(self):
        """
        Scenario: Changes in Course Overview show a confirmation
        Given I have opened a new course in Studio
        When I select Schedule and Details
        And I change the course overview
        And I press the "Save" notification button
        Then I see a confirmation that my changes have been saved
        """
        # Change the value of course overview
        self.settings_page.change_course_description('Changed overview')
        # Save changes
        # Save_changes function ensures that save
        # confirmation is shown.
        self.settings_page.save_changes()

    def test_user_cannot_save_invalid_settings(self):
        """
        Scenario: User cannot save invalid settings
        Given I have opened a new course in Studio
        When I select Schedule and Details
        And I change the "Course Start Date" field to ""
        Then the save notification button is disabled
        """
        # Change the course start date to invalid date.
        self.settings_page.set_element_values({self.COURSE_START_DATE_CSS: ''})
        # Confirm that save button is disabled.
        self.assertEqual(self.settings_page.is_element_present(".action-primary.action-save.is-disabled"), True)
