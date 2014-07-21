"""
Acceptance tests for studio related to the outline page.
"""

from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.outline import CourseOutlinePage, ContainerPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc

from helpers import StudioCourseTest


class CourseOutlineTest(StudioCourseTest):
    """
    Tests that verify the sections name editable only inside headers in Studio Course Outline that you can get to
    when logged in and have a course.
    """

    COURSE_ID_SEPARATOR = "."

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(CourseOutlineTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True).visit()
        self.course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """ Install a course with sections/problems, tabs, updates, and handouts """
        course_fixture.add_children(XBlockFixtureDesc('chapter', 'Test Section'))


class CourseSectionTest(CourseOutlineTest):
    """
    Tests that verify the sections name editable only inside headers in Studio Course Outline that you can get to
    when logged in and have a course.
    """
    def test_section_name_editable_in_course_outline(self):
        """
        Check that section name is editable on course outline page.
        """
        self.course_outline_page.visit()
        new_name = u"Test Section New"
        section = self.course_outline_page.section_at(0)
        self.assertEqual(section.name, u"Test Section")
        section.change_name(new_name)
        self.browser.refresh()
        self.assertEqual(section.name, new_name)

    # TODO: re-enable when release date support is added back
    # def test_section_name_not_editable_inside_modal(self):
    #     """
    #     Check that section name is not editable inside "Section Release Date" modal on course outline page.
    #     """
    #     parent_css='div.modal-window'
    #     self.course_outline_page.click_release_date()
    #     section_name = self.course_outline_page.get_section_name(parent_css)[0]
    #     self.assertEqual(section_name, '"Test Section"')
    #     self.course_outline_page.click_section_name(parent_css)
    #     section_name_edit_form = self.course_outline_page.section_name_edit_form_present(parent_css)
    #     self.assertFalse(section_name_edit_form)


class CreateSectionsTest(CourseOutlineTest):
    """
    Feature: Create new sections/subsections/units
    """

    def populate_course_fixture(self, course_fixture):
        """ Start with a completely empty course to easily test adding things to it """
        pass

    def test_create_new_section_from_top_button(self):
        """
        Scenario: Create new section from button at top of page
            Given that I am on the course outline
            When I click the "+ Add section" button at the top of the page
            Then I see a new section added to the bottom of the page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_top_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.assertTrue(self.course_outline_page.section_at(0).in_editable_form())

    def test_create_new_section_from_bottom_button(self):
        """
        Scenario: Create new section from button at bottom of page
            Given that I am on the course outline
            When I click the "+ Add section" button at the bottom of the page
            Then I see a new section added to the bottom of the page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_bottom_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.assertTrue(self.course_outline_page.section_at(0).in_editable_form())

    def test_create_new_subsection(self):
        """
        Scenario: Create new subsection
            Given that I have created a section
            When I click the "+ Add subsection" button in that section
            Then I see a new subsection added to the bottom of the section
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_top_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).add_subsection()
        subsections = self.course_outline_page.section_at(0).subsections()
        self.assertEqual(len(subsections), 1)
        self.assertTrue(subsections[0].in_editable_form())

    def test_create_new_unit(self):
        """
        Scenario: Create new unit
            Given that I have created a section
            And that I have created a subsection within that section
            When I click the "+ Add unit" button in that subsection
            Then I am redirected to a New Unit page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.add_section_from_top_button()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).add_subsection()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).add_unit()
        unit_page = ContainerPage(self.browser, None)
        self.assertTrue(unit_page.display_name_in_editable_form())
