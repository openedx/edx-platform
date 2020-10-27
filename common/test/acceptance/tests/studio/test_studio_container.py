"""
Acceptance tests for Studio related to the container page.
The container page is used both for displaying units, and
for displaying containers within units.
"""
import datetime

import ddt

from base_studio_test import ContainerBase
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.create_mode import ModeCreationPage
from common.test.acceptance.pages.lms.staff_view import StaffCoursewarePage
from common.test.acceptance.pages.studio.xblock_editor import XBlockEditorView, XBlockVisibilityEditorView
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.html_component_editor import HtmlXBlockEditorView
from common.test.acceptance.pages.studio.move_xblock import MoveModalView
from common.test.acceptance.pages.studio.utils import add_discussion
from common.test.acceptance.tests.helpers import create_user_partition_json
from openedx.core.lib.tests import attr
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID, MINIMUM_STATIC_PARTITION_ID, Group


class NestedVerticalTest(ContainerBase):

    def populate_course_fixture(self, course_fixture):
        """
        Sets up a course structure with nested verticals.
        """
        self.container_title = ""
        self.group_a = "Group A"
        self.group_b = "Group B"
        self.group_empty = "Group Empty"
        self.group_a_item_1 = "Group A Item 1"
        self.group_a_item_2 = "Group A Item 2"
        self.group_b_item_1 = "Group B Item 1"
        self.group_b_item_2 = "Group B Item 2"

        self.group_a_handle = 0
        self.group_a_item_1_handle = 1
        self.group_a_item_2_handle = 2
        self.group_empty_handle = 3
        self.group_b_handle = 4
        self.group_b_item_1_handle = 5
        self.group_b_item_2_handle = 6

        self.group_a_item_1_action_index = 0
        self.group_a_item_2_action_index = 1

        self.duplicate_label = "Duplicate of '{0}'"
        self.discussion_label = "Discussion"

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('vertical', 'Test Container').add_children(
                            XBlockFixtureDesc('vertical', 'Group A').add_children(
                                XBlockFixtureDesc('html', self.group_a_item_1),
                                XBlockFixtureDesc('html', self.group_a_item_2)
                            ),
                            XBlockFixtureDesc('vertical', 'Group Empty'),
                            XBlockFixtureDesc('vertical', 'Group B').add_children(
                                XBlockFixtureDesc('html', self.group_b_item_1),
                                XBlockFixtureDesc('html', self.group_b_item_2)
                            )
                        )
                    )
                )
            )
        )


@attr(shard=1)
class AddComponentTest(NestedVerticalTest):
    """
    Tests of adding a component to the container page.
    """

    def add_and_verify(self, menu_index, expected_ordering):
        self.do_action_and_verify(
            lambda (container): add_discussion(container, menu_index),
            expected_ordering
        )

    def test_add_component_in_group(self):
        group_b_menu = 2

        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2, self.discussion_label]},
                             {self.group_empty: []}]
        self.add_and_verify(group_b_menu, expected_ordering)

    def test_add_component_in_empty_group(self):
        group_empty_menu = 1

        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: [self.discussion_label]}]
        self.add_and_verify(group_empty_menu, expected_ordering)

    def test_add_component_in_container(self):
        container_menu = 3

        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b, self.discussion_label]},
                             {self.group_a: [self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.add_and_verify(container_menu, expected_ordering)


@attr(shard=1)
class DuplicateComponentTest(NestedVerticalTest):
    """
    Tests of duplicating a component on the container page.
    """

    def duplicate_and_verify(self, source_index, expected_ordering):
        self.do_action_and_verify(
            lambda (container): container.duplicate(source_index),
            expected_ordering
        )

    def test_duplicate_first_in_group(self):
        duplicate_label = self.duplicate_label.format(self.group_a_item_1)
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_1, duplicate_label, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.duplicate_and_verify(self.group_a_item_1_action_index, expected_ordering)

    def test_duplicate_second_in_group(self):
        duplicate_label = self.duplicate_label.format(self.group_a_item_2)
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_1, self.group_a_item_2, duplicate_label]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.duplicate_and_verify(self.group_a_item_2_action_index, expected_ordering)

    def test_duplicate_the_duplicate(self):
        first_duplicate_label = self.duplicate_label.format(self.group_a_item_1)
        second_duplicate_label = self.duplicate_label.format(first_duplicate_label)

        expected_ordering = [
            {self.container_title: [self.group_a, self.group_empty, self.group_b]},
            {self.group_a: [self.group_a_item_1, first_duplicate_label, second_duplicate_label, self.group_a_item_2]},
            {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
            {self.group_empty: []}
        ]

        def duplicate_twice(container):
            container.duplicate(self.group_a_item_1_action_index)
            container.duplicate(self.group_a_item_1_action_index + 1)

        self.do_action_and_verify(duplicate_twice, expected_ordering)


@attr(shard=1)
class DeleteComponentTest(NestedVerticalTest):
    """
    Tests of deleting a component from the container page.
    """

    def delete_and_verify(self, source_index, expected_ordering):
        self.do_action_and_verify(
            lambda (container): container.delete(source_index),
            expected_ordering
        )

    def test_delete_first_in_group(self):
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]

        # Group A itself has a delete icon now, so item_1 is index 1 instead of 0.
        group_a_item_1_delete_index = 1
        self.delete_and_verify(group_a_item_1_delete_index, expected_ordering)


@attr(shard=16)
class EditContainerTest(NestedVerticalTest):
    """
    Tests of editing a container.
    """

    def modify_display_name_and_verify(self, component):
        """
        Helper method for changing a display name.
        """
        modified_name = 'modified'
        self.assertNotEqual(component.name, modified_name)
        component.edit()
        component_editor = XBlockEditorView(self.browser, component.locator)
        component_editor.set_field_value_and_save('Display Name', modified_name)
        self.assertEqual(component.name, modified_name)

    def test_edit_container_on_unit_page(self):
        """
        Test the "edit" button on a container appearing on the unit page.
        """
        unit = self.go_to_unit_page()
        component = unit.xblocks[1]
        self.modify_display_name_and_verify(component)

    def test_edit_container_on_container_page(self):
        """
        Test the "edit" button on a container appearing on the container page.
        """
        container = self.go_to_nested_container_page()
        self.modify_display_name_and_verify(container)


class BaseGroupConfigurationsTest(ContainerBase):
    ALL_LEARNERS_AND_STAFF = XBlockVisibilityEditorView.ALL_LEARNERS_AND_STAFF
    CHOOSE_ONE = "Select a group type"
    CONTENT_GROUP_PARTITION = XBlockVisibilityEditorView.CONTENT_GROUP_PARTITION
    ENROLLMENT_TRACK_PARTITION = XBlockVisibilityEditorView.ENROLLMENT_TRACK_PARTITION
    MISSING_GROUP_LABEL = 'Deleted Group\nThis group no longer exists. Choose another group or remove the access restriction.'
    VALIDATION_ERROR_LABEL = 'This component has validation issues.'
    VALIDATION_ERROR_MESSAGE = "Error:\nThis component's access settings refer to deleted or invalid groups."
    GROUP_VISIBILITY_MESSAGE = 'Access to some content in this unit is restricted to specific groups of learners.'
    MODAL_NOT_RESTRICTED_MESSAGE = "Access is not restricted"

    def setUp(self):
        super(BaseGroupConfigurationsTest, self).setUp()

        # Set up a cohort-schemed user partition
        self.id_base = MINIMUM_STATIC_PARTITION_ID
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        self.id_base,
                        self.CONTENT_GROUP_PARTITION,
                        'Content Group Partition',
                        [
                            Group(self.id_base + 1, 'Dogs'),
                            Group(self.id_base + 2, 'Cats')
                        ],
                        scheme="cohort"
                    )
                ],
            },
        })

        self.container_page = self.go_to_unit_page()
        self.html_component = self.container_page.xblocks[1]

    def populate_course_fixture(self, course_fixture):
        """
        Populate a simple course a section, subsection, and unit, and HTML component.
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('html', 'Html Component')
                    )
                )
            )
        )

    def edit_component_visibility(self, component):
        """
        Edit the visibility of an xblock on the container page and returns an XBlockVisibilityEditorView.
        """
        component.edit_visibility()
        return XBlockVisibilityEditorView(self.browser, component.locator)

    def edit_unit_visibility(self, unit):
        """
        Edit the visibility of a unit on the container page and returns an XBlockVisibilityEditorView.
        """
        unit.edit_visibility()
        return XBlockVisibilityEditorView(self.browser, unit.locator)

    def verify_current_groups_message(self, visibility_editor, expected_current_groups):
        """
        Check that the current visibility is displayed at the top of the dialog.
        """
        if expected_current_groups == self.ALL_LEARNERS_AND_STAFF:
            self.assertEqual("Access is not restricted", visibility_editor.current_groups_message)
        else:
            self.assertEqual(
                "Access is restricted to: {groups}".format(groups=expected_current_groups),
                visibility_editor.current_groups_message
            )

    def verify_selected_partition_scheme(self, visibility_editor, expected_scheme):
        """
        Check that the expected partition scheme is selected.
        """
        self.assertItemsEqual(expected_scheme, visibility_editor.selected_partition_scheme)

    def verify_selected_groups(self, visibility_editor, expected_groups):
        """
        Check the expected partition groups.
        """
        self.assertItemsEqual(expected_groups, [group.text for group in visibility_editor.selected_groups])

    def select_and_verify_saved(self, component, partition_label, groups=[]):
        """
        Edit the visibility of an xblock on the container page and
        verify that the edit persists. Note that `groups`
        are labels which should be clicked, but not necessarily checked.
        """
        # Make initial edit(s) and save
        visibility_editor = self.edit_component_visibility(component)

        visibility_editor.select_groups_in_partition_scheme(partition_label, groups)

        # Re-open the modal and inspect its selected inputs. If no groups were selected,
        # "All Learners" should be selected partitions scheme, and we show "Select a group type" in the select.
        if not groups:
            partition_label = self.CHOOSE_ONE
        visibility_editor = self.edit_component_visibility(component)
        self.verify_selected_partition_scheme(visibility_editor, partition_label)
        self.verify_selected_groups(visibility_editor, groups)
        visibility_editor.save()

    def select_and_verify_unit_group_access(self, unit, partition_label, groups=[]):
        """
        Edit the visibility of an xblock on the unit page and
        verify that the edit persists. Note that `groups`
        are labels which should be clicked, but are not necessarily checked.
        """
        unit_access_editor = self.edit_unit_visibility(unit)
        unit_access_editor.select_groups_in_partition_scheme(partition_label, groups)

        if not groups:
            partition_label = self.CHOOSE_ONE
        unit_access_editor = self.edit_unit_visibility(unit)
        self.verify_selected_partition_scheme(unit_access_editor, partition_label)
        self.verify_selected_groups(unit_access_editor, groups)
        unit_access_editor.save()

    def verify_component_validation_error(self, component):
        """
        Verify that we see validation errors for the given component.
        """
        self.assertTrue(component.has_validation_error)
        self.assertEqual(component.validation_error_text, self.VALIDATION_ERROR_LABEL)
        self.assertEqual([self.VALIDATION_ERROR_MESSAGE], component.validation_error_messages)

    def verify_visibility_set(self, component, is_set):
        """
        Verify that the container page shows that component visibility
        settings have been edited if `is_set` is True; otherwise
        verify that the container page shows no such information.
        """
        if is_set:
            self.assertIn(self.GROUP_VISIBILITY_MESSAGE, self.container_page.sidebar_visibility_message)
            self.assertTrue(component.has_group_visibility_set)
        else:
            self.assertNotIn(self.GROUP_VISIBILITY_MESSAGE, self.container_page.sidebar_visibility_message)
            self.assertFalse(component.has_group_visibility_set)

    def verify_unit_visibility_set(self, unit, set_groups=[]):
        """
        Verify that the container visibility modal shows that unit visibility
        settings have been edited if there are `set_groups`. Otherwise verify
        that the modal shows no such information.
        """
        unit_access_editor = self.edit_unit_visibility(unit)
        if set_groups:
            self.assertIn(", ".join(set_groups), unit_access_editor.current_groups_message)
        else:
            self.assertEqual(self.MODAL_NOT_RESTRICTED_MESSAGE, unit_access_editor.current_groups_message)
        unit_access_editor.cancel()

    def update_component(self, component, metadata):
        """
        Update a component's metadata and refresh the page.
        """
        self.course_fixture._update_xblock(component.locator, {'metadata': metadata})
        self.browser.refresh()
        self.container_page.wait_for_page()

    def remove_missing_groups(self, visibility_editor, component):
        """
        Deselect the missing groups for a component.  After save,
        verify that there are no missing group messages in the modal
        and that there is no validation error on the component.
        """
        for option in visibility_editor.all_group_options:
            if option.text == self.MISSING_GROUP_LABEL:
                option.click()
        visibility_editor.save()
        visibility_editor = self.edit_component_visibility(component)
        self.assertNotIn(self.MISSING_GROUP_LABEL, [item.text for item in visibility_editor.all_group_options])
        visibility_editor.cancel()
        self.assertFalse(component.has_validation_error)


@attr(shard=21)
class UnitAccessContainerTest(BaseGroupConfigurationsTest):
    """
    Tests unit level access
    """
    GROUP_RESTRICTED_MESSAGE = 'Access to this unit is restricted to: Dogs'

    def _toggle_container_unit_access(self, group_ids, unit):
        """
        Toggle the unit level access on the course outline page
        """
        unit.toggle_unit_access('Content Groups', group_ids)

    def _verify_container_unit_access_message(self, group_ids, expected_message):
        """
        Check that the container page displays the correct unit
        access message.
        """
        self.outline.visit()
        self.outline.expand_all_subsections()
        unit = self.outline.section_at(0).subsection_at(0).unit_at(0)
        self._toggle_container_unit_access(group_ids, unit)

        container_page = self.go_to_unit_page()
        self.assertEqual(str(container_page.get_xblock_access_message()), expected_message)

    def test_default_selection(self):
        """
        Tests that no message is displayed when there are no
        restrictions on the unit or components.
        """
        self._verify_container_unit_access_message([], '')

    def test_restricted_components_message(self):
        """
        Test that the proper message is displayed when access to
        some components is restricted.
        """
        container_page = self.go_to_unit_page()
        html_component = container_page.xblocks[1]

        # Initially set visibility to Dog group.
        self.update_component(
            html_component,
            {'group_access': {self.id_base: [self.id_base + 1]}}
        )

        self._verify_container_unit_access_message([], self.GROUP_VISIBILITY_MESSAGE)

    def test_restricted_access_message(self):
        """
        Test that the proper message is displayed when access to the
        unit is restricted to a particular group.
        """
        self._verify_container_unit_access_message([self.id_base + 1], self.GROUP_RESTRICTED_MESSAGE)


@attr(shard=9)
class ContentGroupVisibilityModalTest(BaseGroupConfigurationsTest):
    """
    Tests of the visibility settings modal for components on the unit
    page (content groups).
    """
    def test_default_selection(self):
        """
        Scenario: The component visibility modal selects visible to all by default.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            Then the default visibility selection should be 'All Students and Staff'
            And the container page should not display the content visibility warning
        """
        visibility_dialog = self.edit_component_visibility(self.html_component)
        self.verify_current_groups_message(visibility_dialog, self.ALL_LEARNERS_AND_STAFF)
        self.verify_selected_partition_scheme(visibility_dialog, self.CHOOSE_ONE)
        visibility_dialog.cancel()
        self.verify_visibility_set(self.html_component, False)

    def test_reset_to_all_students_and_staff(self):
        """
        Scenario: The component visibility modal can be set to be visible to all students and staff.
            Given I have a unit with one component
            When I go to the container page for that unit
            Then the container page should not display the content visibility warning by default.
            If I then restrict access and save, and then I open the visibility editor modal for that unit's component
            And I select 'All Students and Staff'
            And I save the modal
            Then the visibility selection should be 'All Students and Staff'
            And the container page should still not display the content visibility warning
        """
        self.select_and_verify_saved(self.html_component, self.CONTENT_GROUP_PARTITION, ['Dogs'])
        self.select_and_verify_saved(self.html_component, self.ALL_LEARNERS_AND_STAFF)
        self.verify_visibility_set(self.html_component, False)

    def test_reset_unit_access_to_all_students_and_staff(self):
        """
        Scenario: The unit visibility modal can be set to be visible to all students and staff.
            Given I have a unit
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit
            And I select 'Dogs'
            And I save the modal
            Then I re-open the modal, the unit access modal should display the content visibility settings
            Then after re-opening the modal again
            And I select 'All Learners and Staff'
            And I save the modal
            And I re-open the modal, the unit access modal should display that no content is restricted
        """
        self.select_and_verify_unit_group_access(self.container_page, self.CONTENT_GROUP_PARTITION, ['Dogs'])
        self.verify_unit_visibility_set(self.container_page, set_groups=["Dogs"])
        self.select_and_verify_unit_group_access(self.container_page, self.ALL_LEARNERS_AND_STAFF)
        self.verify_unit_visibility_set(self.container_page)

    def test_select_single_content_group(self):
        """
        Scenario: The component visibility modal can be set to be visible to one content group.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            And I select 'Dogs'
            And I save the modal
            Then the visibility selection should be 'Dogs' and 'Specific Content Groups'
        """
        self.select_and_verify_saved(self.html_component, self.CONTENT_GROUP_PARTITION, ['Dogs'])

    def test_select_multiple_content_groups(self):
        """
        Scenario: The component visibility modal can be set to be visible to multiple content groups.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            And I select 'Dogs' and 'Cats'
            And I save the modal
            Then the visibility selection should be 'Dogs', 'Cats', and 'Specific Content Groups'
        """
        self.select_and_verify_saved(self.html_component, self.CONTENT_GROUP_PARTITION, ['Dogs', 'Cats'])

    def test_select_zero_content_groups(self):
        """
        Scenario: The component visibility modal can not be set to be visible to 'Specific Content Groups' without
                selecting those specific groups.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            And I select 'Specific Content Groups'
            And I save the modal
            Then the visibility selection should be 'All Students and Staff'
            And the container page should not display the content visibility warning
        """
        self.select_and_verify_saved(
            self.html_component, self.CONTENT_GROUP_PARTITION
        )
        self.verify_visibility_set(self.html_component, False)

    def test_missing_groups(self):
        """
        Scenario: The component visibility modal shows a validation error when visibility is set to multiple unknown
                group ids.
            Given I have a unit with one component
            And that component's group access specifies multiple invalid group ids
            When I go to the container page for that unit
            Then I should see a validation error message on that unit's component
            And I open the visibility editor modal for that unit's component
            Then I should see that I have selected multiple deleted groups
            And the container page should display the content visibility warning
            And I de-select the missing groups
            And I save the modal
            Then the visibility selection should be 'All Students and Staff'
            And I should not see any validation errors on the component
            And the container page should not display the content visibility warning
        """
        self.update_component(
            self.html_component,
            {'group_access': {self.id_base: [self.id_base + 3, self.id_base + 4]}}
        )
        self._verify_and_remove_missing_content_groups(
            "Deleted Group, Deleted Group",
            [self.MISSING_GROUP_LABEL] * 2
        )
        self.verify_visibility_set(self.html_component, False)

    def test_found_and_missing_groups(self):
        """
        Scenario: The component visibility modal shows a validation error when visibility is set to multiple unknown
                group ids and multiple known group ids.
            Given I have a unit with one component
            And that component's group access specifies multiple invalid and valid group ids
            When I go to the container page for that unit
            Then I should see a validation error message on that unit's component
            And I open the visibility editor modal for that unit's component
            Then I should see that I have selected multiple deleted groups
            And then if I de-select the missing groups
            And I save the modal
            Then the visibility selection should be the names of the valid groups.
            And I should not see any validation errors on the component
        """
        self.update_component(
            self.html_component,
            {'group_access': {self.id_base: [self.id_base + 1, self.id_base + 2, self.id_base + 3, self.id_base + 4]}}
        )

        self._verify_and_remove_missing_content_groups(
            'Dogs, Cats, Deleted Group, Deleted Group',
            ['Dogs', 'Cats'] + [self.MISSING_GROUP_LABEL] * 2
        )

        visibility_editor = self.edit_component_visibility(self.html_component)
        self.verify_selected_partition_scheme(visibility_editor, self.CONTENT_GROUP_PARTITION)
        expected_groups = ['Dogs', 'Cats']
        self.verify_current_groups_message(visibility_editor, ", ".join(expected_groups))
        self.verify_selected_groups(visibility_editor, expected_groups)

    def _verify_and_remove_missing_content_groups(self, current_groups_message, all_group_labels):
        self.verify_component_validation_error(self.html_component)
        visibility_editor = self.edit_component_visibility(self.html_component)
        self.verify_selected_partition_scheme(visibility_editor, self.CONTENT_GROUP_PARTITION)
        self.verify_current_groups_message(visibility_editor, current_groups_message)
        self.verify_selected_groups(visibility_editor, all_group_labels)
        self.remove_missing_groups(visibility_editor, self.html_component)


@attr(shard=3)
class EnrollmentTrackVisibilityModalTest(BaseGroupConfigurationsTest):
    """
    Tests of the visibility settings modal for components on the unit
    page (enrollment tracks).
    """
    AUDIT_TRACK = "Audit Track"
    VERIFIED_TRACK = "Verified Track"

    def setUp(self):
        super(EnrollmentTrackVisibilityModalTest, self).setUp()

        # Add an audit mode to the course
        ModeCreationPage(self.browser, self.course_id, mode_slug=u'audit', mode_display_name=self.AUDIT_TRACK).visit()

        # Add a verified mode to the course
        ModeCreationPage(
            self.browser, self.course_id, mode_slug=u'verified',
            mode_display_name=self.VERIFIED_TRACK, min_price=10
        ).visit()

        self.container_page = self.go_to_unit_page()
        self.html_component = self.container_page.xblocks[1]

        # Initially set visibility to Verified track.
        self.update_component(
            self.html_component,
            {'group_access': {ENROLLMENT_TRACK_PARTITION_ID: [2]}}  # "2" is Verified
        )

    def verify_component_group_visibility_messsage(self, component, expected_groups):
        """
        Verifies that the group visibility message below the component display name is correct.
        """
        if not expected_groups:
            self.assertIsNone(component.get_partition_group_message)
        else:
            self.assertEqual("Access restricted to: " + expected_groups, component.get_partition_group_message)

    def test_setting_enrollment_tracks(self):
        """
        Test that enrollment track groups can be selected.
        """
        # Verify that the "Verified" Group is shown on the unit page (under the unit display name).
        self.verify_component_group_visibility_messsage(self.html_component, "Verified Track")

        # Open dialog with "Verified" already selected.
        visibility_editor = self.edit_component_visibility(self.html_component)
        self.verify_current_groups_message(visibility_editor, self.VERIFIED_TRACK)
        self.verify_selected_partition_scheme(
            visibility_editor,
            self.ENROLLMENT_TRACK_PARTITION
        )
        self.verify_selected_groups(visibility_editor, [self.VERIFIED_TRACK])
        visibility_editor.cancel()

        # Select "All Learners and Staff". The helper method saves the change,
        # then reopens the dialog to verify that it was persisted.
        self.select_and_verify_saved(self.html_component, self.ALL_LEARNERS_AND_STAFF)
        self.verify_component_group_visibility_messsage(self.html_component, None)

        # Select "Audit" enrollment track. The helper method saves the change,
        # then reopens the dialog to verify that it was persisted.
        self.select_and_verify_saved(self.html_component, self.ENROLLMENT_TRACK_PARTITION, [self.AUDIT_TRACK])
        self.verify_component_group_visibility_messsage(self.html_component, "Audit Track")


@attr(shard=16)
class UnitPublishingTest(ContainerBase):
    """
    Tests of the publishing control and related widgets on the Unit page.
    """

    PUBLISHED_STATUS = "Publishing Status\nPublished (not yet released)"
    PUBLISHED_LIVE_STATUS = "Publishing Status\nPublished and Live"
    DRAFT_STATUS = "Publishing Status\nDraft (Unpublished changes)"
    LOCKED_STATUS = "Publishing Status\nVisible to Staff Only"
    RELEASE_TITLE_RELEASED = "RELEASED:"
    RELEASE_TITLE_RELEASE = "RELEASE:"

    LAST_PUBLISHED = 'Last published'
    LAST_SAVED = 'Draft saved on'

    def populate_course_fixture(self, course_fixture):
        """
        Sets up a course structure with a unit and a single HTML child.
        """

        self.html_content = '<p><strong>Body of HTML Unit.</strong></p>'
        self.courseware = CoursewarePage(self.browser, self.course_id)
        past_start_date = datetime.datetime(1974, 6, 22)
        self.past_start_date_text = "Jun 22, 1974 at 00:00 UTC"
        future_start_date = datetime.datetime(2100, 9, 13)

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('html', 'Test html', data=self.html_content)
                    )
                )
            ),
            XBlockFixtureDesc(
                'chapter',
                'Unlocked Section',
                metadata={'start': past_start_date.isoformat()}
            ).add_children(
                XBlockFixtureDesc('sequential', 'Unlocked Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Unlocked Unit').add_children(
                        XBlockFixtureDesc('problem', '<problem></problem>', data=self.html_content)
                    )
                )
            ),
            XBlockFixtureDesc('chapter', 'Section With Locked Unit').add_children(
                XBlockFixtureDesc(
                    'sequential',
                    'Subsection With Locked Unit',
                    metadata={'start': past_start_date.isoformat()}
                ).add_children(
                    XBlockFixtureDesc(
                        'vertical',
                        'Locked Unit',
                        metadata={'visible_to_staff_only': True}
                    ).add_children(
                        XBlockFixtureDesc('discussion', '', data=self.html_content)
                    )
                )
            ),
            XBlockFixtureDesc(
                'chapter',
                'Unreleased Section',
                metadata={'start': future_start_date.isoformat()}
            ).add_children(
                XBlockFixtureDesc('sequential', 'Unreleased Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Unreleased Unit')
                )
            )
        )

    def test_publishing(self):
        """
        Scenario: The publish title changes based on whether or not draft content exists
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            Then the title in the Publish information box is "Published and Live"
            And the Publish button is disabled
            And the last published text contains "Last published"
            And the last saved text contains "Last published"
            And when I add a component to the unit
            Then the title in the Publish information box is "Draft (Unpublished changes)"
            And the last saved text contains "Draft saved on"
            And the Publish button is enabled
            And when I click the Publish button
            Then the title in the Publish information box is "Published and Live"
            And the last published text contains "Last published"
            And the last saved text contains "Last published"
        """
        unit = self.go_to_unit_page()
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        # Start date set in course fixture to 1970.
        self._verify_release_date_info(
            unit, self.RELEASE_TITLE_RELEASED, 'Jan 01, 1970 at 00:00 UTC\nwith Section "Test Section"'
        )
        self._verify_last_published_and_saved(unit, self.LAST_PUBLISHED, self.LAST_PUBLISHED)
        # Should not be able to click on Publish action -- but I don't know how to test that it is not clickable.
        # TODO: continue discussion with Muhammad and Jay about this.

        # Add a component to the page so it will have unpublished changes.
        add_discussion(unit)
        unit.verify_publish_title(self.DRAFT_STATUS)
        self._verify_last_published_and_saved(unit, self.LAST_PUBLISHED, self.LAST_SAVED)
        unit.publish_action.click()
        unit.wait_for_ajax()
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        self._verify_last_published_and_saved(unit, self.LAST_PUBLISHED, self.LAST_PUBLISHED)

    def test_discard_changes(self):
        """
        Scenario: The publish title changes after "Discard Changes" is clicked
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            Then the Discard Changes button is disabled
            And I add a component to the unit
            Then the title in the Publish information box is "Draft (Unpublished changes)"
            And the Discard Changes button is enabled
            And when I click the Discard Changes button
            Then the title in the Publish information box is "Published and Live"
        """
        unit = self.go_to_unit_page()
        add_discussion(unit)
        unit.verify_publish_title(self.DRAFT_STATUS)
        unit.discard_changes()
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)

    def test_view_live_no_changes(self):
        """
        Scenario: "View Live" shows published content in LMS
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            Then the View Live button is enabled
            And when I click on the View Live button
            Then I see the published content in LMS
        """
        unit = self.go_to_unit_page()
        self._view_published_version(unit)
        self._verify_components_visible(['html'])

    def test_view_live_changes(self):
        """
        Scenario: "View Live" does not show draft content in LMS
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            And when I add a component to the unit
            And when I click on the View Live button
            Then I see the published content in LMS
            And I do not see the unpublished component
        """
        unit = self.go_to_unit_page()
        add_discussion(unit)
        self._view_published_version(unit)
        self._verify_components_visible(['html'])
        self.assertEqual(self.html_content, self.courseware.xblock_component_html_content(0))

    def test_view_live_after_publish(self):
        """
        Scenario: "View Live" shows newly published content
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            And when I add a component to the unit
            And when I click the Publish button
            And when I click on the View Live button
            Then I see the newly published component
        """
        unit = self.go_to_unit_page()
        add_discussion(unit)
        unit.publish_action.click()
        self._view_published_version(unit)
        self._verify_components_visible(['html', 'discussion'])

    def test_initially_unlocked_visible_to_students(self):
        """
        Scenario: An unlocked unit with release date in the past is visible to students
            Given I have a published unlocked unit with release date in the past
            When I go to the unit page in Studio
            Then the unit has a warning that it is visible to students
            And it is marked as "RELEASED" with release date in the past visible
            And when I click on the View Live Button
            And when I view the course as a student
            Then I see the content in the unit
        """
        unit = self.go_to_unit_page("Unlocked Section", "Unlocked Subsection", "Unlocked Unit")
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        self.assertTrue(unit.currently_visible_to_students)
        self._verify_release_date_info(
            unit, self.RELEASE_TITLE_RELEASED, self.past_start_date_text + '\n' + 'with Section "Unlocked Section"'
        )
        self._view_published_version(unit)
        self._verify_student_view_visible(['problem'])

    def test_locked_visible_to_staff_only(self):
        """
        Scenario: After locking a unit with release date in the past, it is only visible to staff
            Given I have a published unlocked unit with release date in the past
            When I go to the unit page in Studio
            And when I select "Hide from students"
            Then the unit does not have a warning that it is visible to students
            And the unit does not display inherited staff lock
            And when I click on the View Live Button
            Then I see the content in the unit when logged in as staff
            And when I view the course as a student
            Then I do not see any content in the unit
        """
        unit = self.go_to_unit_page("Unlocked Section", "Unlocked Subsection", "Unlocked Unit")
        checked = unit.toggle_staff_lock()
        self.assertTrue(checked)
        self.assertFalse(unit.currently_visible_to_students)
        self.assertFalse(unit.shows_inherited_staff_lock())
        unit.verify_publish_title(self.LOCKED_STATUS)
        self._view_published_version(unit)
        # Will initially be in staff view, locked component should be visible.
        self._verify_components_visible(['problem'])
        # Switch to student view and verify not visible
        self._verify_student_view_locked()

    def test_initially_locked_not_visible_to_students(self):
        """
        Scenario: A locked unit with release date in the past is not visible to students
            Given I have a published locked unit with release date in the past
            When I go to the unit page in Studio
            Then the unit does not have a warning that it is visible to students
            And it is marked as "RELEASE" with release date in the past visible
            And when I click on the View Live Button
            And when I view the course as a student
            Then I do not see any content in the unit
        """
        unit = self.go_to_unit_page("Section With Locked Unit", "Subsection With Locked Unit", "Locked Unit")
        unit.verify_publish_title(self.LOCKED_STATUS)
        self.assertFalse(unit.currently_visible_to_students)
        self._verify_release_date_info(
            unit, self.RELEASE_TITLE_RELEASE,
            self.past_start_date_text + '\n' + 'with Subsection "Subsection With Locked Unit"'
        )
        self._view_published_version(unit)
        self._verify_student_view_locked()

    def test_unlocked_visible_to_all(self):
        """
        Scenario: After unlocking a unit with release date in the past, it is visible to both students and staff
            Given I have a published unlocked unit with release date in the past
            When I go to the unit page in Studio
            And when I deselect "Hide from students"
            Then the unit does have a warning that it is visible to students
            And when I click on the View Live Button
            Then I see the content in the unit when logged in as staff
            And when I view the course as a student
            Then I see the content in the unit
        """
        unit = self.go_to_unit_page("Section With Locked Unit", "Subsection With Locked Unit", "Locked Unit")
        checked = unit.toggle_staff_lock()
        self.assertFalse(checked)
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        self.assertTrue(unit.currently_visible_to_students)
        self._view_published_version(unit)
        # Will initially be in staff view, components always visible.
        self._verify_components_visible(['discussion'])
        # Switch to student view and verify visible.
        self._verify_student_view_visible(['discussion'])

    def test_explicit_lock_overrides_implicit_subsection_lock_information(self):
        """
        Scenario: A unit's explicit staff lock hides its inherited subsection staff lock information
            Given I have a course with sections, subsections, and units
            And I have enabled explicit staff lock on a subsection
            When I visit the unit page
            Then the unit page shows its inherited staff lock
            And I enable explicit staff locking
            Then the unit page does not show its inherited staff lock
            And when I disable explicit staff locking
            Then the unit page now shows its inherited staff lock
        """
        self.outline.visit()
        self.outline.expand_all_subsections()
        subsection = self.outline.section_at(0).subsection_at(0)
        unit = subsection.unit_at(0)
        subsection.set_staff_lock(True)
        unit_page = unit.go_to()
        self._verify_explicit_lock_overrides_implicit_lock_information(unit_page)

    def test_explicit_lock_overrides_implicit_section_lock_information(self):
        """
        Scenario: A unit's explicit staff lock hides its inherited subsection staff lock information
            Given I have a course with sections, subsections, and units
            And I have enabled explicit staff lock on a section
            When I visit the unit page
            Then the unit page shows its inherited staff lock
            And I enable explicit staff locking
            Then the unit page does not show its inherited staff lock
            And when I disable explicit staff locking
            Then the unit page now shows its inherited staff lock
        """
        self.outline.visit()
        self.outline.expand_all_subsections()
        section = self.outline.section_at(0)
        unit = section.subsection_at(0).unit_at(0)
        section.set_staff_lock(True)
        unit_page = unit.go_to()
        self._verify_explicit_lock_overrides_implicit_lock_information(unit_page)

    def test_cancel_does_not_create_draft(self):
        """
        Scenario: Editing a component and then canceling does not create a draft version (TNL-399)
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            And edit the content of an HTML component and then press cancel
            Then the content does not change
            And the title in the Publish information box is "Published and Live"
            And when I reload the page
            Then the title in the Publish information box is "Published and Live"
        """
        unit = self.go_to_unit_page()
        component = unit.xblocks[1]
        component.edit()
        HtmlXBlockEditorView(self.browser, component.locator).set_content_and_cancel("modified content")
        self.assertEqual(component.student_content, "Body of HTML Unit.")
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        self.browser.refresh()
        unit.wait_for_page()
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)

    def test_delete_child_in_published_unit(self):
        """
        Scenario: A published unit can be published again after deleting a child
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            And delete the only component
            Then the title in the Publish information box is "Draft (Unpublished changes)"
            And when I click the Publish button
            Then the title in the Publish information box is "Published and Live"
            And when I click the View Live button
            Then I see an empty unit in LMS
        """
        unit = self.go_to_unit_page()
        unit.delete(0)
        unit.verify_publish_title(self.DRAFT_STATUS)
        unit.publish_action.click()
        unit.wait_for_ajax()
        unit.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        self._view_published_version(unit)
        self.assertEqual(0, self.courseware.num_xblock_components)

    def test_published_not_live(self):
        """
        Scenario: The publish title displays correctly for units that are not live
            Given I have a published unit with no unpublished changes that releases in the future
            When I go to the unit page in Studio
            Then the title in the Publish information box is "Published (not yet released)"
            And when I add a component to the unit
            Then the title in the Publish information box is "Draft (Unpublished changes)"
            And when I click the Publish button
            Then the title in the Publish information box is "Published (not yet released)"
        """
        unit = self.go_to_unit_page('Unreleased Section', 'Unreleased Subsection', 'Unreleased Unit')
        unit.verify_publish_title(self.PUBLISHED_STATUS)
        add_discussion(unit)
        unit.verify_publish_title(self.DRAFT_STATUS)
        unit.publish_action.click()
        unit.wait_for_ajax()
        unit.verify_publish_title(self.PUBLISHED_STATUS)

    def _view_published_version(self, unit):
        """
        Goes to the published version, then waits for the browser to load the page.
        """
        unit.view_published_version()
        self.assertEqual(len(self.browser.window_handles), 2)
        self.courseware.wait_for_page()

    def _verify_and_return_staff_page(self):
        """
        Verifies that the browser is on the staff page and returns a StaffCoursewarePage.
        """
        page = StaffCoursewarePage(self.browser, self.course_id)
        page.wait_for_page()
        return page

    def _verify_student_view_locked(self):
        """
        Verifies no component is visible when viewing as a student.
        """
        page = self._verify_and_return_staff_page()
        page.set_staff_view_mode('Learner')
        page.wait_for(lambda: self.courseware.num_xblock_components == 0, 'No XBlocks visible')

    def _verify_student_view_visible(self, expected_components):
        """
        Verifies expected components are visible when viewing as a student.
        """
        self._verify_and_return_staff_page().set_staff_view_mode('Learner')
        self._verify_components_visible(expected_components)

    def _verify_components_visible(self, expected_components):
        """
        Verifies the expected components are visible (and there are no extras).
        """
        self.assertEqual(len(expected_components), self.courseware.num_xblock_components)
        for index, component in enumerate(expected_components):
            self.assertEqual(component, self.courseware.xblock_component_type(index))

    def _verify_release_date_info(self, unit, expected_title, expected_date):
        """
        Verifies how the release date is displayed in the publishing sidebar.
        """
        self.assertEqual(expected_title, unit.release_title)
        self.assertEqual(expected_date, unit.release_date)

    def _verify_last_published_and_saved(self, unit, expected_published_prefix, expected_saved_prefix):
        """
        Verifies that last published and last saved messages respectively contain the given strings.
        """
        self.assertIn(expected_published_prefix, unit.last_published_text)
        self.assertIn(expected_saved_prefix, unit.last_saved_text)

    def _verify_explicit_lock_overrides_implicit_lock_information(self, unit_page):
        """
        Verifies that a unit with inherited staff lock does not display inherited information when explicitly locked.
        """
        self.assertTrue(unit_page.shows_inherited_staff_lock())
        unit_page.toggle_staff_lock(inherits_staff_lock=True)
        self.assertFalse(unit_page.shows_inherited_staff_lock())
        unit_page.toggle_staff_lock(inherits_staff_lock=True)
        self.assertTrue(unit_page.shows_inherited_staff_lock())

    # TODO: need to work with Jay/Christine to get testing of "Preview" working.
    # def test_preview(self):
    #     unit = self.go_to_unit_page()
    #     add_discussion(unit)
    #     unit.preview()
    #     self.assertEqual(2, self.courseware.num_xblock_components)
    #     self.assertEqual('html', self.courseware.xblock_component_type(0))
    #     self.assertEqual('discussion', self.courseware.xblock_component_type(1))


@attr(shard=3)
class DisplayNameTest(ContainerBase):
    """
    Test consistent use of display_name_with_default
    """
    def populate_course_fixture(self, course_fixture):
        """
        Sets up a course structure with nested verticals.
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('vertical', None)
                    )
                )
            )
        )

    def test_display_name_default(self):
        """
        Scenario: Given that an XBlock with a dynamic display name has been added to the course,
            When I view the unit page and note the display name of the block,
            Then I see the dynamically generated display name,
            And when I then go to the container page for that same block,
            Then I see the same generated display name.
        """
        # Unfortunately no blocks in the core platform implement display_name_with_default
        # in an interesting way for this test, so we are just testing for consistency and not
        # the actual value.
        unit = self.go_to_unit_page()
        test_block = unit.xblocks[1]
        title_on_unit_page = test_block.name
        container = test_block.go_to_container()
        self.assertEqual(container.name, title_on_unit_page)


@attr(shard=3)
class ProblemCategoryTabsTest(ContainerBase):
    """
    Test to verify tabs in problem category.
    """
    def setUp(self, is_staff=True):
        super(ProblemCategoryTabsTest, self).setUp(is_staff=is_staff)

    def populate_course_fixture(self, course_fixture):
        """
        Sets up course structure.
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def test_correct_tabs_present(self):
        """
        Scenario: Verify that correct tabs are present in problem category.

        Given I am a staff user
        When I go to unit page
        Then I only see `Common Problem Types` and `Advanced` tabs in `problem` category
        """
        self.go_to_unit_page()
        page = ContainerPage(self.browser, None)
        self.assertEqual(page.get_category_tab_names('problem'), ['Common Problem Types', 'Advanced'])

    def test_common_problem_types_tab(self):
        """
        Scenario: Verify that correct components are present in Common Problem Types tab.

        Given I am a staff user
        When I go to unit page
        Then I see correct components under `Common Problem Types` tab in `problem` category
        """
        self.go_to_unit_page()
        page = ContainerPage(self.browser, None)

        expected_components = [
            "Blank Common Problem",
            "Checkboxes",
            "Dropdown",
            "Multiple Choice",
            "Numerical Input",
            "Text Input",
            "Checkboxes with Hints and Feedback",
            "Dropdown with Hints and Feedback",
            "Multiple Choice with Hints and Feedback",
            "Numerical Input with Hints and Feedback",
            "Text Input with Hints and Feedback",
        ]
        self.assertEqual(page.get_category_tab_components('problem', 1), expected_components)


@attr(shard=16)
@ddt.ddt
class MoveComponentTest(ContainerBase):
    """
    Tests of moving an XBlock to another XBlock.
    """
    PUBLISHED_LIVE_STATUS = "Publishing Status\nPublished and Live"
    DRAFT_STATUS = "Publishing Status\nDraft (Unpublished changes)"

    def setUp(self, is_staff=True):
        super(MoveComponentTest, self).setUp(is_staff=is_staff)
        self.container = ContainerPage(self.browser, None)
        self.move_modal_view = MoveModalView(self.browser)

        self.navigation_options = {
            'section': 0,
            'subsection': 0,
            'unit': 1,
        }
        self.source_component_display_name = 'HTML 11'
        self.source_xblock_category = 'component'
        self.message_move = 'Success! "{display_name}" has been moved.'
        self.message_undo = 'Move cancelled. "{display_name}" has been moved back to its original location.'

    def populate_course_fixture(self, course_fixture):
        """
        Sets up a course structure.
        """
        # pylint: disable=attribute-defined-outside-init
        self.unit_page1 = XBlockFixtureDesc('vertical', 'Test Unit 1').add_children(
            XBlockFixtureDesc('html', 'HTML 11'),
            XBlockFixtureDesc('html', 'HTML 12')
        )
        self.unit_page2 = XBlockFixtureDesc('vertical', 'Test Unit 2').add_children(
            XBlockFixtureDesc('html', 'HTML 21'),
            XBlockFixtureDesc('html', 'HTML 22')
        )
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    self.unit_page1,
                    self.unit_page2
                )
            )
        )

    def verify_move_opertions(self, unit_page, source_component, operation, component_display_names_after_operation,
                              should_verify_publish_title=True):
        """
        Verify move operations.

        Arguments:
            unit_page (Object)                                Unit container page.
            source_component (Object)                         Source XBlock object to be moved.
            operation (str),                                  `move` or `undo move` operation.
            component_display_names_after_operation (dict)    Display names of components after operation in source/dest
            should_verify_publish_title (Boolean)             Should verify publish title ot not. Default is True.
        """
        source_component.open_move_modal()
        self.move_modal_view.navigate_to_category(self.source_xblock_category, self.navigation_options)
        self.assertEqual(self.move_modal_view.is_move_button_enabled, True)

        # Verify unit is in published state before move operation
        if should_verify_publish_title:
            self.container.verify_publish_title(self.PUBLISHED_LIVE_STATUS)

        self.move_modal_view.click_move_button()
        self.container.verify_confirmation_message(
            self.message_move.format(display_name=self.source_component_display_name)
        )
        self.assertEqual(len(unit_page.displayed_children), 1)

        # Verify unit in draft state now
        if should_verify_publish_title:
            self.container.verify_publish_title(self.DRAFT_STATUS)

        if operation == 'move':
            self.container.click_take_me_there_link()
        elif operation == 'undo_move':
            self.container.click_undo_move_link()
            self.container.verify_confirmation_message(
                self.message_undo.format(display_name=self.source_component_display_name)
            )

        unit_page = ContainerPage(self.browser, None)
        components = unit_page.displayed_children
        self.assertEqual(
            [component.name for component in components],
            component_display_names_after_operation
        )

    def verify_state_change(self, unit_page, operation):
        """
        Verify that after state change, confirmation message is hidden.

        Arguments:
            unit_page (Object)  Unit container page.
            operation (String)  Publish or discard changes operation.
        """
        # Verify unit in draft state now
        self.container.verify_publish_title(self.DRAFT_STATUS)

        # Now click publish/discard button
        if operation == 'publish':
            unit_page.publish_action.click()
        else:
            unit_page.discard_changes()

        # Now verify success message is hidden
        self.container.verify_publish_title(self.PUBLISHED_LIVE_STATUS)
        self.container.verify_confirmation_message(
            message=self.message_move.format(display_name=self.source_component_display_name),
            verify_hidden=True
        )

    def test_move_component_successfully(self):
        """
        Test if we can move a component successfully.

        Given I am a staff user
        And I go to unit page in first section
        And I open the move modal
        And I navigate to unit in second section
        And I see move button is enabled
        When I click on the move button
        Then I see move operation success message
        And When I click on take me there link
        Then I see moved component there.
        """
        unit_page = self.go_to_unit_page(unit_name='Test Unit 1')
        components = unit_page.displayed_children
        self.assertEqual(len(components), 2)

        self.verify_move_opertions(
            unit_page=unit_page,
            source_component=components[0],
            operation='move',
            component_display_names_after_operation=['HTML 21', 'HTML 22', 'HTML 11']
        )

    def test_undo_move_component_successfully(self):
        """
        Test if we can undo move a component successfully.

        Given I am a staff user
        And I go to unit page in first section
        And I open the move modal
        When I click on the move button
        Then I see move operation successful message
        And When I clicked on undo move link
        Then I see that undo move operation is successful
        """
        unit_page = self.go_to_unit_page(unit_name='Test Unit 1')
        components = unit_page.displayed_children
        self.assertEqual(len(components), 2)

        self.verify_move_opertions(
            unit_page=unit_page,
            source_component=components[0],
            operation='undo_move',
            component_display_names_after_operation=['HTML 11', 'HTML 12']
        )

    @ddt.data('publish', 'discard')
    def test_publish_discard_changes_afer_move(self, operation):
        """
        Test if success banner is hidden when we  discard changes or publish the unit after a move operation.

        Given I am a staff user
        And I go to unit page in first section
        And I open the move modal
        And I navigate to unit in second section
        And I see move button is enabled
        When I click on the move button
        Then I see move operation success message
        And When I click on publish or discard changes button
        Then I see move operation success message is hidden.
        """
        unit_page = self.go_to_unit_page(unit_name='Test Unit 1')
        components = unit_page.displayed_children
        self.assertEqual(len(components), 2)

        components[0].open_move_modal()
        self.move_modal_view.navigate_to_category(self.source_xblock_category, self.navigation_options)
        self.assertEqual(self.move_modal_view.is_move_button_enabled, True)

        # Verify unit is in published state before move operation
        self.container.verify_publish_title(self.PUBLISHED_LIVE_STATUS)

        self.move_modal_view.click_move_button()
        self.container.verify_confirmation_message(
            self.message_move.format(display_name=self.source_component_display_name)
        )
        self.assertEqual(len(unit_page.displayed_children), 1)

        self.verify_state_change(unit_page, operation)

    def test_content_experiment(self):
        """
        Test if we can move a component of content experiment successfully.

        Given that I am a staff user
        And I go to content experiment page
        And I open the move dialogue modal
        When I navigate to the unit in second section
        Then I see move button is enabled
        And when I click on the move button
        Then I see move operation success message
        And when I click on take me there link
        Then I see moved component there
        And when I undo move a component
        Then I see that undo move operation success message
        """
        # Add content experiment support to course.
        self.course_fixture.add_advanced_settings({
            u'advanced_modules': {'value': ['split_test']},
        })

        # Create group configurations
        # pylint: disable=protected-access
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            'metadata': {
                u'user_partitions': [
                    create_user_partition_json(
                        0,
                        'Test Group Configuration',
                        'Description of the group configuration.',
                        [Group('0', 'Group A'), Group('1', 'Group B')]
                    ),
                ],
            },
        })

        # Add split test to unit_page1 and assign newly created group configuration to it
        split_test = XBlockFixtureDesc('split_test', 'Test Content Experiment', metadata={'user_partition_id': 0})
        self.course_fixture.create_xblock(self.unit_page1.locator, split_test)

        # Visit content experiment container page.
        unit_page = ContainerPage(self.browser, split_test.locator)
        unit_page.visit()

        group_a_locator = unit_page.displayed_children[0].locator

        # Add some components to Group A.
        self.course_fixture.create_xblock(
            group_a_locator, XBlockFixtureDesc('html', 'HTML 311')
        )
        self.course_fixture.create_xblock(
            group_a_locator, XBlockFixtureDesc('html', 'HTML 312')
        )

        # Go to group page to move it's component.
        group_container_page = ContainerPage(self.browser, group_a_locator)
        group_container_page.visit()

        # Verify content experiment block has correct groups and components.
        components = group_container_page.displayed_children
        self.assertEqual(len(components), 2)

        self.source_component_display_name = 'HTML 311'

        # Verify undo move operation for content experiment.
        self.verify_move_opertions(
            unit_page=group_container_page,
            source_component=components[0],
            operation='undo_move',
            component_display_names_after_operation=['HTML 311', 'HTML 312'],
            should_verify_publish_title=False
        )

        # Verify move operation for content experiment.
        self.verify_move_opertions(
            unit_page=group_container_page,
            source_component=components[0],
            operation='move',
            component_display_names_after_operation=['HTML 21', 'HTML 22', 'HTML 311'],
            should_verify_publish_title=False
        )

    # Ideally this test should be decorated with @attr('a11y') so that it should run in a11y jenkins job
    # But for some reason it always fails in a11y jenkins job and passes always locally on devstack as well
    # as in bokchoy jenkins job. Due to this reason, test is marked to run under bokchoy jenkins job.
    def test_a11y(self):
        """
        Verify move modal a11y.
        """
        unit_page = self.go_to_unit_page(unit_name='Test Unit 1')

        unit_page.a11y_audit.config.set_scope(
            include=[".modal-window.move-modal"]
        )
        unit_page.a11y_audit.config.set_rules({
            'ignore': [
                'color-contrast',  # TODO: AC-716
                'link-href',  # TODO: AC-716
            ]
        })

        unit_page.displayed_children[0].open_move_modal()

        for category in ['section', 'subsection', 'component']:
            self.move_modal_view.navigate_to_category(category, self.navigation_options)
            unit_page.a11y_audit.check_for_accessibility_errors()
