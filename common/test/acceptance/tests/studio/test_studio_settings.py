# coding: utf-8
"""
Acceptance tests for Studio's Setting pages
"""
from __future__ import unicode_literals
import os

from mock import patch
from nose.plugins.attrib import attr

from base_studio_test import StudioCourseTest
from bok_choy.promise import EmptyPromise
from ...fixtures.course import XBlockFixtureDesc
from ..helpers import create_user_partition_json
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.settings import SettingsPage
from ...pages.studio.settings_advanced import AdvancedSettingsPage
from ...pages.studio.settings_group_configurations import GroupConfigurationsPage
from ...pages.lms.courseware import CoursewarePage
from textwrap import dedent
from xmodule.partitions.partitions import Group


@attr('shard_8')
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
        EmptyPromise(
            lambda: self.outline_page.is_browser_on_page(), "loaded page {!r}".format(self.outline_page),
            timeout=30
        ).fulfill()


@attr('shard_8')
class AdvancedSettingsValidationTest(StudioCourseTest):
    """
    Tests for validation feature in Studio's advanced settings tab
    """
    def setUp(self):
        super(AdvancedSettingsValidationTest, self).setUp()
        self.advanced_settings = AdvancedSettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.type_fields = ['Course Display Name', 'Advanced Module List', 'Discussion Topic Mapping',
                            'Maximum Attempts', 'Course Announcement Date']

        # Before every test, make sure to visit the page first
        self.advanced_settings.visit()
        self.assertTrue(self.advanced_settings.is_browser_on_page())

    def test_modal_shows_one_validation_error(self):
        """
        Test that advanced settings don't save if there's a single wrong input,
        and that it shows the correct error message in the modal.
        """

        # Feed an integer value for String field.
        # .set method saves automatically after setting a value
        course_display_name = self.advanced_settings.get('Course Display Name')
        self.advanced_settings.set('Course Display Name', 1)
        self.advanced_settings.wait_for_modal_load()

        # Test Modal
        self.check_modal_shows_correct_contents(['Course Display Name'])
        self.advanced_settings.refresh_and_wait_for_load()

        self.assertEquals(
            self.advanced_settings.get('Course Display Name'),
            course_display_name,
            'Wrong input for Course Display Name must not change its value'
        )

    def test_modal_shows_multiple_validation_errors(self):
        """
        Test that advanced settings don't save with multiple wrong inputs
        """

        # Save original values and feed wrong inputs
        original_values_map = self.get_settings_fields_of_each_type()
        self.set_wrong_inputs_to_fields()
        self.advanced_settings.wait_for_modal_load()

        # Test Modal
        self.check_modal_shows_correct_contents(self.type_fields)
        self.advanced_settings.refresh_and_wait_for_load()

        for key, val in original_values_map.iteritems():
            self.assertEquals(
                self.advanced_settings.get(key),
                val,
                'Wrong input for Advanced Settings Fields must not change its value'
            )

    def test_undo_changes(self):
        """
        Test that undo changes button in the modal resets all settings changes
        """

        # Save original values and feed wrong inputs
        original_values_map = self.get_settings_fields_of_each_type()
        self.set_wrong_inputs_to_fields()

        # Let modal popup
        self.advanced_settings.wait_for_modal_load()

        # Click Undo Changes button
        self.advanced_settings.undo_changes_via_modal()

        # Check that changes are undone
        for key, val in original_values_map.iteritems():
            self.assertEquals(
                self.advanced_settings.get(key),
                val,
                'Undoing Should revert back to original value'
            )

    def test_manual_change(self):
        """
        Test that manual changes button in the modal keeps settings unchanged
        """
        inputs = {"Course Display Name": 1,
                  "Advanced Module List": 1,
                  "Discussion Topic Mapping": 1,
                  "Maximum Attempts": '"string"',
                  "Course Announcement Date": '"string"',
                  }

        self.set_wrong_inputs_to_fields()
        self.advanced_settings.wait_for_modal_load()
        self.advanced_settings.trigger_manual_changes()

        # Check that the validation modal went away.
        self.assertFalse(self.advanced_settings.is_validation_modal_present())

        # Iterate through the wrong values and make sure they're still displayed
        for key, val in inputs.iteritems():
            self.assertEquals(
                str(self.advanced_settings.get(key)),
                str(val),
                'manual change should keep: ' + str(val) + ', but is: ' + str(self.advanced_settings.get(key))
            )

    def check_modal_shows_correct_contents(self, wrong_settings_list):
        """
        Helper function that checks if the validation modal contains correct
        error messages.
        """
        # Check presence of modal
        self.assertTrue(self.advanced_settings.is_validation_modal_present())

        # List of wrong settings item & what is presented in the modal should be the same
        error_item_names = self.advanced_settings.get_error_item_names()
        self.assertEqual(set(wrong_settings_list), set(error_item_names))

        error_item_messages = self.advanced_settings.get_error_item_messages()
        self.assertEqual(len(error_item_names), len(error_item_messages))

    def get_settings_fields_of_each_type(self):
        """
        Get one of each field type:
           - String: Course Display Name
           - List: Advanced Module List
           - Dict: Discussion Topic Mapping
           - Integer: Maximum Attempts
           - Date: Course Announcement Date
        """
        return {
            "Course Display Name": self.advanced_settings.get('Course Display Name'),
            "Advanced Module List": self.advanced_settings.get('Advanced Module List'),
            "Discussion Topic Mapping": self.advanced_settings.get('Discussion Topic Mapping'),
            "Maximum Attempts": self.advanced_settings.get('Maximum Attempts'),
            "Course Announcement Date": self.advanced_settings.get('Course Announcement Date'),
        }

    def set_wrong_inputs_to_fields(self):
        """
        Set wrong values for the chosen fields
        """
        self.advanced_settings.set_values(
            {
                "Course Display Name": 1,
                "Advanced Module List": 1,
                "Discussion Topic Mapping": 1,
                "Maximum Attempts": '"string"',
                "Course Announcement Date": '"string"',
            }
        )

    def test_only_expected_fields_are_displayed(self):
        """
        Scenario: The Advanced Settings screen displays settings/fields not specifically hidden from
        view by a developer.
        Given I have a set of CourseMetadata fields defined for the course
        When I view the Advanced Settings screen for the course
        The total number of fields displayed matches the number I expect
        And the actual fields displayed match the fields I expect to see
        """
        expected_fields = self.advanced_settings.expected_settings_names
        displayed_fields = self.advanced_settings.displayed_settings_names
        self.assertEquals(set(displayed_fields), set(expected_fields))


@attr('shard_1')
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

        # There are several existing color contrast errors on this page,
        # we will ignore this error in the test until we fix them.
        self.settings_page.a11y_audit.config.set_rules({
            "ignore": [
                'color-contrast',  # TODO: AC-225
                'link-href',  # TODO: AC-226
                'nav-aria-label',  # TODO: AC-227
                'icon-aria-hidden',  # TODO: AC-229
            ],
        })

        # TODO: Figure out how to get CodeMirror to pass accessibility testing
        # We use the CodeMirror Javascript library to
        # add code editing to a number of textarea elements
        # on this page. CodeMirror generates markup that does
        # not pass our accessibility testing rules.
        self.settings_page.a11y_audit.config.set_scope(
            exclude=['.CodeMirror textarea']
        )

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

        # limit the scope of the audit to the special exams tab on the modal dialog
        self.course_outline.a11y_audit.config.set_scope(
            include=['section.edit-settings-timed-examination']
        )
        self.course_outline.a11y_audit.check_for_accessibility_errors()


class StudioSettingsImageUploadTest(StudioCourseTest):
    """
    Class to test course settings image uploads.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(StudioSettingsImageUploadTest, self).setUp()
        self.settings_page = SettingsPage(self.browser, self.course_info['org'], self.course_info['number'],
                                          self.course_info['run'])
        # from nose.tools import set_trace; set_trace()
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
