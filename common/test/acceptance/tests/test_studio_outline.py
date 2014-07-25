"""
Acceptance tests for studio related to the outline page.
"""

from bok_choy.promise import EmptyPromise

from ..pages.studio.overview import CourseOutlinePage, ContainerPage, ExpandCollapseLinkState
from ..pages.lms.courseware import CoursewarePage
from ..fixtures.course import XBlockFixtureDesc

from .base_studio_test import StudioCourseTest


class CourseOutlineTest(StudioCourseTest):
    """
    Base class for all course outline tests
    """

    COURSE_ID_SEPARATOR = "."

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(CourseOutlineTest, self).setUp()
        self.course_outline_page = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )

    def populate_course_fixture(self, course_fixture):
        """ Install a course with sections/problems, tabs, updates, and handouts """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('html', 'Test HTML Component'),
                        XBlockFixtureDesc('discussion', 'Test Discussion Component')
                    )
                )
            )
        )


class EditNamesTest(CourseOutlineTest):
    """
    Feature: Click-to-edit section/subsection names
    """

    __test__ = True

    def set_name_and_verify(self, item, old_name, new_name, expected_name):
        """
        Changes the display name of item from old_name to new_name, then verifies that its value is expected_name.
        """
        self.assertEqual(item.name, old_name)
        item.change_name(new_name)
        self.assertFalse(item.in_editable_form())
        self.assertEqual(item.name, expected_name)

    def test_edit_section_name(self):
        """
        Scenario: Click-to-edit section name
            Given that I have created a section
            When I click on the name of section
            Then the section name becomes editable
            And given that I have edited the section name
            When I click outside of the edited section name
            Then the section name saves
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0),
            'Test Section',
            'Changed',
            'Changed'
        )

    def test_edit_subsection_name(self):
        """
        Scenario: Click-to-edit subsection name
            Given that I have created a subsection
            When I click on the name of subsection
            Then the subsection name becomes editable
            And given that I have edited the subsection name
            When I click outside of the edited subsection name
            Then the subsection name saves
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0).subsection_at(0),
            'Test Subsection',
            'Changed',
            'Changed'
        )

    def test_edit_empty_section_name(self):
        """
        Scenario: Click-to-edit section name, enter empty name
            Given that I have created a section
            And I have clicked to edit the name of the section
            And I have entered an empty section name
            When I click outside of the edited section name
            Then the section name does not change
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0),
            'Test Section',
            '',
            'Test Section'
        )

    def test_edit_empty_subsection_name(self):
        """
        Scenario: Click-to-edit subsection name, enter empty name
            Given that I have created a subsection
            And I have clicked to edit the name of the subsection
            And I have entered an empty subsection name
            When I click outside of the edited subsection name
            Then the subsection name does not change
            And becomes non-editable
        """
        self.course_outline_page.visit()
        self.set_name_and_verify(
            self.course_outline_page.section_at(0).subsection_at(0),
            'Test Subsection',
            '',
            'Test Subsection'
        )


class CreateSectionsTest(CourseOutlineTest):
    """
    Feature: Create new sections/subsections/units
    """

    __test__ = True

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
        EmptyPromise(unit_page.is_browser_on_page, 'Browser is on the unit page').fulfill()
        self.assertTrue(unit_page.is_inline_editing_display_name())


class DeleteContentTest(CourseOutlineTest):
    """
    Feature: Deleting sections/subsections/units
    """

    __test__ = True

    def test_delete_section(self):
        """
        Scenario: Delete section
            Given that I am on the course outline
            When I click the delete button for a section on the course outline
            Then I should receive a confirmation message, asking me if I really want to delete the section
            When I click "Yes, I want to delete this component"
            Then the confirmation message should close
            And the section should immediately be deleted from the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).delete()
        self.assertEqual(len(self.course_outline_page.sections()), 0)

    def test_cancel_delete_section(self):
        """
        Scenario: Cancel delete of section
            Given that I clicked the delte button for a section on the course outline
            And I received a confirmation message, asking me if I really want to delete the component
            When I click "Cancel"
            Then the confirmation message should close
            And the section should remain in the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.sections()), 1)
        self.course_outline_page.section_at(0).delete(cancel=True)
        self.assertEqual(len(self.course_outline_page.sections()), 1)

    def test_delete_subsection(self):
        """
        Scenario: Delete subsection
            Given that I am on the course outline
            When I click the delete button for a subsection on the course outline
            Then I should receive a confirmation message, asking me if I really want to delete the subsection
            When I click "Yes, I want to delete this component"
            Then the confiramtion message should close
            And the subsection should immediately be deleted from the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).delete()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 0)

    def test_cancel_delete_subsection(self):
        """
        Scenario: Cancel delete of subsection
            Given that I clicked the delete button for a subsection on the course outline
            And I received a confirmation message, asking me if I really want to delete the subsection
            When I click "cancel"
            Then the confirmation message should close
            And the subsection should remain in the course outline
        """
        self.course_outline_page.visit()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).delete(cancel=True)
        self.assertEqual(len(self.course_outline_page.section_at(0).subsections()), 1)

    def test_delete_unit(self):
        """
        Scenario: Delete unit
            Given that I am on the course outline
            When I click the delete button for a unit on the course outline
            Then I should receive a confirmation message, asking me if I really want to delete the unit
            When I click "Yes, I want to delete this unit"
            Then the confirmation message should close
            And the unit should immediately be deleted from the course outline
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).subsection_at(0).toggle_expand()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).unit_at(0).delete()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 0)

    def test_cancel_delete_unit(self):
        """
        Scenario: Cancel delete of unit
            Given that I clicked the delete button for a unit on the course outline
            And I received a confirmation message, asking me if I really want to delete the unit
            When I click "Cancel"
            Then the confirmation message should close
            And the unit should remain in the course outline
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).subsection_at(0).toggle_expand()
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 1)
        self.course_outline_page.section_at(0).subsection_at(0).unit_at(0).delete(cancel=True)
        self.assertEqual(len(self.course_outline_page.section_at(0).subsection_at(0).units()), 1)

    def test_delete_all_no_content_message(self):
        """
        Scenario: Delete all sections/subsections/units in a course, "no content" message should appear
            Given that I delete all sections, subsections, and units in a course
            When I visit the course outline
            Then I will see a message that says, "You haven't added any content to this course yet"
            Add see a + Add Section button
        """
        self.course_outline_page.visit()
        self.assertFalse(self.course_outline_page.has_no_content_message)
        self.course_outline_page.section_at(0).delete()
        self.assertEqual(len(self.course_outline_page.sections()), 0)
        self.assertTrue(self.course_outline_page.has_no_content_message)


class ExpandCollapseMultipleSectionsTest(CourseOutlineTest):
    """
    Feature: Courses with multiple sections can expand and collapse all sections.
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with a course with two sections """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit 2')
                )
            )
        )

    def verify_all_sections(self, collapsed):
        """
        Verifies that all sections are collapsed if collapsed is True, otherwise all expanded.
        """
        for section in self.course_outline_page.sections():
            self.assertEqual(collapsed, section.is_collapsed)

    def toggle_all_sections(self):
        """
        Toggles the expand collapse state of all sections.
        """
        for section in self.course_outline_page.sections():
            section.toggle_expand()

    def test_expanded_by_default(self):
        """
        Scenario: The default layout for the outline page is to show sections in expanded view
            Given I have a course with sections
            When I navigate to the course outline page
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.verify_all_sections(collapsed=False)

    def test_no_expand_link_for_empty_course(self):
        """
        Scenario: Collapse link is removed after last section of a course is deleted
            Given I have a course with multiple sections
            And I navigate to the course outline page
            When I will confirm all alerts
            And I press the "section" delete icon
            Then I do not see the "Collapse All Sections" link
            And I will see a message that says "You haven't added any content to this course yet"
        """
        self.course_outline_page.visit()
        for section in self.course_outline_page.sections():
            section.delete()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)
        self.assertTrue(self.course_outline_page.has_no_content_message)

    def test_collapse_all_when_all_expanded(self):
        """
        Scenario: Collapse all sections when all sections are expanded
            Given I navigate to the outline page of a course with sections
            And all sections are expanded
            When I click the "Collapse All Sections" link
            Then I see the "Expand All Sections" link
            And all sections are collapsed
        """
        self.course_outline_page.visit()
        self.verify_all_sections(collapsed=False)
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.verify_all_sections(collapsed=True)

    def test_collapse_all_when_some_expanded(self):
        """
        Scenario: Collapsing all sections when 1 or more sections are already collapsed
            Given I navigate to the outline page of a course with sections
            And all sections are expanded
            When I collapse the first section
            And I click the "Collapse All Sections" link
            Then I see the "Expand All Sections" link
            And all sections are collapsed
        """
        self.course_outline_page.visit()
        self.verify_all_sections(collapsed=False)
        self.course_outline_page.section_at(0).toggle_expand()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.verify_all_sections(collapsed=True)

    def test_expand_all_when_all_collapsed(self):
        """
        Scenario: Expanding all sections when all sections are collapsed
            Given I navigate to the outline page of a course with multiple sections
            And I click the "Collapse All Sections" link
            When I click the "Expand All Sections" link
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.verify_all_sections(collapsed=False)

    def test_expand_all_when_some_collapsed(self):
        """
        Scenario: Expanding all sections when 1 or more sections are already expanded
            Given I navigate to the outline page of a course with multiple sections
            And I click the "Collapse All Sections" link
            When I expand the first section
            And I click the "Expand All Sections" link
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.EXPAND)
        self.course_outline_page.section_at(0).toggle_expand()
        self.course_outline_page.toggle_expand_collapse()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.verify_all_sections(collapsed=False)


class ExpandCollapseSingleSectionTest(CourseOutlineTest):
    """
    Feature: Courses with a single section can expand and collapse all sections.
    """

    __test__ = True

    def test_no_expand_link_for_empty_course(self):
        """
        Scenario: Collapse link is removed after last section of a course is deleted
            Given I have a course with one section
            And I navigate to the course outline page
            When I will confirm all alerts
            And I press the "section" delete icon
            Then I do not see the "Collapse All Sections" link
            And I will see a message that says "You haven't added any content to this course yet"
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).delete()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)
        self.assertTrue(self.course_outline_page.has_no_content_message)


class ExpandCollapseEmptyTest(CourseOutlineTest):
    """
    Feature: Courses with no sections initially can expand and collapse all sections after addition.
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with an empty course """
        pass

    def test_no_expand_link_for_empty_course(self):
        """
        Scenario: Expand/collapse for a course with no sections
            Given I have a course with no sections
            When I navigate to the course outline page
            Then I do not see the "Collapse All Sections" link
        """
        self.course_outline_page.visit()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)

    def test_link_appears_after_section_creation(self):
        """
        Scenario: Collapse link appears after creating first section of a course
            Given I have a course with no sections
            When I navigate to the course outline page
            And I add a section
            Then I see the "Collapse All Sections" link
            And all sections are expanded
        """
        self.course_outline_page.visit()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.MISSING)
        self.course_outline_page.add_section_from_top_button()
        self.assertEquals(self.course_outline_page.expand_collapse_link_state, ExpandCollapseLinkState.COLLAPSE)
        self.assertFalse(self.course_outline_page.section_at(0).is_collapsed)


class DefaultStatesEmptyTest(CourseOutlineTest):
    """
    Feature: Misc course outline default states/actions when starting with an empty course
    """

    __test__ = True

    def populate_course_fixture(self, course_fixture):
        """ Start with an empty course """
        pass

    def test_empty_course_message(self):
        """
        Scenario: Empty course state
            Given that I am in a course with no sections, subsections, nor units
            When I visit the course outline
            Then I will see a message that says "You haven't added any content to this course yet"
            And see a + Add Section button
        """
        self.course_outline_page.visit()
        self.assertTrue(self.course_outline_page.has_no_content_message)
        self.assertTrue(self.course_outline_page.bottom_add_section_button.is_present())


class DefaultStatesContentTest(CourseOutlineTest):
    """
    Feature: Misc course outline default states/actions when starting with a course with content
    """

    __test__ = True

    def test_view_live(self):
        """
        Scenario: View Live version from course outline
            Given that I am on the course outline
            When I click the "View Live" button
            Then a new tab will open to the course on the LMS
        """
        self.course_outline_page.visit()
        self.course_outline_page.view_live()
        courseware = CoursewarePage(self.browser, self.course_id)
        courseware.wait_for_page()
        self.assertEqual(courseware.num_xblock_components, 2)
        self.assertEqual(courseware.xblock_component_type(0), 'html')
        self.assertEqual(courseware.xblock_component_type(1), 'discussion')


class UnitNavigationTest(CourseOutlineTest):
    """
    Feature: Navigate to units
    """

    __test__ = True

    def test_navigate_to_unit(self):
        """
        Scenario: Click unit name to navigate to unit page
            Given that I have expanded a section/subsection so I can see unit names
            When I click on a unit name
            Then I will be taken to the appropriate unit page
        """
        self.course_outline_page.visit()
        self.course_outline_page.section_at(0).subsection_at(0).toggle_expand()
        unit = self.course_outline_page.section_at(0).subsection_at(0).unit_at(0).go_to()
        self.assertTrue(unit.is_browser_on_page)
