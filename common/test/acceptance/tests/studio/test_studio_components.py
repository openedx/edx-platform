"""
Acceptance tests for adding components in Studio.
"""
import ddt

from .base_studio_test import ContainerBase
from ...fixtures.course import XBlockFixtureDesc
from ...pages.studio.container import ContainerPage
from ...pages.studio.utils import add_component


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
