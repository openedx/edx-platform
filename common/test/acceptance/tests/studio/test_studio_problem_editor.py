"""
Acceptance tests for Problem component in studio
"""


from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.problem_editor import ProblemXBlockEditorView
from common.test.acceptance.pages.studio.utils import add_component
from common.test.acceptance.tests.helpers import skip_if_browser
from common.test.acceptance.tests.studio.base_studio_test import ContainerBase


class ProblemComponentEditor(ContainerBase):
    """
    Feature: CMS.Component Adding
    As a course author, I want to be able to add and edit Problem
    """

    def setUp(self, is_staff=True):
        """
        Create a course with a section, subsection, and unit to which to add the component.
        """
        super(ProblemComponentEditor, self).setUp(is_staff=is_staff)
        self.component = 'Blank Common Problem'
        self.unit = self.go_to_unit_page()
        self.container_page = ContainerPage(self.browser, None)
        # Add a Problem
        add_component(self.container_page, 'problem', self.component)
        self.component = self.unit.xblocks[1]
        self.container_page.edit()
        self.problem_editor = ProblemXBlockEditorView(self.browser, self.component.locator)

    def populate_course_fixture(self, course_fixture):
        """
        Adds a course fixture
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def test_user_can_modify_float_input(self):
        """
        Scenario: User can modify float input values
        Given I have created a Blank Common Problem
        When I edit and select Settings
            Then I can set the weight to "3.5"
            And my change to weight is persisted
            And I can revert to the default value of unset for weight
        """
        self.problem_editor.open_settings()
        self.problem_editor.set_field_val('Problem Weight', '3.5')
        self.problem_editor.save()

        # reopen settings
        self.container_page.edit()
        self.problem_editor.open_settings()

        field_value = self.problem_editor.get_field_val('Problem Weight')
        self.assertEqual(field_value, '3.5')
        self.problem_editor.revert_setting()
        field_value = self.problem_editor.get_field_val('Problem Weight')
        self.assertEqual(field_value, '', 'Component settings is not reverted to default')

    @skip_if_browser('firefox')
    # Lettuce tests run on chrome and chrome does not allow to enter
    # periods/dots in this field and consequently we have to save the
    # value as '234'. Whereas, bokchoy runs with the older version of
    # firefox on jenkins, which does not allow to save the value if it
    # has a period/dot. Clicking on save button after filling '2.34' in
    # field, does not do anything and test does not go any further.
    # So, it fails always.
    def test_user_cannot_type_decimal_values(self):
        """
        Scenario: User cannot type decimal values integer number field
        Given I have created a Blank Common Problem
        When I edit and select Settings
            Then if I set the max attempts to "2.34", it will persist as a valid integer
        """
        self.problem_editor.open_settings()
        self.problem_editor.set_field_val('Maximum Attempts', '2.34')
        self.problem_editor.save()

        # reopen settings
        self.container_page.edit()
        self.problem_editor.open_settings()

        field_value = self.problem_editor.get_field_val('Maximum Attempts')
        self.assertEqual(field_value, '234', "Decimal values are not allowed in this field")

    def test_settings_are_not_saved_on_cancel(self):
        """
        Scenario: Settings changes are not saved on Cancel
        Given I have created a Blank Common Problem
        When I edit and select Settings
            Then I can set the weight to "3.5"
        And I can modify the display name
            Then If I press Cancel my changes are not persisted
        """
        self.problem_editor.open_settings()
        self.problem_editor.set_field_val('Problem Weight', '3.5')
        self.problem_editor.cancel()

        # reopen settings
        self.container_page.edit()
        self.problem_editor.open_settings()

        field_value = self.problem_editor.get_field_val('Problem Weight')
        self.assertEqual(field_value, '', "Component setting should not appear updated if cancelled during editing")

    def test_cheat_sheet_visible_on_toggle(self):
        """
        Scenario: Cheat sheet visible on toggle
        Given I have created a Blank Common Problem
        And I can edit the problem
            Then I can see cheatsheet
        """
        self.problem_editor.toggle_cheatsheet()
        self.assertTrue(self.problem_editor.is_cheatsheet_present(), "Cheatsheet not present")
