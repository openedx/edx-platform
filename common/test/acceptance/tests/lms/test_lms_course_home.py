# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS that utilize the course home page and course outline.
"""
from contextlib import contextmanager
from nose.plugins.attrib import attr

from ..helpers import auto_auth, load_data_str, UniqueCourseTest
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.lms.bookmarks import BookmarksPage
from ...pages.lms.course_home import CourseHomePage
from ...pages.lms.courseware import CoursewarePage


class CourseHomeBaseTest(UniqueCourseTest):
    """
    Provides base setup for course home tests.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(CourseHomeBaseTest, self).setUp()

        self.course_home_page = CourseHomePage(self.browser, self.course_id)
        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections and problems
        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('static_tab', 'Test Static Tab', data=r"static tab data with mathjax \(E=mc^2\)"),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                    XBlockFixtureDesc('html', 'Test HTML'),
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2'),
                XBlockFixtureDesc('sequential', 'Test Subsection 3').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem A', data=load_data_str('multiple_choice.xml'))
                ),
            )
        ).install()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)


class CourseHomeTest(CourseHomeBaseTest):
    """
    Tests the course home page with course outline.
    """

    def test_course_home(self):
        """
        Smoke test of course outline, breadcrumbs to and from cours outline, and bookmarks.
        """
        self.course_home_page.visit()

        # TODO: TNL-6546: Remove unified_course_view.
        self.course_home_page.unified_course_view = True
        self.courseware_page.nav.unified_course_view = True

        # Check that the tab lands on the course home page.
        self.assertTrue(self.course_home_page.is_browser_on_page())

        # Check that the course navigation appears correctly
        EXPECTED_SECTIONS = {
            'Test Section': ['Test Subsection'],
            'Test Section 2': ['Test Subsection 2', 'Test Subsection 3']
        }

        actual_sections = self.course_home_page.outline.sections
        for section, subsections in EXPECTED_SECTIONS.iteritems():
            self.assertIn(section, actual_sections)
            self.assertEqual(actual_sections[section], EXPECTED_SECTIONS[section])

        # Navigate to a particular section
        self.course_home_page.outline.go_to_section('Test Section', 'Test Subsection')

        # Check the sequence items on the courseware page
        EXPECTED_ITEMS = ['Test Problem 1', 'Test Problem 2', 'Test HTML']

        actual_items = self.courseware_page.nav.sequence_items
        self.assertEqual(len(actual_items), len(EXPECTED_ITEMS))
        for expected in EXPECTED_ITEMS:
            self.assertIn(expected, actual_items)

        # Use outline breadcrumb to get back to course home page.
        self.courseware_page.nav.go_to_outline()

        # Navigate to a particular section other than the default landing section.
        self.course_home_page.outline.go_to_section('Test Section 2', 'Test Subsection 3')
        self.assertTrue(self.courseware_page.nav.is_on_section('Test Section 2', 'Test Subsection 3'))

        # Verify that we can navigate to the bookmarks page
        self.course_home_page.visit()
        self.course_home_page.click_bookmarks_button()
        bookmarks_page = BookmarksPage(self.browser, self.course_id)
        self.assertTrue(bookmarks_page.is_browser_on_page())

        # Test "Resume Course" button from header
        self.course_home_page.visit()
        self.course_home_page.resume_course_from_header()
        self.assertTrue(self.courseware_page.nav.is_on_section('Test Section 2', 'Test Subsection 3'))

        # Test "Resume Course" button from within outline
        self.course_home_page.visit()
        self.course_home_page.outline.resume_course_from_outline()
        self.assertTrue(self.courseware_page.nav.is_on_section('Test Section 2', 'Test Subsection 3'))


@attr('a11y')
class CourseHomeA11yTest(CourseHomeBaseTest):
    """
    Tests the accessibility of the course home page with course outline.
    """

    def setUp(self):
        super(CourseHomeA11yTest, self).setUp()

    def test_course_home_a11y(self):
        """
        Test the accessibility of the course home page with course outline.
        """
        course_home_page = CourseHomePage(self.browser, self.course_id)
        course_home_page.visit()
        course_home_page.a11y_audit.check_for_accessibility_errors()
