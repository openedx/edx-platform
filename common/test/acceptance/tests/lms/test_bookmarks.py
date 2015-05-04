# -*- coding: utf-8 -*-
"""
End-to-end tests for the courseware unit bookmarks.
"""
import json
import requests

from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.bookmarks import BookmarksPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.common.logout import LogoutPage

from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...fixtures import LMS_BASE_URL
from ..helpers import EventsTestMixin, UniqueCourseTest, is_404_page


class BookmarksTestMixin(EventsTestMixin, UniqueCourseTest):
    """
    Mixin with helper methods for testing Bookmarks.
    """
    USERNAME = "STUDENT"
    EMAIL = "student@example.com"
    COURSE_TREE_INFO = [
        ['TestSection1', 'TestSubsection1', 'TestProblem1'],
        ['TestSection2', 'TestSubsection2', 'TestProblem2']
    ]

    def create_course_fixture(self):
        """ Create course fixture """
        self.course_fixture = CourseFixture(  # pylint: disable=attribute-defined-outside-init
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.course_fixture.add_children(
            XBlockFixtureDesc('chapter', self.COURSE_TREE_INFO[0][0]).add_children(
                XBlockFixtureDesc('sequential', self.COURSE_TREE_INFO[0][1]).add_children(
                    XBlockFixtureDesc('problem', self.COURSE_TREE_INFO[0][2])
                )
            ),
            XBlockFixtureDesc('chapter', self.COURSE_TREE_INFO[1][0]).add_children(
                XBlockFixtureDesc('sequential', self.COURSE_TREE_INFO[1][1]).add_children(
                    XBlockFixtureDesc('problem', self.COURSE_TREE_INFO[1][2])
                )
            )
        ).install()


class BookmarksTest(BookmarksTestMixin):
    """
    Tests to verify bookmarks functionality.
    """

    def setUp(self):
        """
        Initialize test setup.
        """
        super(BookmarksTest, self).setUp()

        self.course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.create_course_fixture()

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id).visit()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.courseware_page.visit()
        self.bookmarks = BookmarksPage(self.browser, self.course_id)

        # Use auto-auth to retrieve the session for a logged in user
        self.session = requests.Session()
        response = self.session.get(LMS_BASE_URL + "/auto_auth?username=STUDENT&email=student@example.com")
        self.assertTrue(response.ok, "Failed to get session info")

    def _bookmark_unit(self, course_id, usage_id):
        """ Bookmark a single unit """
        csrftoken = self.session.cookies['csrftoken']
        headers = {'Content-type': 'application/json', "X-CSRFToken": csrftoken}
        url = LMS_BASE_URL + "/api/bookmarks/v0/bookmarks/?course_id=" + course_id + '&fields=path'  # pylint: disable=protected-access
        data = json.dumps({'usage_id': usage_id})

        response = self.session.post(url, data=data, headers=headers, cookies=self.session.cookies)
        response = json.loads(response.text)
        self.assertTrue(response['usage_id'] == usage_id, "Failed to bookmark unit")

    def _bookmarks_blocks(self, xblocks):
        """ Bookmark all units in a course """
        for xblock in xblocks:
            self._bookmark_unit(self.course_id, usage_id=xblock.locator)

    def _delete_section(self, index):
        """ Delete a section at index `index` """

        # Logout and login as staff
        LogoutPage(self.browser).visit()
        AutoAuthPage(
            self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id, staff=True
        ).visit()

        # Visit course outline page in studio.
        self.course_outline_page.visit()
        self.course_outline_page.wait_for_page()

        self.course_outline_page.section_at(index).delete()

        # Logout and login as a student.
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id).visit()

        # Visit courseware as a student.
        self.courseware_page.visit()
        self.courseware_page.wait_for_page()

    def test_empty_bookmarks_list(self):
        """
        Scenario: An empty bookmarks list is shown if there are no bookmarked units.

        Given that I am a registered user
        And I visit my courseware page
        And I can see the Bookmarks button
        When I click on Bookmarks button
        Then I should see an empty bookmarks list
        And empty bookmarks list content is correct
        """
        self.assertTrue(self.bookmarks.bookmarks_button_visible())
        self.bookmarks.click_bookmarks_button()
        self.assertEqual(self.bookmarks.results_header_text(), 'MY BOOKMARKS')
        self.assertEqual(self.bookmarks.empty_header_text(), 'You have not bookmarked any courseware pages yet.')

        empty_list_text = ("Use bookmarks to help you easily return to courseware pages. To bookmark a page, "
                           "select Bookmark in the upper right corner of that page. To see a list of all your "
                           "bookmarks, select Bookmarks in the upper left corner of any courseware page.")
        self.assertEqual(self.bookmarks.empty_list_text(), empty_list_text)

    def test_bookmarks_list(self):
        """
        Scenario: A bookmarks list is shown if there are bookmarked units.

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked 2 units
        When I click on Bookmarks button
        Then I should see a bookmarked list with 2 bookmark links
        And breadcrumb trail is correct for a bookmark
        When I click on bookmarked link
        Then I can navigate to correct bookmarked unit
        """
        xblocks = self.course_fixture.get_nested_xblocks(category="problem")
        self._bookmarks_blocks(xblocks)

        self.bookmarks.click_bookmarks_button()
        self.assertTrue(self.bookmarks.results_present())
        self.assertEqual(self.bookmarks.results_header_text(), 'MY BOOKMARKS')
        self.assertEqual(self.bookmarks.count(), 2)

        bookmarked_breadcrumbs = self.bookmarks.breadcrumbs()

        # Verify bookmarked breadcrumbs and link navigation
        for index, problem_info in enumerate(self.COURSE_TREE_INFO):
            self.assertEqual(bookmarked_breadcrumbs[index], problem_info)
            self.bookmarks.click_bookmark(index)
            self.courseware_page.wait_for_page()
            self.assertEqual(xblocks[index].locator, self.courseware_page.active_usage_id())
            self.courseware_page.visit().wait_for_page()
            self.bookmarks.click_bookmarks_button()

    def test_unreachable_bookmark(self):
        """
        Scenario: We should get a HTTP 404 for an unreachable bookmark.

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked 2 units
        Then I delete a bookmarked unit
        Then I click on Bookmarks button
        And I should see a bookmarked list
        When I click on deleted bookmark
        Then I should navigated to 404 page
        """
        self._bookmarks_blocks(self.course_fixture.get_nested_xblocks(category="problem"))

        self._delete_section(0)

        self.bookmarks.click_bookmarks_button()
        self.assertTrue(self.bookmarks.results_present())
        self.assertEqual(self.bookmarks.count(), 2)

        self.bookmarks.click_bookmark(0)
        self.assertTrue(is_404_page(self.browser))
