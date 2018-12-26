"""
Acceptance tests for Problem component in studio
"""
from common.test.acceptance.tests.studio.base_studio_test import ContainerBase
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.studio.utils import add_component
from common.test.acceptance.pages.studio.problem_editor import ProblemXBlockEditorView


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

    def test_user_can_view_metadata(self):
        """
        Scenario: User can view metadata
        Given I have created a Blank Common Problem
        When I edit and select Settings
        Then I see the advanced settings and their expected values
        And Edit High Level Source is not visible
        """
        expected_default_settings = {
            'Display Name': u'Blank Common Problem',
            'Matlab API key': u'',
            'Maximum Attempts': u'',
            'Problem Weight': u'',
            'Randomization': u'Never',
            'Show Answer': u'Finished',
            'Show Reset Button': u'False',
            'Timer Between Attempts': u'0'
        }
        self.problem_editor.open_settings()
        settings = self.problem_editor.get_settings()
        self.assertEqual(expected_default_settings, settings)
        self.assertFalse(self.problem_editor.is_latex_compiler_present())

    def test_user_can_modify_string_values(self):
        """
        Given I have created a Blank Common Problem
        When I edit and select Settings
        Then I can modify the display name
        And my display name change is persisted on save
        """
        self.problem_editor.open_settings()
        self.problem_editor.set_field_val('Display Name', 'New Name')
        self.problem_editor.save()
        component_name = self.unit.xblock_titles[0]
        self.assertEqual(component_name, 'New Name')

    def test_user_can_specify_special_characters(self):
        """
        Scenario: User can specify special characters in String values
        Given I have created a Blank Common Problem
        When I edit and select Settings
        Then I can specify special characters in the display name
        And my special characters are persisted on save
        """
        self.problem_editor.open_settings()
        self.problem_editor.set_field_val('Display Name', '&&&')
        self.problem_editor.save()
        component_name = self.unit.xblock_titles[0]
        self.assertEqual(component_name, '&&&')
