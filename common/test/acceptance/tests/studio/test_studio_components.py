"""
Acceptance tests for adding components in Studio.
"""
import ddt

from .base_studio_test import ContainerBase
from ...fixtures.course import XBlockFixtureDesc
from ...pages.studio.container import ContainerPage
from ...pages.studio.utils import add_component, add_components
from common.test.acceptance.pages.studio.settings_advanced import AdvancedSettingsPage


@ddt.ddt
class AdvancedProblemComponentTest(ContainerBase):
    """
    Feature: CMS.Component Adding
    As a course author, I want to be able to add a wide variety of components
    """
    def setUp(self, is_staff=True):
        """
        Create a course with a section, subsection, and unit to which to add the component.
        """
        super(AdvancedProblemComponentTest, self).setUp(is_staff=is_staff)

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

    @ddt.data(
        'Blank Advanced Problem',
        'Circuit Schematic Builder',
        'Custom Python-Evaluated Input',
        'Drag and Drop',
        'Image Mapped Input',
        'Math Expression Input',
        'Problem with Adaptive Hint',
    )
    def test_add_advanced_problem(self, component):
        """
        Scenario Outline: I can add Advanced Problem components
           Given I am in Studio editing a new unit
           When I add a "<Component>" "Advanced Problem" component
           Then I see a "<Component>" Problem component

        Examples:
               | Component                     |
               | Blank Advanced Problem        |
               | Circuit Schematic Builder     |
               | Custom Python-Evaluated Input |
               | Drag and Drop                 |
               | Image Mapped Input            |
               | Math Expression Input         |
               | Problem with Adaptive Hint    |
        """
        self.go_to_unit_page()
        page = ContainerPage(self.browser, None)
        add_component(page, 'problem', component, is_advanced_problem=True)
        problem = page.xblocks[1]
        self.assertEqual(problem.name, component)


class ComponentTest(ContainerBase):
    """
    Test class to add different components.
    (Not the advanced components)
    """
    def setUp(self, is_staff=True):
        """
        Create a course with a section, subsection, and unit to which to add the component.
        """
        super(ComponentTest, self).setUp(is_staff=is_staff)
        self.advanced_settings = AdvancedSettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

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

    def test_add_html_component(self):
        """
        Scenario: I can add HTML components
        Given I am in Studio editing a new unit
        When I add this type of HTML component:
            | Component               |
            | Text                    |
            | Announcement            |
            | Zooming Image Tool      |
            | Raw HTML                |
        Then I see HTML components in this order:
            | Component               |
            | Text                    |
            | Announcement            |
            | Zooming Image Tool      |
            | Raw HTML                |
        """
        # Components to be added
        components = ['Text', 'Announcement', 'Zooming Image Tool', 'Raw HTML']
        self.go_to_unit_page()
        container_page = ContainerPage(self.browser, None)
        # Add components
        add_components(container_page, 'html', components)
        problems = [x_block.name for x_block in container_page.xblocks[1:]]
        # Assert that components appear in same order as added.
        self.assertEqual(problems, components)

    def test_add_latex_html_component(self):
        """
        Scenario: I can add Latex HTML components
        Given I am in Studio editing a new unit
        Given I have enabled latex compiler
        When I add this type of HTML component:
            | Component               |
            | E-text Written in LaTeX |
        Then I see HTML components in this order:
            | Component               |
            | E-text Written in LaTeX |
        """
        # Latex component
        component = 'E-text Written in LaTeX'
        # Visit advanced settings page and enable latex compiler.
        self.advanced_settings.visit()
        self.advanced_settings.set('Enable LaTeX Compiler', 'True')
        self.go_to_unit_page()
        container_page = ContainerPage(self.browser, None)
        # Add latex component
        add_component(container_page, 'html', component, is_advanced_problem=False)
        problem = container_page.xblocks[1]
        # Asset that component has been added.
        self.assertEqual(problem.name, component)

    def test_common_problem_component(self):
        """
        Scenario: I can add Common Problem components
        Given I am in Studio editing a new unit
        When I add this type of Problem component:
            | Component            |`
            | Blank Common Problem |
            | Checkboxes           |
            | Dropdown             |
            | Multiple Choice      |
            | Numerical Input      |
            | Text Input           |
        Then I see Problem components in this order:
            | Component            |
            | Blank Common Problem |
            | Checkboxes           |
            | Dropdown             |
            | Multiple Choice      |
            | Numerical Input      |
            | Text Input           |
        """
        # Components to be added.
        components = ['Blank Common Problem', 'Checkboxes', 'Dropdown',
                      'Multiple Choice', 'Numerical Input', 'Text Input']

        self.go_to_unit_page()
        container_page = ContainerPage(self.browser, None)
        # Add components
        add_components(container_page, 'problem', components)
        problems = [x_block.name for x_block in container_page.xblocks[1:]]
        # Assert that components appear in the same order as added.
        self.assertEqual(problems, components)
