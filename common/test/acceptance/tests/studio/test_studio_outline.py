"""
Acceptance tests for studio related to the outline page.
"""

from test_studio_general import CourseOutlineTest


class CreateSectionsTest(CourseOutlineTest):
    """
    Feature: Create new sections/subsections/units
    """
    def test_create_new_section_from_top_button(self):
        """
        Scenario: Create new section from button at top of page
            Given that I am on the course outline
            When I click the "+ Add section" button at the top of the page
            Then I see a new section added to the bottom of the page
            And the display name is in its editable form.
        """
        self.course_outline_page.visit()
        self.course_outline_page.top_create_section_button().click()
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
        self.course_outline_page.bottom_create_section_button().click()
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
        self.course_outline_page.top_create_section_button().click()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).add_subsection_button().click()
        subsections = self.course_outline_page.first_section().subsections()
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
        self.course_outline_page.top_create_section_button().click()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).add_subsection_button().click()
        self.assertEqual(len(self.course_outline_page.first_section().subsections()), 1)
        self.course_outline_page.sections[0].subsections[0].add_unit_button().click()
        unit_page = self.course_outline_page.sections[0].subsections[0].unit.go_to()
        self.assertTrue(unit_page.display_name_in_editable_form())
