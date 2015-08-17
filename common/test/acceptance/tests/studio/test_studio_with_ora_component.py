"""
Acceptance tests for Studio related to edit/save peer grading interface.
"""

from ...fixtures.course import XBlockFixtureDesc
from ...pages.studio.import_export import ExportCoursePage
from ...pages.studio.component_editor import ComponentEditorView
from ...pages.studio.overview import CourseOutlinePage
from base_studio_test import StudioCourseTest
from ..helpers import load_data_str


class ORAComponentTest(StudioCourseTest):
    """
    Tests tht edit/save is working correctly when link_to_location
    is given in peer grading interface settings.
    """

    def setUp(self):
        super(ORAComponentTest, self).setUp()

        self.course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )
        self.export_page = ExportCoursePage(
            self.browser,
            self.course_info['org'], self.course_info['number'], self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """
        Return a test course fixture containing a discussion component.
        """

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc(
                            'combinedopenended',
                            "Peer Problem",
                            data=load_data_str('ora_peer_problem.xml'),
                            metadata={
                                'graded': True,
                            },
                        ),
                        XBlockFixtureDesc('peergrading', 'Peer Module'),
                    )
                )
            )
        )

    def _go_to_unit_page(self, section_name='Test Section', subsection_name='Test Subsection', unit_name='Test Unit'):
        self.course_outline_page.visit()
        subsection = self.course_outline_page.section(section_name).subsection(subsection_name)
        return subsection.expand_subsection().unit(unit_name).go_to()

    def test_edit_save_and_export(self):
        """
        Ensure that edit/save is working correctly with link_to_location
        in peer interface settings.
        """
        self.course_outline_page.visit()
        unit = self._go_to_unit_page()
        peer_problem_location = unit.xblocks[1].locator

        # Problem location should contain "combinedopeneneded".
        self.assertIn("combinedopenended", peer_problem_location)
        component = unit.xblocks[2]

        # Interface component name should be "Peer Module".
        self.assertEqual(component.name, "Peer Module")
        component.edit()
        component_editor = ComponentEditorView(self.browser, component.locator)
        component_editor.set_field_value_and_save('Link to Problem Location', peer_problem_location)

        # Verify that we can edit component again after saving and link_to_location is present.
        component.edit()
        location_input_element = component_editor.get_setting_element("Link to Problem Location")
        self.assertEqual(
            location_input_element.get_attribute('value'),
            peer_problem_location
        )

    def test_verify_ora1_deprecation_message(self):
        """
        Scenario: Verifies the ora1 deprecation message on ora components.

        Given I have a course with ora 1 components
        When I go to the unit page
        Then I see a deprecation error message in ora 1 components.
        """
        self.course_outline_page.visit()
        unit = self._go_to_unit_page()

        for xblock in unit.xblocks:
            self.assertTrue(xblock.has_validation_error)
            self.assertEqual(
                xblock.validation_error_text,
                "ORA1 is no longer supported. To use this assessment, "
                "replace this ORA1 component with an ORA2 component."
            )
