"""
Acceptance tests for Studio related to the container page.
The container page is used both for displaying units, and
for displaying containers within units.
"""
from nose.plugins.attrib import attr
from unittest import skip

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.component_editor import ComponentEditorView, ComponentVisibilityEditorView
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.html_component_editor import HtmlComponentEditorView
from common.test.acceptance.pages.studio.utils import add_discussion, drag
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.staff_view import StaffPage
from common.test.acceptance.tests.helpers import create_user_partition_json

import datetime
from bok_choy.promise import Promise, EmptyPromise
from base_studio_test import ContainerBase
from xmodule.partitions.partitions import Group


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


@skip("Flaky: 01/16/2015")
@attr(shard=1)
class DragAndDropTest(NestedVerticalTest):
    """
    Tests of reordering within the container page.
    """

    def drag_and_verify(self, source, target, expected_ordering):
        self.do_action_and_verify(
            lambda (container): drag(container, source, target, 40),
            expected_ordering
        )

    def test_reorder_in_group(self):
        """
        Drag Group A Item 2 before Group A Item 1.
        """
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_2, self.group_a_item_1]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.drag_and_verify(self.group_a_item_2_handle, self.group_a_item_1_handle, expected_ordering)

    def test_drag_to_top(self):
        """
        Drag Group A Item 1 to top level (outside of Group A).
        """
        expected_ordering = [{self.container_title: [self.group_a_item_1, self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.drag_and_verify(self.group_a_item_1_handle, self.group_a_handle, expected_ordering)

    def test_drag_into_different_group(self):
        """
        Drag Group B Item 1 into Group A (first element).
        """
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_b_item_1, self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_2]},
                             {self.group_empty: []}]
        self.drag_and_verify(self.group_b_item_1_handle, self.group_a_item_1_handle, expected_ordering)

    def test_drag_group_into_group(self):
        """
        Drag Group B into Group A (first element).
        """
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty]},
                             {self.group_a: [self.group_b, self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.drag_and_verify(self.group_b_handle, self.group_a_item_1_handle, expected_ordering)

    def test_drag_after_addition(self):
        """
        Add some components and then verify that drag and drop still works.
        """
        group_a_menu = 0

        def add_new_components_and_rearrange(container):
            # Add a video component to Group 1
            add_discussion(container, group_a_menu)
            # Duplicate the first item in Group A
            container.duplicate(self.group_a_item_1_action_index)

            first_handle = self.group_a_item_1_handle
            # Drag newly added video component to top.
            drag(container, first_handle + 3, first_handle, 40)
            # Drag duplicated component to top.
            drag(container, first_handle + 2, first_handle, 40)

        duplicate_label = self.duplicate_label.format(self.group_a_item_1)

        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [duplicate_label, self.discussion_label, self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]

        self.do_action_and_verify(add_new_components_and_rearrange, expected_ordering)


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


@attr(shard=1)
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
        component_editor = ComponentEditorView(self.browser, component.locator)
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

    def test_edit_raw_html(self):
        """
        Test the raw html editing functionality.
        """
        modified_content = "<p>modified content</p>"

        #navigate to and open the component for editing
        unit = self.go_to_unit_page()
        container = unit.xblocks[1].go_to_container()
        component = container.xblocks[1].children[0]
        component.edit()

        html_editor = HtmlComponentEditorView(self.browser, component.locator)
        html_editor.set_content_and_save(modified_content, raw=True)

        #note we're expecting the <p> tags to have been removed
        self.assertEqual(component.student_content, "modified content")


@attr(shard=3)
class EditVisibilityModalTest(ContainerBase):
    """
    Tests of the visibility settings modal for components on the unit
    page.
    """
    VISIBILITY_LABEL_ALL = 'All Students and Staff'
    VISIBILITY_LABEL_SPECIFIC = 'Specific Content Groups'
    MISSING_GROUP_LABEL = 'Deleted Content Group\nContent group no longer exists. Please choose another or allow access to All Students and staff'
    VALIDATION_ERROR_LABEL = 'This component has validation issues.'
    VALIDATION_ERROR_MESSAGE = 'Error:\nThis component refers to deleted or invalid content groups.'
    GROUP_VISIBILITY_MESSAGE = 'Some content in this unit is visible only to particular content groups'

    def setUp(self):
        super(EditVisibilityModalTest, self).setUp()

        # Set up a cohort-schemed user partition
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Configuration Dogs, Cats',
                        'Content Group Partition',
                        [Group("0", 'Dogs'), Group("1", 'Cats')],
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
        Edit the visibility of an xblock on the container page.
        """
        component.edit_visibility()
        return ComponentVisibilityEditorView(self.browser, component.locator)

    def verify_selected_labels(self, visibility_editor, expected_labels):
        """
        Verify that a visibility editor's selected labels match the
        expected ones.
        """
        # If anything other than 'All Students and Staff', is selected,
        # 'Specific Content Groups' should be selected as well.
        if expected_labels != [self.VISIBILITY_LABEL_ALL]:
            expected_labels.append(self.VISIBILITY_LABEL_SPECIFIC)
        self.assertItemsEqual(expected_labels, [option.text for option in visibility_editor.selected_options])

    def select_and_verify_saved(self, component, labels, expected_labels=None):
        """
        Edit the visibility of an xblock on the container page and
        verify that the edit persists.  If provided, verify that
        `expected_labels` are selected after save, otherwise expect
        that `labels` are selected after save.  Note that `labels`
        are labels which should be clicked, but not necessarily checked.
        """
        if expected_labels is None:
            expected_labels = labels

        # Make initial edit(s) and save
        visibility_editor = self.edit_component_visibility(component)
        for label in labels:
            visibility_editor.select_option(label, save=False)
        visibility_editor.save()

        # Re-open the modal and inspect its selected inputs
        visibility_editor = self.edit_component_visibility(component)
        self.verify_selected_labels(visibility_editor, expected_labels)
        visibility_editor.save()

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
        for option in visibility_editor.selected_options:
            if option.text == self.MISSING_GROUP_LABEL:
                option.click()
        visibility_editor.save()
        visibility_editor = self.edit_component_visibility(component)
        self.assertNotIn(self.MISSING_GROUP_LABEL, [item.text for item in visibility_editor.all_options])
        visibility_editor.cancel()
        self.assertFalse(component.has_validation_error)

    def test_default_selection(self):
        """
        Scenario: The component visibility modal selects visible to all by default.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            Then the default visibility selection should be 'All Students and Staff'
            And the container page should not display the content visibility warning
        """
        self.verify_selected_labels(self.edit_component_visibility(self.html_component), [self.VISIBILITY_LABEL_ALL])
        self.verify_visibility_set(self.html_component, False)

    def test_reset_to_all_students_and_staff(self):
        """
        Scenario: The component visibility modal can be set to be visible to all students and staff.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            And I select 'Dogs'
            And I save the modal
            Then the container page should display the content visibility warning
            And I re-open the visibility editor modal for that unit's component
            And I select 'All Students and Staff'
            And I save the modal
            Then the visibility selection should be 'All Students and Staff'
            And the container page should not display the content visibility warning
        """
        self.select_and_verify_saved(self.html_component, ['Dogs'])
        self.verify_visibility_set(self.html_component, True)
        self.select_and_verify_saved(self.html_component, [self.VISIBILITY_LABEL_ALL])
        self.verify_visibility_set(self.html_component, False)

    def test_select_single_content_group(self):
        """
        Scenario: The component visibility modal can be set to be visible to one content group.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            And I select 'Dogs'
            And I save the modal
            Then the visibility selection should be 'Dogs' and 'Specific Content Groups'
            And the container page should display the content visibility warning
        """
        self.select_and_verify_saved(self.html_component, ['Dogs'])
        self.verify_visibility_set(self.html_component, True)

    def test_select_multiple_content_groups(self):
        """
        Scenario: The component visibility modal can be set to be visible to multiple content groups.
            Given I have a unit with one component
            When I go to the container page for that unit
            And I open the visibility editor modal for that unit's component
            And I select 'Dogs' and 'Cats'
            And I save the modal
            Then the visibility selection should be 'Dogs', 'Cats', and 'Specific Content Groups'
            And the container page should display the content visibility warning
        """
        self.select_and_verify_saved(self.html_component, ['Dogs', 'Cats'])
        self.verify_visibility_set(self.html_component, True)

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
            self.html_component, [self.VISIBILITY_LABEL_SPECIFIC], expected_labels=[self.VISIBILITY_LABEL_ALL]
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
        self.update_component(self.html_component, {'group_access': {0: [2, 3]}})
        self.verify_component_validation_error(self.html_component)
        visibility_editor = self.edit_component_visibility(self.html_component)
        self.verify_selected_labels(visibility_editor, [self.MISSING_GROUP_LABEL] * 2)
        self.remove_missing_groups(visibility_editor, self.html_component)
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
            And the container page should display the content visibility warning
            And I de-select the missing groups
            And I save the modal
            Then the visibility selection should be the names of the valid groups.
            And I should not see any validation errors on the component
            And the container page should display the content visibility warning
        """
        self.update_component(self.html_component, {'group_access': {0: [0, 1, 2, 3]}})
        self.verify_component_validation_error(self.html_component)
        visibility_editor = self.edit_component_visibility(self.html_component)
        self.verify_selected_labels(visibility_editor, ['Dogs', 'Cats'] + [self.MISSING_GROUP_LABEL] * 2)
        self.remove_missing_groups(visibility_editor, self.html_component)
        visibility_editor = self.edit_component_visibility(self.html_component)
        self.verify_selected_labels(visibility_editor, ['Dogs', 'Cats'])
        self.verify_visibility_set(self.html_component, True)


@attr(shard=1)
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
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
        # Start date set in course fixture to 1970.
        self._verify_release_date_info(
            unit, self.RELEASE_TITLE_RELEASED, 'Jan 01, 1970 at 00:00 UTC\nwith Section "Test Section"'
        )
        self._verify_last_published_and_saved(unit, self.LAST_PUBLISHED, self.LAST_PUBLISHED)
        # Should not be able to click on Publish action -- but I don't know how to test that it is not clickable.
        # TODO: continue discussion with Muhammad and Jay about this.

        # Add a component to the page so it will have unpublished changes.
        add_discussion(unit)
        self._verify_publish_title(unit, self.DRAFT_STATUS)
        self._verify_last_published_and_saved(unit, self.LAST_PUBLISHED, self.LAST_SAVED)
        unit.publish_action.click()
        unit.wait_for_ajax()
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
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
        self._verify_publish_title(unit, self.DRAFT_STATUS)
        unit.discard_changes()
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)

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
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
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
        self._verify_publish_title(unit, self.LOCKED_STATUS)
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
        self._verify_publish_title(unit, self.LOCKED_STATUS)
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
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
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

    def test_published_unit_with_draft_child(self):
        """
        Scenario: A published unit with a draft child can be published
            Given I have a published unit with no unpublished changes
            When I go to the unit page in Studio
            And edit the content of the only component
            Then the content changes
            And the title in the Publish information box is "Draft (Unpublished changes)"
            And when I click the Publish button
            Then the title in the Publish information box is "Published and Live"
            And when I click the View Live button
            Then I see the changed content in LMS
        """
        modified_content = 'modified content'

        unit = self.go_to_unit_page()
        component = unit.xblocks[1]
        component.edit()
        HtmlComponentEditorView(self.browser, component.locator).set_content_and_save(modified_content)
        self.assertEqual(component.student_content, modified_content)
        self._verify_publish_title(unit, self.DRAFT_STATUS)
        unit.publish_action.click()
        unit.wait_for_ajax()
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
        self._view_published_version(unit)
        self.assertIn(modified_content, self.courseware.xblock_component_html_content(0))

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
        HtmlComponentEditorView(self.browser, component.locator).set_content_and_cancel("modified content")
        self.assertEqual(component.student_content, "Body of HTML Unit.")
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
        self.browser.refresh()
        unit.wait_for_page()
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)

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
        self._verify_publish_title(unit, self.DRAFT_STATUS)
        unit.publish_action.click()
        unit.wait_for_ajax()
        self._verify_publish_title(unit, self.PUBLISHED_LIVE_STATUS)
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
        self._verify_publish_title(unit, self.PUBLISHED_STATUS)
        add_discussion(unit)
        self._verify_publish_title(unit, self.DRAFT_STATUS)
        unit.publish_action.click()
        unit.wait_for_ajax()
        self._verify_publish_title(unit, self.PUBLISHED_STATUS)

    def _view_published_version(self, unit):
        """
        Goes to the published version, then waits for the browser to load the page.
        """
        unit.view_published_version()
        self.assertEqual(len(self.browser.window_handles), 2)
        self.courseware.wait_for_page()

    def _verify_and_return_staff_page(self):
        """
        Verifies that the browser is on the staff page and returns a StaffPage.
        """
        page = StaffPage(self.browser, self.course_id)
        EmptyPromise(page.is_browser_on_page, 'Browser is on staff page in LMS').fulfill()
        return page

    def _verify_student_view_locked(self):
        """
        Verifies no component is visible when viewing as a student.
        """
        self._verify_and_return_staff_page().set_staff_view_mode('Student')
        self.assertEqual(0, self.courseware.num_xblock_components)

    def _verify_student_view_visible(self, expected_components):
        """
        Verifies expected components are visible when viewing as a student.
        """
        self._verify_and_return_staff_page().set_staff_view_mode('Student')
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

    def _verify_publish_title(self, unit, expected_title):
        """
        Waits for the publish title to change to the expected value.
        """
        def wait_for_title_change():
            return (unit.publish_title == expected_title, unit.publish_title)

        Promise(wait_for_title_change, "Publish title incorrect. Found '" + unit.publish_title + "'").fulfill()

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
