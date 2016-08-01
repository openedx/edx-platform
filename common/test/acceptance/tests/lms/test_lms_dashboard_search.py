"""
Test dashboard search
"""
import os
import json

from bok_choy.web_app_test import WebAppTest
from common.test.acceptance.tests.helpers import generate_course_key
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.pages.studio.utils import add_html_component, type_in_codemirror
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.lms.dashboard_search import DashboardSearchPage
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc


class DashboardSearchTest(WebAppTest):
    """
    Test dashboard search.
    """
    USERNAME = 'STUDENT_TESTER'
    EMAIL = 'student101@example.com'

    STAFF_USERNAME = "STAFF_TESTER"
    STAFF_EMAIL = "staff101@example.com"

    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def setUp(self):
        """
        Create the search page and courses to search.
        """
        # create test file in which index for this test will live
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)

        super(DashboardSearchTest, self).setUp()
        self.dashboard = DashboardSearchPage(self.browser)

        self.courses = {
            'A': {
                'org': 'test_org',
                'number': self.unique_id,
                'run': 'test_run_A',
                'display_name': 'Test Course A '
            },
            'B': {
                'org': 'test_org',
                'number': self.unique_id,
                'run': 'test_run_B',
                'display_name': 'Test Course B '
            },
            'C': {
                'org': 'test_org',
                'number': self.unique_id,
                'run': 'test_run_C',
                'display_name': 'Test Course C '
            }
        }

        # generate course fixtures and outline pages
        self.course_outlines = {}
        self.course_fixtures = {}
        for key, course_info in self.courses.iteritems():
            course_outline = CourseOutlinePage(
                self.browser,
                course_info['org'],
                course_info['number'],
                course_info['run']
            )

            course_fix = CourseFixture(
                course_info['org'],
                course_info['number'],
                course_info['run'],
                course_info['display_name']
            )

            course_fix.add_children(
                XBlockFixtureDesc('chapter', 'Section 1').add_children(
                    XBlockFixtureDesc('sequential', 'Subsection 1').add_children(
                        XBlockFixtureDesc('problem', 'Test Problem')
                    )
                )
            ).add_children(
                XBlockFixtureDesc('chapter', 'Section 2').add_children(
                    XBlockFixtureDesc('sequential', 'Subsection 2')
                )
            ).install()

            self.course_outlines[key] = course_outline
            self.course_fixtures[key] = course_fix

    def tearDown(self):
        """
        Remove index file
        """
        super(DashboardSearchTest, self).tearDown()
        os.remove(self.TEST_INDEX_FILENAME)

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, username=username, email=email, staff=staff).visit()

    def _studio_add_content(self, course_outline, html_content):
        """
        Add content to first section on studio course page.
        """
        # create a unit in course outline
        course_outline.visit()
        subsection = course_outline.section_at(0).subsection_at(0)
        subsection.expand_subsection()
        subsection.add_unit()

        # got to unit and create an HTML component and save (not publish)
        unit_page = ContainerPage(self.browser, None)
        unit_page.wait_for_page()
        add_html_component(unit_page, 0)
        unit_page.wait_for_element_presence('.edit-button', 'Edit button is visible')
        click_css(unit_page, '.edit-button', 0, require_notification=False)
        unit_page.wait_for_element_visibility('.modal-editor', 'Modal editor is visible')
        type_in_codemirror(unit_page, 0, html_content)
        click_css(unit_page, '.action-save', 0)

    def _studio_publish_content(self, course_outline):
        """
        Publish content in first section on studio course page.
        """
        course_outline.visit()
        subsection = course_outline.section_at(0).subsection_at(0)
        subsection.expand_subsection()
        unit = subsection.unit_at(0)
        unit.publish()

    def test_page_existence(self):
        """
        Make sure that the page exists.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.dashboard.visit()

    def test_search(self):
        """
        Make sure that you can search courses.
        """

        search_string = "dashboard"
        html_content = "dashboard search"

        # Enroll student in courses A & B, but not C
        for course_info in [self.courses['A'], self.courses['B']]:
            course_key = generate_course_key(
                course_info['org'],
                course_info['number'],
                course_info['run']
            )
            AutoAuthPage(
                self.browser,
                username=self.USERNAME,
                email=self.EMAIL,
                course_id=course_key
            ).visit()

        # Create content in studio without publishing.
        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)
        self._studio_add_content(self.course_outlines['A'], html_content)
        self._studio_add_content(self.course_outlines['B'], html_content)
        self._studio_add_content(self.course_outlines['C'], html_content)

        # Do a search, there should be no results shown.
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.dashboard.visit()
        self.dashboard.search_for_term(search_string)
        assert search_string not in self.dashboard.search_results.html[0]

        # Publish in studio to trigger indexing.
        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)
        self._studio_publish_content(self.course_outlines['A'])
        self._studio_publish_content(self.course_outlines['B'])
        self._studio_publish_content(self.course_outlines['C'])

        # Do the search again, this time we expect results from courses A & B, but not C
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.dashboard.visit()

        self.dashboard.search_for_term(search_string)
        assert self.dashboard.search_results.html[0].count(search_string) == 2
        assert self.dashboard.search_results.html[0].count(self.courses['A']['display_name']) == 1
        assert self.dashboard.search_results.html[0].count(self.courses['B']['display_name']) == 1
