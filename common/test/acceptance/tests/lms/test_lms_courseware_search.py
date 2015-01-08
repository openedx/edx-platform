"""
Test courseware search
"""


from ..helpers import UniqueCourseTest
from ...pages.common.logout import LogoutPage
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.courseware_search import CoursewareSearchPage
from ...pages.common.logout import LogoutPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc


class CoursewareSearchTest(UniqueCourseTest):

    """
    Test courseware search.
    """

    USERNAME = 'STUDENT_TESTER'
    EMAIL = 'student101@example.com'

    def setUp(self):
        """
        Create search page and course content to search
        """
        super(CoursewareSearchTest, self).setUp()
        self.courseware_search_page = CoursewareSearchPage(self.browser, self.course_id)

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Section').add_children(
                XBlockFixtureDesc('sequential', 'Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Unit').add_children(
                        XBlockFixtureDesc('html', 'HTML Component', data="<html>Example of searchable content.</html>")
                    )
                )
            )
        ).install()

        self._auto_auth(self.USERNAME, self.EMAIL, False)

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
        self.courseware_search_page.visit()

    def test_search(self):
        """
        Make sure that you can search for something.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        search_results = self.courseware_search_page.visit().search_for_term('searchable')
        assert 'searchable' in search_results
