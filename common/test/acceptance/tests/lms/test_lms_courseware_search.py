"""
Test courseware search
"""

from ..helpers import UniqueCourseTest
from ...pages.common.logout import LogoutPage
from ...pages.studio.utils import add_html_component, click_css, type_in_codemirror
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.container import ContainerPage
from ...pages.lms.courseware_search import CoursewareSearchPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc


class CoursewareSearchTest(UniqueCourseTest):

    """
    Test courseware search.
    """

    USERNAME = 'STUDENT_TESTER'
    EMAIL = 'student101@example.com'
    HTML_CONTENT = """
            Someday I'll wish upon a star
            And wake up where the clouds are far
            Behind me.
            Where troubles melt like lemon drops
            Away above the chimney tops
            That's where you'll find me.
        """
    SEARCH_STRING = "chimney"

    def setUp(self):
        """
        Create search page and course content to search
        """
        super(CoursewareSearchTest, self).setUp()
        self.courseware_search_page = CoursewareSearchPage(self.browser, self.course_id)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Section').add_children(
                XBlockFixtureDesc('sequential', 'Subsection')
            )
        ).install()

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=staff).visit()

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()

    def _studio_publish_content(self):
        self.course_outline.visit()
        subsection = self.course_outline.section_at(0).subsection_at(0)
        subsection.toggle_expand()
        unit = subsection.unit_at(0)
        unit.publish()

    def _studio_add_content(self):

        # create a unit in course outline
        self.course_outline.visit()
        subsection = self.course_outline.section_at(0).subsection_at(0)
        subsection.toggle_expand()
        subsection.add_unit()

        # got to unit and create an HTML component and save (not publish)
        unit_page = ContainerPage(self.browser, None)
        unit_page.wait_for_page()
        add_html_component(unit_page, 0)
        unit_page.wait_for_element_presence('.edit-button', 'Edit button is visible')
        click_css(unit_page, '.edit-button', 0, require_notification=False)
        unit_page.wait_for_element_visibility('.modal-editor', 'Modal editor is visible')
        type_in_codemirror(unit_page, 0, self.HTML_CONTENT)
        click_css(unit_page, '.action-save', 0)

    def test_search(self):
        """
        Make sure that you can search for something.
        """

        # Create content in studio without publishing.
        self._auto_auth('STAFF_USER', 'staff101@example.com', True)
        self._studio_add_content()

        # Do a search, there should be no results shown.
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit().search_for_term(self.SEARCH_STRING)
        self.browser.save_screenshot('search1.png')
        assert self.SEARCH_STRING not in self.courseware_search_page.search_results.html[0]

        # Publish in studio to trigger indexing.
        self._auto_auth('STAFF_USER', 'staff101@example.com', True)
        self._studio_publish_content()

        # Do the search again, this time we expect results.
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit().search_for_term(self.SEARCH_STRING)
        self.browser.save_screenshot('search2.png')
        assert self.SEARCH_STRING in self.courseware_search_page.search_results.html[0]
