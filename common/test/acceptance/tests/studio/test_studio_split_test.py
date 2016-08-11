"""
Acceptance tests for Studio related to the split_test module.
"""

import math
from unittest import skip
from nose.plugins.attrib import attr
from selenium.webdriver.support.ui import Select

from xmodule.partitions.partitions import Group
from bok_choy.promise import Promise, EmptyPromise

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.component_editor import ComponentEditorView
from common.test.acceptance.pages.studio.overview import CourseOutlinePage, CourseOutlineUnit
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.settings_group_configurations import GroupConfigurationsPage
from common.test.acceptance.pages.studio.utils import add_advanced_component
from common.test.acceptance.pages.xblock.utils import wait_for_xblock_initialization
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.tests.helpers import create_user_partition_json

from base_studio_test import StudioCourseTest

from test_studio_container import ContainerBase


class SplitTestMixin(object):
    """
    Mixin that contains useful methods for split_test module testing.
    """
    def verify_groups(self, container, active_groups, inactive_groups, verify_missing_groups_not_present=True):
        """
        Check that the groups appear and are correctly categorized as to active and inactive.

        Also checks that the "add missing groups" button/link is not present unless a value of False is passed
        for verify_missing_groups_not_present.
        """
        def wait_for_xblocks_to_render():
            # First xblock is the container for the page, subtract 1.
            return (len(active_groups) + len(inactive_groups) == len(container.xblocks) - 1, len(active_groups))

        Promise(wait_for_xblocks_to_render, "Number of xblocks on the page are incorrect").fulfill()

        def check_xblock_names(expected_groups, actual_blocks):
            self.assertEqual(len(expected_groups), len(actual_blocks))
            for idx, expected in enumerate(expected_groups):
                self.assertEqual(expected, actual_blocks[idx].name)

        check_xblock_names(active_groups, container.active_xblocks)
        check_xblock_names(inactive_groups, container.inactive_xblocks)

        # Verify inactive xblocks appear after active xblocks
        check_xblock_names(active_groups + inactive_groups, container.xblocks[1:])
        if verify_missing_groups_not_present:
            self.verify_add_missing_groups_button_not_present(container)

    def verify_add_missing_groups_button_not_present(self, container):
        """
        Checks that the "add missing groups" button/link is not present.
        """
        def missing_groups_button_not_present():
            button_present = container.missing_groups_button_present()
            return (not button_present, not button_present)

        Promise(missing_groups_button_not_present, "Add missing groups button should not be showing.").fulfill()


@attr(shard=2)
class SplitTest(ContainerBase, SplitTestMixin):
    """
    Tests for creating and editing split test instances in Studio.
    """
    __test__ = True

    def setUp(self):
        super(SplitTest, self).setUp()
        # This line should be called once courseFixture is installed
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Configuration alpha,beta',
                        'first',
                        [Group("0", 'alpha'), Group("1", 'beta')]
                    ),
                    create_user_partition_json(
                        1,
                        'Configuration 0,1,2',
                        'second',
                        [Group("0", 'Group 0'), Group("1", 'Group 1'), Group("2", 'Group 2')]
                    ),
                ],
            },
        })

    def populate_course_fixture(self, course_fixture):
        course_fixture.add_advanced_settings(
            {u"advanced_modules": {"value": ["split_test"]}}
        )

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def verify_add_missing_groups_button_not_present(self, container):
        """
        Checks that the "add missing groups" button/link is not present.
        """
        def missing_groups_button_not_present():
            button_present = container.missing_groups_button_present()
            return (not button_present, not button_present)

        Promise(missing_groups_button_not_present, "Add missing groups button should not be showing.").fulfill()

    def create_poorly_configured_split_instance(self):
        """
        Creates a split test instance with a missing group and an inactive group.

        Returns the container page.
        """
        unit = self.go_to_unit_page()
        add_advanced_component(unit, 0, 'split_test')
        container = self.go_to_nested_container_page()
        container.edit()
        component_editor = ComponentEditorView(self.browser, container.locator)
        component_editor.set_select_value_and_save('Group Configuration', 'Configuration alpha,beta')
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Configuration alpha,beta',
                        'first',
                        [Group("0", 'alpha'), Group("2", 'gamma')]
                    )
                ],
            },
        })
        return self.go_to_nested_container_page()

    def test_create_and_select_group_configuration(self):
        """
        Tests creating a split test instance on the unit page, and then
        assigning the group configuration.
        """
        unit = self.go_to_unit_page()
        add_advanced_component(unit, 0, 'split_test')
        container = self.go_to_nested_container_page()
        container.edit()
        component_editor = ComponentEditorView(self.browser, container.locator)
        component_editor.set_select_value_and_save('Group Configuration', 'Configuration alpha,beta')
        self.verify_groups(container, ['alpha', 'beta'], [])

        # Switch to the other group configuration. Must navigate again to the container page so
        # that there is only a single "editor" on the page.
        container = self.go_to_nested_container_page()
        container.edit()
        component_editor = ComponentEditorView(self.browser, container.locator)
        component_editor.set_select_value_and_save('Group Configuration', 'Configuration 0,1,2')
        self.verify_groups(container, ['Group 0', 'Group 1', 'Group 2'], ['Group ID 0', 'Group ID 1'])

        # Reload the page to make sure the groups were persisted.
        container = self.go_to_nested_container_page()
        self.verify_groups(container, ['Group 0', 'Group 1', 'Group 2'], ['Group ID 0', 'Group ID 1'])

    @skip("This fails periodically where it fails to trigger the add missing groups action.Dis")
    def test_missing_group(self):
        """
        The case of a split test with invalid configuration (missing group).
        """
        container = self.create_poorly_configured_split_instance()

        # Wait for the xblock to be fully initialized so that the add button is rendered
        wait_for_xblock_initialization(self, '.xblock[data-block-type="split_test"]')

        # Click the add button and verify that the groups were added on the page
        container.add_missing_groups()
        self.verify_groups(container, ['alpha', 'gamma'], ['beta'])

        # Reload the page to make sure the groups were persisted.
        container = self.go_to_nested_container_page()
        self.verify_groups(container, ['alpha', 'gamma'], ['beta'])

    def test_delete_inactive_group(self):
        """
        Test deleting an inactive group.
        """
        container = self.create_poorly_configured_split_instance()

        # The inactive group is the 2nd group, but it is the first one
        # with a visible delete button, so use index 0
        container.delete(0)
        self.verify_groups(container, ['alpha'], [], verify_missing_groups_not_present=False)


@attr(shard=2)
class GroupConfigurationsNoSplitTest(StudioCourseTest):
    """
    Tests how the Group Configuration page should look when the split_test module is not enabled.
    """
    def setUp(self):
        super(GroupConfigurationsNoSplitTest, self).setUp()
        self.group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def test_no_content_experiment_sections(self):
        """
        Scenario: if split_test module is not present in Advanced Settings, content experiment
           parts of the Group Configurations page are not shown.
        Given I have a course with split_test module not enabled
        Then when I go to the Group Configurations page there are no content experiment sections
        """
        self.group_configurations_page.visit()
        self.assertFalse(self.group_configurations_page.experiment_group_sections_present)


@attr(shard=2)
class GroupConfigurationsTest(ContainerBase, SplitTestMixin):
    """
    Tests that Group Configurations page works correctly with previously
    added configurations in Studio
    """
    __test__ = True

    def setUp(self):
        super(GroupConfigurationsTest, self).setUp()
        self.page = GroupConfigurationsPage(
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

    def _assert_fields(self, config, cid=None, name='', description='', groups=None):
        self.assertEqual(config.mode, 'details')

        if name:
            self.assertIn(name, config.name)

        if cid:
            self.assertEqual(cid, config.id)
        else:
            # To make sure that id is present on the page and it is not an empty.
            # We do not check the value of the id, because it's generated randomly and we cannot
            # predict this value
            self.assertTrue(config.id)

        # Expand the configuration
        config.toggle()

        if description:
            self.assertIn(description, config.description)

        if groups:
            allocation = int(math.floor(100 / len(groups)))
            self.assertEqual(groups, [group.name for group in config.groups])
            for group in config.groups:
                self.assertEqual(str(allocation) + "%", group.allocation)

        # Collapse the configuration
        config.toggle()

    def _add_split_test_to_vertical(self, number, group_configuration_metadata=None):
        """
        Add split test to vertical #`number`.

        If `group_configuration_metadata` is not None, use it to assign group configuration to split test.
        """
        vertical = self.course_fixture.get_nested_xblocks(category="vertical")[number]
        if group_configuration_metadata:
            split_test = XBlockFixtureDesc('split_test', 'Test Content Experiment', metadata=group_configuration_metadata)
        else:
            split_test = XBlockFixtureDesc('split_test', 'Test Content Experiment')
        self.course_fixture.create_xblock(vertical.locator, split_test)
        return split_test

    def populate_course_fixture(self, course_fixture):
        course_fixture.add_advanced_settings({
            u"advanced_modules": {"value": ["split_test"]},
        })
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def create_group_configuration_experiment(self, groups, associate_experiment):
        """
        Creates a Group Configuration containing a list of groups.
        Optionally creates a Content Experiment and associates it with previous Group Configuration.

        Returns group configuration or (group configuration, experiment xblock)
        """
        # Create a new group configurations
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(0, "Name", "Description.", groups),
                ],
            },
        })

        if associate_experiment:
            # Assign newly created group configuration to experiment
            vertical = self.course_fixture.get_nested_xblocks(category="vertical")[0]
            split_test = XBlockFixtureDesc('split_test', 'Test Content Experiment', metadata={'user_partition_id': 0})
            self.course_fixture.create_xblock(vertical.locator, split_test)

        # Go to the Group Configuration Page
        self.page.visit()
        config = self.page.experiment_group_configurations[0]

        if associate_experiment:
            return config, split_test
        return config

    def publish_unit_in_lms_and_view(self, courseware_page, publish=True):
        """
        Given course outline page, publish first unit and view it in LMS when publish is false, it will only view
        """
        self.outline_page.visit()
        self.outline_page.expand_all_subsections()
        section = self.outline_page.section_at(0)
        unit = section.subsection_at(0).unit_at(0).go_to()

        # I publish and view in LMS and it is rendered correctly
        if publish:
            unit.publish_action.click()
        unit.view_published_version()
        self.assertEqual(len(self.browser.window_handles), 2)
        courseware_page.wait_for_page()

    def get_select_options(self, page, selector):
        """
        Get list of options of dropdown that is specified by selector on a given page.
        """
        select_element = page.q(css=selector)
        self.assertTrue(select_element.is_present())
        return [option.text for option in Select(select_element[0]).options]

    def test_no_group_configurations_added(self):
        """
        Scenario: Ensure that message telling me to create a new group configuration is
        shown when group configurations were not added.
        Given I have a course without group configurations
        When I go to the Group Configuration page in Studio
        Then I see "You have not created any group configurations yet." message
        """
        self.page.visit()
        self.assertTrue(self.page.experiment_group_sections_present)
        self.assertTrue(self.page.no_experiment_groups_message_is_present)
        self.assertIn(
            "You have not created any group configurations yet.",
            self.page.no_experiment_groups_message_text
        )

    def test_group_configurations_have_correct_data(self):
        """
        Scenario: Ensure that the group configuration is rendered correctly in expanded/collapsed mode.
        Given I have a course with 2 group configurations
        And I go to the Group Configuration page in Studio
        And I work with the first group configuration
        And I see `name`, `id` are visible and have correct values
        When I expand the first group configuration
        Then I see `description` and `groups` appear and also have correct values
        And I do the same checks for the second group configuration
        """
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Name of the Group Configuration',
                        'Description of the group configuration.',
                        [Group("0", 'Group 0'), Group("1", 'Group 1')]
                    ),
                    create_user_partition_json(
                        1,
                        'Name of second Group Configuration',
                        'Second group configuration.',
                        [Group("0", 'Alpha'), Group("1", 'Beta'), Group("2", 'Gamma')]
                    ),
                ],
            },
        })

        self.page.visit()
        config = self.page.experiment_group_configurations[0]
        # no groups when the the configuration is collapsed
        self.assertEqual(len(config.groups), 0)
        self._assert_fields(
            config,
            cid="0", name="Name of the Group Configuration",
            description="Description of the group configuration.",
            groups=["Group 0", "Group 1"]
        )

        config = self.page.experiment_group_configurations[1]

        self._assert_fields(
            config,
            name="Name of second Group Configuration",
            description="Second group configuration.",
            groups=["Alpha", "Beta", "Gamma"]
        )

    def test_can_create_and_edit_group_configuration(self):
        """
        Scenario: Ensure that the group configuration can be created and edited correctly.
        Given I have a course without group configurations
        When I click button 'Create new Group Configuration'
        And I set new name and description, change name for the 2nd default group, add one new group
        And I click button 'Create'
        Then I see the new group configuration is added and has correct data
        When I edit the group group_configuration
        And I change the name and description, add new group, remove old one and change name for the Group A
        And I click button 'Save'
        Then I see the group configuration is saved successfully and has the new data
        """
        self.page.visit()
        self.assertEqual(len(self.page.experiment_group_configurations), 0)
        # Create new group configuration
        self.page.create_experiment_group_configuration()
        config = self.page.experiment_group_configurations[0]
        config.name = "New Group Configuration Name"
        config.description = "New Description of the group configuration."
        config.groups[1].name = "New Group Name"
        # Add new group
        config.add_group()  # Group C

        # Save the configuration
        self.assertEqual(config.get_text('.action-primary'), "Create")
        self.assertFalse(config.delete_button_is_present)
        config.save()

        self._assert_fields(
            config,
            name="New Group Configuration Name",
            description="New Description of the group configuration.",
            groups=["Group A", "New Group Name", "Group C"]
        )

        # Edit the group configuration
        config.edit()
        # Update fields
        self.assertTrue(config.id)
        config.name = "Second Group Configuration Name"
        config.description = "Second Description of the group configuration."
        self.assertEqual(config.get_text('.action-primary'), "Save")
        # Add new group
        config.add_group()  # Group D
        # Remove group with name "New Group Name"
        config.groups[1].remove()
        # Rename Group A
        config.groups[0].name = "First Group"
        # Save the configuration
        config.save()

        self._assert_fields(
            config,
            name="Second Group Configuration Name",
            description="Second Description of the group configuration.",
            groups=["First Group", "Group C", "Group D"]
        )

    def test_focus_management_in_experiment_group_inputs(self):
        """
        Scenario: Ensure that selecting the focus inputs in the groups list
        sets the .is-focused class on the fieldset
        Given I have a course with experiment group configurations
        When I click the name of the first group
        Then the fieldset wrapping the group names whould get class .is-focused
        When I click away from the first group
        Then the fieldset should not have class .is-focused anymore
        """
        self.page.visit()
        self.page.create_experiment_group_configuration()
        config = self.page.experiment_group_configurations[0]
        group_a = config.groups[0]

        # Assert the fieldset doesn't have .is-focused class
        self.assertFalse(self.page.q(css="fieldset.groups-fields.is-focused").visible)

        # Click on the Group A input field
        self.page.q(css=group_a.prefix).click()

        # Assert the fieldset has .is-focused class applied
        self.assertTrue(self.page.q(css="fieldset.groups-fields.is-focused").visible)

        # Click away
        self.page.q(css=".page-header").click()

        # Assert the fieldset doesn't have .is-focused class
        self.assertFalse(self.page.q(css="fieldset.groups-fields.is-focused").visible)

    def test_use_group_configuration(self):
        """
        Scenario: Ensure that the group configuration can be used by split_module correctly
        Given I have a course without group configurations
        When I create new group configuration
        And I set new name and add a new group, save the group configuration
        And I go to the unit page in Studio
        And I add new advanced module "Content Experiment"
        When I assign created group configuration to the module
        Then I see the module has correct groups
        """
        self.page.visit()
        # Create new group configuration
        self.page.create_experiment_group_configuration()
        config = self.page.experiment_group_configurations[0]
        config.name = "New Group Configuration Name"
        # Add new group
        config.add_group()
        config.groups[2].name = "New group"
        # Save the configuration
        config.save()

        split_test = self._add_split_test_to_vertical(number=0)

        container = ContainerPage(self.browser, split_test.locator)
        container.visit()
        container.edit()
        component_editor = ComponentEditorView(self.browser, container.locator)
        component_editor.set_select_value_and_save('Group Configuration', 'New Group Configuration Name')
        self.verify_groups(container, ['Group A', 'Group B', 'New group'], [])

    def test_container_page_active_verticals_names_are_synced(self):
        """
        Scenario: Ensure that the Content Experiment display synced vertical names and correct groups.
        Given I have a course with group configuration
        And I go to the Group Configuration page in Studio
        And I edit the name of the group configuration, add new group and remove old one
        And I change the name for the group "New group" to "Second Group"
        And I go to the Container page in Studio
        And I edit the Content Experiment
        Then I see the group configuration name is changed in `Group Configuration` dropdown
        And the group configuration name is changed on container page
        And I see the module has 2 active groups and one inactive
        And I see "Add missing groups" link exists
        When I click on "Add missing groups" link
        The I see the module has 3 active groups and one inactive
        """
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Name of the Group Configuration',
                        'Description of the group configuration.',
                        [Group("0", 'Group A'), Group("1", 'Group B'), Group("2", 'Group C')]
                    ),
                ],
            },
        })

        # Add split test to vertical and assign newly created group configuration to it
        split_test = self._add_split_test_to_vertical(number=0, group_configuration_metadata={'user_partition_id': 0})

        self.page.visit()
        config = self.page.experiment_group_configurations[0]
        config.edit()
        config.name = "Second Group Configuration Name"
        # `Group C` -> `Second Group`
        config.groups[2].name = "Second Group"
        # Add new group
        config.add_group()  # Group D
        # Remove Group A
        config.groups[0].remove()
        # Save the configuration
        config.save()

        container = ContainerPage(self.browser, split_test.locator)
        container.visit()
        container.edit()
        component_editor = ComponentEditorView(self.browser, container.locator)
        self.assertEqual(
            "Second Group Configuration Name",
            component_editor.get_selected_option_text('Group Configuration')
        )
        component_editor.cancel()
        self.assertIn(
            "Second Group Configuration Name",
            container.get_xblock_information_message()
        )
        self.verify_groups(
            container, ['Group B', 'Second Group'], ['Group ID 0'],
            verify_missing_groups_not_present=False
        )
        # Click the add button and verify that the groups were added on the page
        container.add_missing_groups()
        self.verify_groups(container, ['Group B', 'Second Group', 'Group D'], ['Group ID 0'])

    def test_can_cancel_creation_of_group_configuration(self):
        """
        Scenario: Ensure that creation of the group configuration can be canceled correctly.
        Given I have a course without group configurations
        When I click button 'Create new Group Configuration'
        And I set new name and description, add 1 additional group
        And I click button 'Cancel'
        Then I see that there is no new group configurations in the course
        """
        self.page.visit()

        self.assertEqual(len(self.page.experiment_group_configurations), 0)
        # Create new group configuration
        self.page.create_experiment_group_configuration()

        config = self.page.experiment_group_configurations[0]
        config.name = "Name of the Group Configuration"
        config.description = "Description of the group configuration."
        # Add new group
        config.add_group()  # Group C
        # Cancel the configuration
        config.cancel()

        self.assertEqual(len(self.page.experiment_group_configurations), 0)

    def test_can_cancel_editing_of_group_configuration(self):
        """
        Scenario: Ensure that editing of the group configuration can be canceled correctly.
        Given I have a course with group configuration
        When I go to the edit mode of the group configuration
        And I set new name and description, add 2 additional groups
        And I click button 'Cancel'
        Then I see that new changes were discarded
        """
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Name of the Group Configuration',
                        'Description of the group configuration.',
                        [Group("0", 'Group 0'), Group("1", 'Group 1')]
                    ),
                    create_user_partition_json(
                        1,
                        'Name of second Group Configuration',
                        'Second group configuration.',
                        [Group("0", 'Alpha'), Group("1", 'Beta'), Group("2", 'Gamma')]
                    ),
                ],
            },
        })
        self.page.visit()
        config = self.page.experiment_group_configurations[0]
        config.name = "New Group Configuration Name"
        config.description = "New Description of the group configuration."
        # Add 2 new groups
        config.add_group()  # Group C
        config.add_group()  # Group D
        # Cancel the configuration
        config.cancel()

        self._assert_fields(
            config,
            name="Name of the Group Configuration",
            description="Description of the group configuration.",
            groups=["Group 0", "Group 1"]
        )

    def test_group_configuration_validation(self):
        """
        Scenario: Ensure that validation of the group configuration works correctly.
        Given I have a course without group configurations
        And I create new group configuration with 2 default groups
        When I set only description and try to save
        Then I see error message "Group Configuration name is required."
        When I set a name
        And I delete the name of one of the groups and try to save
        Then I see error message "All groups must have a name"
        When I delete all the groups and try to save
        Then I see error message "There must be at least one group."
        When I add a group and try to save
        Then I see the group configuration is saved successfully
        """
        def try_to_save_and_verify_error_message(message):
            # Try to save
            config.save()
            # Verify that configuration is still in editing mode
            self.assertEqual(config.mode, 'edit')
            # Verify error message
            self.assertEqual(message, config.validation_message)

        self.page.visit()
        # Create new group configuration
        self.page.create_experiment_group_configuration()
        # Leave empty required field
        config = self.page.experiment_group_configurations[0]
        config.description = "Description of the group configuration."

        try_to_save_and_verify_error_message("Group Configuration name is required.")

        # Set required field
        config.name = "Name of the Group Configuration"
        config.groups[1].name = ''
        try_to_save_and_verify_error_message("All groups must have a name.")
        config.groups[0].remove()
        config.groups[0].remove()
        try_to_save_and_verify_error_message("There must be at least one group.")
        config.add_group()

        # Save the configuration
        config.save()

        self._assert_fields(
            config,
            name="Name of the Group Configuration",
            description="Description of the group configuration.",
            groups=["Group A"]
        )

    def test_group_configuration_empty_usage(self):
        """
        Scenario: When group configuration is not used, ensure that the link to outline page works correctly.
        Given I have a course without group configurations
        And I create new group configuration with 2 default groups
        Then I see a link to the outline page
        When I click on the outline link
        Then I see the outline page
        """
        # Create a new group configurations
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        "Name",
                        "Description.",
                        [Group("0", "Group A"), Group("1", "Group B")]
                    ),
                ],
            },
        })

        # Go to the Group Configuration Page and click on outline anchor
        self.page.visit()
        config = self.page.experiment_group_configurations[0]
        config.toggle()
        config.click_outline_anchor()

        # Waiting for the page load and verify that we've landed on course outline page
        EmptyPromise(
            lambda: self.outline_page.is_browser_on_page(), "loaded page {!r}".format(self.outline_page),
            timeout=30
        ).fulfill()

    def test_group_configuration_non_empty_usage(self):
        """
        Scenario: When group configuration is used, ensure that the links to units using a group configuration work correctly.
        Given I have a course without group configurations
        And I create new group configuration with 2 default groups
        And I create a unit and assign the newly created group configuration
        And open the Group Configuration page
        Then I see a link to the newly created unit
        When I click on the unit link
        Then I see correct unit page
        """
        # Create a new group configurations
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        "Name",
                        "Description.",
                        [Group("0", "Group A"), Group("1", "Group B")]
                    ),
                ],
            },
        })

        # Assign newly created group configuration to unit
        vertical = self.course_fixture.get_nested_xblocks(category="vertical")[0]
        self.course_fixture.create_xblock(
            vertical.locator,
            XBlockFixtureDesc('split_test', 'Test Content Experiment', metadata={'user_partition_id': 0})
        )
        unit = CourseOutlineUnit(self.browser, vertical.locator)

        # Go to the Group Configuration Page and click unit anchor
        self.page.visit()
        config = self.page.experiment_group_configurations[0]
        config.toggle()
        usage = config.usages[0]
        config.click_unit_anchor()

        unit = ContainerPage(self.browser, vertical.locator)
        # Waiting for the page load and verify that we've landed on the unit page
        EmptyPromise(
            lambda: unit.is_browser_on_page(), "loaded page {!r}".format(unit),
            timeout=30
        ).fulfill()

        self.assertIn(unit.name, usage)

    def test_can_delete_unused_group_configuration(self):
        """
        Scenario: Ensure that the user can delete unused group configuration.
        Given I have a course with 2 group configurations
        And I go to the Group Configuration page
        When I delete the Group Configuration with name "Configuration 1"
        Then I see that there is one Group Configuration
        When I edit the Group Configuration with name "Configuration 2"
        And I delete the Group Configuration with name "Configuration 2"
        Then I see that the are no Group Configurations
        """
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        'Configuration 1',
                        'Description of the group configuration.',
                        [Group("0", 'Group 0'), Group("1", 'Group 1')]
                    ),
                    create_user_partition_json(
                        1,
                        'Configuration 2',
                        'Second group configuration.',
                        [Group("0", 'Alpha'), Group("1", 'Beta'), Group("2", 'Gamma')]
                    )
                ],
            },
        })
        self.page.visit()

        self.assertEqual(len(self.page.experiment_group_configurations), 2)
        config = self.page.experiment_group_configurations[1]
        # Delete first group configuration via detail view
        config.delete()
        self.assertEqual(len(self.page.experiment_group_configurations), 1)

        config = self.page.experiment_group_configurations[0]
        config.edit()
        self.assertFalse(config.delete_button_is_disabled)
        # Delete first group configuration via edit view
        config.delete()
        self.assertEqual(len(self.page.experiment_group_configurations), 0)

    def test_cannot_delete_used_group_configuration(self):
        """
        Scenario: Ensure that the user cannot delete unused group configuration.
        Given I have a course with group configuration that is used in the Content Experiment
        When I go to the Group Configuration page
        Then I do not see delete button and I see a note about that
        When I edit the Group Configuration
        Then I do not see delete button and I see the note about that
        """
        # Create a new group configurations
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        "Name",
                        "Description.",
                        [Group("0", "Group A"), Group("1", "Group B")]
                    )
                ],
            },
        })
        vertical = self.course_fixture.get_nested_xblocks(category="vertical")[0]
        self.course_fixture.create_xblock(
            vertical.locator,
            XBlockFixtureDesc('split_test', 'Test Content Experiment', metadata={'user_partition_id': 0})
        )
        # Go to the Group Configuration Page and click unit anchor
        self.page.visit()

        config = self.page.experiment_group_configurations[0]
        self.assertTrue(config.delete_button_is_disabled)
        self.assertIn('Cannot delete when in use by an experiment', config.delete_note)

        config.edit()
        self.assertTrue(config.delete_button_is_disabled)
        self.assertIn('Cannot delete when in use by an experiment', config.delete_note)

    def test_easy_access_from_experiment(self):
        """
        Scenario: When a Content Experiment uses a Group Configuration,
        ensure that the link to that Group Configuration works correctly.

        Given I have a course with two Group Configurations
        And Content Experiment is assigned to one Group Configuration
        Then I see a link to Group Configuration
        When I click on the Group Configuration link
        Then I see the Group Configurations page
        And I see that appropriate Group Configuration is expanded.
        """
        # Create a new group configurations
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        "Name",
                        "Description.",
                        [Group("0", "Group A"), Group("1", "Group B")]
                    ),
                    create_user_partition_json(
                        1,
                        'Name of second Group Configuration',
                        'Second group configuration.',
                        [Group("0", 'Alpha'), Group("1", 'Beta'), Group("2", 'Gamma')]
                    ),
                ],
            },
        })

        # Assign newly created group configuration to unit
        vertical = self.course_fixture.get_nested_xblocks(category="vertical")[0]
        self.course_fixture.create_xblock(
            vertical.locator,
            XBlockFixtureDesc('split_test', 'Test Content Experiment', metadata={'user_partition_id': 1})
        )

        unit = ContainerPage(self.browser, vertical.locator)
        unit.visit()
        experiment = unit.xblocks[0]

        group_configuration_link_name = experiment.group_configuration_link_name

        experiment.go_to_group_configuration_page()
        self.page.wait_for_page()

        # Appropriate Group Configuration is expanded.
        self.assertFalse(self.page.experiment_group_configurations[0].is_expanded)
        self.assertTrue(self.page.experiment_group_configurations[1].is_expanded)

        self.assertEqual(
            group_configuration_link_name,
            self.page.experiment_group_configurations[1].name
        )

    def test_details_error_validation_message(self):
        """
        Scenario: When a Content Experiment uses a Group Configuration, ensure
        that an error validation message appears if necessary.

        Given I have a course with a Group Configuration containing two Groups
        And a Content Experiment is assigned to that Group Configuration
        When I go to the Group Configuration Page
        Then I do not see a error icon and message in the Group Configuration details view.
        When I add a Group
        Then I see an error icon and message in the Group Configuration details view
        """

        # Create group configuration and associated experiment
        config, _ = self.create_group_configuration_experiment([Group("0", "Group A"), Group("1", "Group B")], True)

        # Display details view
        config.toggle()
        # Check that error icon and message are not present
        self.assertFalse(config.details_error_icon_is_present)
        self.assertFalse(config.details_message_is_present)

        # Add a group
        config.toggle()
        config.edit()
        config.add_group()
        config.save()

        # Display details view
        config.toggle()
        # Check that error icon and message are present
        self.assertTrue(config.details_error_icon_is_present)
        self.assertTrue(config.details_message_is_present)
        self.assertIn(
            "This content experiment has issues that affect content visibility.",
            config.details_message_text
        )

    def test_details_warning_validation_message(self):
        """
        Scenario: When a Content Experiment uses a Group Configuration, ensure
        that a warning validation message appears if necessary.

        Given I have a course with a Group Configuration containing three Groups
        And a Content Experiment is assigned to that Group Configuration
        When I go to the Group Configuration Page
        Then I do not see a warning icon and message in the Group Configuration details view.
        When I remove a Group
        Then I see a warning icon and message in the Group Configuration details view
        """

        # Create group configuration and associated experiment
        config, _ = self.create_group_configuration_experiment([Group("0", "Group A"), Group("1", "Group B"), Group("2", "Group C")], True)

        # Display details view
        config.toggle()
        # Check that warning icon and message are not present
        self.assertFalse(config.details_warning_icon_is_present)
        self.assertFalse(config.details_message_is_present)

        # Remove a group
        config.toggle()
        config.edit()
        config.groups[2].remove()
        config.save()

        # Display details view
        config.toggle()
        # Check that warning icon and message are present
        self.assertTrue(config.details_warning_icon_is_present)
        self.assertTrue(config.details_message_is_present)
        self.assertIn(
            "This content experiment has issues that affect content visibility.",
            config.details_message_text
        )

    def test_edit_warning_message_empty_usage(self):
        """
        Scenario: When a Group Configuration is not used, ensure that there are no warning icon and message.

        Given I have a course with a Group Configuration containing two Groups
        When I edit the Group Configuration
        Then I do not see a warning icon and message
        """

        # Create a group configuration with no associated experiment and display edit view
        config = self.create_group_configuration_experiment([Group("0", "Group A"), Group("1", "Group B")], False)
        config.edit()
        # Check that warning icon and message are not present
        self.assertFalse(config.edit_warning_icon_is_present)
        self.assertFalse(config.edit_warning_message_is_present)

    def test_edit_warning_message_non_empty_usage(self):
        """
        Scenario: When a Group Configuration is used, ensure that there are a warning icon and message.

        Given I have a course with a Group Configuration containing two Groups
        When I edit the Group Configuration
        Then I see a warning icon and message
        """

        # Create a group configuration with an associated experiment and display edit view
        config, _ = self.create_group_configuration_experiment([Group("0", "Group A"), Group("1", "Group B")], True)
        config.edit()
        # Check that warning icon and message are present
        self.assertTrue(config.edit_warning_icon_is_present)
        self.assertTrue(config.edit_warning_message_is_present)
        self.assertIn(
            "This configuration is currently used in content experiments. If you make changes to the groups, you may need to edit those experiments.",
            config.edit_warning_message_text
        )

    def publish_unit_and_verify_groups_in_lms(self, courseware_page, group_names, publish=True):
        """
        Publish first unit in LMS and verify that Courseware page has given Groups
        """
        self.publish_unit_in_lms_and_view(courseware_page, publish)
        self.assertEqual(u'split_test', courseware_page.xblock_component_type())
        self.assertTrue(courseware_page.q(css=".split-test-select").is_present())
        rendered_group_names = self.get_select_options(page=courseware_page, selector=".split-test-select")
        self.assertListEqual(group_names, rendered_group_names)

    def test_split_test_LMS_staff_view(self):
        """
        Scenario: Ensure that split test is correctly rendered in LMS staff mode as it is
                  and after inactive group removal.

        Given I have a course with group configurations and split test that assigned to first group configuration
        Then I publish split test and view it in LMS in staff view
        And it is rendered correctly
        Then I go to group configuration and delete group
        Then I publish split test and view it in LMS in staff view
        And it is rendered correctly
        Then I go to split test and delete inactive vertical
        Then I publish unit and view unit in LMS in staff view
        And it is rendered correctly
        """

        config, split_test = self.create_group_configuration_experiment([Group("0", "Group A"), Group("1", "Group B"), Group("2", "Group C")], True)
        container = ContainerPage(self.browser, split_test.locator)

        # render in LMS correctly
        courseware_page = CoursewarePage(self.browser, self.course_id)
        self.publish_unit_and_verify_groups_in_lms(courseware_page, [u'Group A', u'Group B', u'Group C'])

        # I go to group configuration and delete group
        self.page.visit()
        self.page.q(css='.group-toggle').first.click()
        config.edit()
        config.groups[2].remove()
        config.save()
        self.page.q(css='.group-toggle').first.click()
        self._assert_fields(config, name="Name", description="Description", groups=["Group A", "Group B"])
        self.browser.close()
        self.browser.switch_to_window(self.browser.window_handles[0])

        # render in LMS to see how inactive vertical is rendered
        self.publish_unit_and_verify_groups_in_lms(
            courseware_page,
            [u'Group A', u'Group B', u'Group ID 2 (inactive)'],
            publish=False
        )

        self.browser.close()
        self.browser.switch_to_window(self.browser.window_handles[0])

        # I go to split test and delete inactive vertical
        container.visit()
        container.delete(0)

        # render in LMS again
        self.publish_unit_and_verify_groups_in_lms(courseware_page, [u'Group A', u'Group B'])
