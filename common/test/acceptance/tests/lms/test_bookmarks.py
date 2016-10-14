# -*- coding: utf-8 -*-
"""
End-to-end tests for the courseware unit bookmarks.
"""
from flaky import flaky
import json
from nose.plugins.attrib import attr
import requests

from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage as StudioAutoAuthPage
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage as LmsAutoAuthPage
from common.test.acceptance.pages.lms.bookmarks import BookmarksPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.course_nav import CourseNavPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.common import BASE_URL

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.tests.helpers import EventsTestMixin, UniqueCourseTest, is_404_page


class BookmarksTestMixin(EventsTestMixin, UniqueCourseTest):
    """
    Mixin with helper methods for testing Bookmarks.
    """
    USERNAME = "STUDENT"
    EMAIL = "student@example.com"

    def create_course_fixture(self, num_chapters):
        """
        Create course fixture

        Arguments:
            num_chapters: number of chapters to create
        """
        self.course_fixture = CourseFixture(  # pylint: disable=attribute-defined-outside-init
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        xblocks = []
        for index in range(num_chapters):
            xblocks += [
                XBlockFixtureDesc('chapter', 'TestSection{}'.format(index)).add_children(
                    XBlockFixtureDesc('sequential', 'TestSubsection{}'.format(index)).add_children(
                        XBlockFixtureDesc('vertical', 'TestVertical{}'.format(index))
                    )
                )
            ]
        self.course_fixture.add_children(*xblocks).install()

    def verify_event_data(self, event_type, event_data):
        """
        Verify emitted event data.

        Arguments:
            event_type: expected event type
            event_data: expected event data
        """
        actual_events = self.wait_for_events(event_filter={'event_type': event_type}, number_of_matches=1)
        self.assert_events_match(event_data, actual_events)


@attr(shard=8)
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

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.bookmarks_page = BookmarksPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)

        # Get session to be used for bookmarking units
        self.session = requests.Session()
        params = {'username': self.USERNAME, 'email': self.EMAIL, 'course_id': self.course_id}
        response = self.session.get(BASE_URL + "/auto_auth", params=params)
        self.assertTrue(response.ok, "Failed to get session")

    def _test_setup(self, num_chapters=2):
        """
        Setup test settings.

        Arguments:
            num_chapters: number of chapters to create in course
        """
        self.create_course_fixture(num_chapters)

        # Auto-auth register for the course.
        LmsAutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id).visit()

        self.courseware_page.visit()

    def _bookmark_unit(self, location):
        """
        Bookmark a unit

        Arguments:
            location (str): unit location
        """
        _headers = {
            'Content-type': 'application/json',
            'X-CSRFToken': self.session.cookies['csrftoken'],
        }
        params = {'course_id': self.course_id}
        data = json.dumps({'usage_id': location})
        response = self.session.post(
            BASE_URL + '/api/bookmarks/v1/bookmarks/',
            data=data,
            params=params,
            headers=_headers
        )
        self.assertTrue(response.ok, "Failed to bookmark unit")

    def _bookmark_units(self, num_units):
        """
        Bookmark first `num_units` units

        Arguments:
            num_units(int): Number of units to bookmarks
        """
        xblocks = self.course_fixture.get_nested_xblocks(category="vertical")
        for index in range(num_units):
            self._bookmark_unit(xblocks[index].locator)

    def _breadcrumb(self, num_units, modified_name=None):
        """
        Creates breadcrumbs for the first `num_units`

        Arguments:
            num_units(int): Number of units for which we want to create breadcrumbs

        Returns:
            list of breadcrumbs
        """
        breadcrumbs = []
        for index in range(num_units):
            breadcrumbs.append(
                [
                    'TestSection{}'.format(index),
                    'TestSubsection{}'.format(index),
                    modified_name if modified_name else 'TestVertical{}'.format(index)
                ]
            )
        return breadcrumbs

    def _delete_section(self, index):
        """ Delete a section at index `index` """

        # Logout and login as staff
        LogoutPage(self.browser).visit()
        StudioAutoAuthPage(
            self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id, staff=True
        ).visit()

        # Visit course outline page in studio.
        self.course_outline_page.visit()
        self.course_outline_page.wait_for_page()

        self.course_outline_page.section_at(index).delete()

        # Logout and login as a student.
        LogoutPage(self.browser).visit()
        LmsAutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id).visit()

        # Visit courseware as a student.
        self.courseware_page.visit()
        self.courseware_page.wait_for_page()

    def _toggle_bookmark_and_verify(self, bookmark_icon_state, bookmark_button_state, bookmarked_count):
        """
        Bookmark/Un-Bookmark a unit and then verify
        """
        self.assertTrue(self.courseware_page.bookmark_button_visible)
        self.courseware_page.click_bookmark_unit_button()
        self.assertEqual(self.courseware_page.bookmark_icon_visible, bookmark_icon_state)
        self.assertEqual(self.courseware_page.bookmark_button_state, bookmark_button_state)
        self.bookmarks_page.click_bookmarks_button()
        self.assertEqual(self.bookmarks_page.count(), bookmarked_count)

    def _verify_pagination_info(
            self,
            bookmark_count_on_current_page,
            header_text,
            previous_button_enabled,
            next_button_enabled,
            current_page_number,
            total_pages
    ):
        """
        Verify pagination info
        """
        self.assertEqual(self.bookmarks_page.count(), bookmark_count_on_current_page)
        self.assertEqual(self.bookmarks_page.get_pagination_header_text(), header_text)
        self.assertEqual(self.bookmarks_page.is_previous_page_button_enabled(), previous_button_enabled)
        self.assertEqual(self.bookmarks_page.is_next_page_button_enabled(), next_button_enabled)
        self.assertEqual(self.bookmarks_page.get_current_page_number(), current_page_number)
        self.assertEqual(self.bookmarks_page.get_total_pages, total_pages)

    def _navigate_to_bookmarks_list(self):
        """
        Navigates and verifies the bookmarks list page.
        """
        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.results_header_text(), 'My Bookmarks')

    def _verify_breadcrumbs(self, num_units, modified_name=None):
        """
        Verifies the breadcrumb trail.
        """
        bookmarked_breadcrumbs = self.bookmarks_page.breadcrumbs()

        # Verify bookmarked breadcrumbs.
        breadcrumbs = self._breadcrumb(num_units=num_units, modified_name=modified_name)
        breadcrumbs.reverse()
        self.assertEqual(bookmarked_breadcrumbs, breadcrumbs)

    def update_and_publish_block_display_name(self, modified_name):
        """
        Update and publish the block/unit display name.
        """
        self.course_outline_page.visit()
        self.course_outline_page.wait_for_page()

        self.course_outline_page.expand_all_subsections()
        section = self.course_outline_page.section_at(0)
        container_page = section.subsection_at(0).unit_at(0).go_to()

        self.course_fixture._update_xblock(container_page.locator, {  # pylint: disable=protected-access
            "metadata": {
                "display_name": modified_name
            }
        })

        container_page.visit()
        container_page.wait_for_page()

        self.assertEqual(container_page.name, modified_name)
        container_page.publish_action.click()

    def test_bookmark_button(self):
        """
        Scenario: Bookmark unit button toggles correctly

        Given that I am a registered user
        And I visit my courseware page
        For first 2 units
            I visit the unit
            And I can see the Bookmark button
            When I click on Bookmark button
            Then unit should be bookmarked
            Then I click again on the bookmark button
            And I should see a unit un-bookmarked
        """
        self._test_setup()
        for index in range(2):
            self.course_nav.go_to_section('TestSection{}'.format(index), 'TestSubsection{}'.format(index))

            self._toggle_bookmark_and_verify(True, 'bookmarked', 1)
            self.bookmarks_page.click_bookmarks_button(False)
            self._toggle_bookmark_and_verify(False, '', 0)

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
        self._test_setup()
        self.assertTrue(self.bookmarks_page.bookmarks_button_visible())
        self.bookmarks_page.click_bookmarks_button()
        self.assertEqual(self.bookmarks_page.results_header_text(), 'My Bookmarks')
        self.assertEqual(self.bookmarks_page.empty_header_text(), 'You have not bookmarked any courseware pages yet.')

        empty_list_text = ("Use bookmarks to help you easily return to courseware pages. To bookmark a page, "
                           "select Bookmark in the upper right corner of that page. To see a list of all your "
                           "bookmarks, select Bookmarks in the upper left corner of any courseware page.")
        self.assertEqual(self.bookmarks_page.empty_list_text(), empty_list_text)

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
        self._test_setup()
        self._bookmark_units(2)

        self._navigate_to_bookmarks_list()
        self._verify_breadcrumbs(num_units=2)

        self._verify_pagination_info(
            bookmark_count_on_current_page=2,
            header_text='Showing 1-2 out of 2 total',
            previous_button_enabled=False,
            next_button_enabled=False,
            current_page_number=1,
            total_pages=1
        )

        # get usage ids for units
        xblocks = self.course_fixture.get_nested_xblocks(category="vertical")
        xblock_usage_ids = [xblock.locator for xblock in xblocks]
        # Verify link navigation
        for index in range(2):
            self.bookmarks_page.click_bookmarked_block(index)
            self.courseware_page.wait_for_page()
            self.assertIn(self.courseware_page.active_usage_id(), xblock_usage_ids)
            self.courseware_page.visit().wait_for_page()
            self.bookmarks_page.click_bookmarks_button()

    def test_bookmark_shows_updated_breadcrumb_after_publish(self):
        """
        Scenario: A bookmark breadcrumb trail is updated after publishing the changed display name.

        Given that I am a registered user
        And I visit my courseware page
        And I can see bookmarked unit
        Then I visit unit page in studio
        Then I change unit display_name
        And I publish the changes
        Then I visit my courseware page
        And I visit bookmarks list page
        When I see the bookmark
        Then I can see the breadcrumb trail
        with updated display_name.
        """
        self._test_setup(num_chapters=1)
        self._bookmark_units(num_units=1)

        self._navigate_to_bookmarks_list()
        self._verify_breadcrumbs(num_units=1)

        LogoutPage(self.browser).visit()
        LmsAutoAuthPage(
            self.browser,
            username=self.USERNAME,
            email=self.EMAIL,
            course_id=self.course_id,
            staff=True
        ).visit()

        modified_name = "Updated name"
        self.update_and_publish_block_display_name(modified_name)

        LogoutPage(self.browser).visit()
        LmsAutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id).visit()
        self.courseware_page.visit()

        self._navigate_to_bookmarks_list()
        self._verify_breadcrumbs(num_units=1, modified_name=modified_name)

    @flaky  # TODO fix this flaky test
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
        self._test_setup(num_chapters=1)
        self._bookmark_units(1)
        self._delete_section(0)

        self._navigate_to_bookmarks_list()

        self._verify_pagination_info(
            bookmark_count_on_current_page=1,
            header_text='Showing 1 out of 1 total',
            previous_button_enabled=False,
            next_button_enabled=False,
            current_page_number=1,
            total_pages=1
        )

        self.bookmarks_page.click_bookmarked_block(0)
        self.assertTrue(is_404_page(self.browser))

    def test_page_size_limit(self):
        """
        Scenario: We can't get bookmarks more than default page size.

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 11 units available
        Then I click on Bookmarks button
        And I should see a bookmarked list
        And bookmark list contains 10 bookmarked items
        """
        self._test_setup(11)
        self._bookmark_units(11)
        self._navigate_to_bookmarks_list()

        self._verify_pagination_info(
            bookmark_count_on_current_page=10,
            header_text='Showing 1-10 out of 11 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    def test_pagination_with_single_page(self):
        """
        Scenario: Bookmarks list pagination is working as expected for single page
        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 2 units available
        Then I click on Bookmarks button
        And I should see a bookmarked list with 2 bookmarked items
        And I should see paging header and footer with correct data
        And previous and next buttons are disabled
        """
        self._test_setup(num_chapters=2)
        self._bookmark_units(num_units=2)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self._verify_pagination_info(
            bookmark_count_on_current_page=2,
            header_text='Showing 1-2 out of 2 total',
            previous_button_enabled=False,
            next_button_enabled=False,
            current_page_number=1,
            total_pages=1
        )

    def test_next_page_button(self):
        """
        Scenario: Next button is working as expected for bookmarks list pagination

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 12 units available

        Then I click on Bookmarks button
        And I should see a bookmarked list of 10 items
        And I should see paging header and footer with correct info

        Then I click on next page button in footer
        And I should be navigated to second page
        And I should see a bookmarked list with 2 items
        And I should see paging header and footer with correct info
        """
        self._test_setup(num_chapters=12)
        self._bookmark_units(num_units=12)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())

        self._verify_pagination_info(
            bookmark_count_on_current_page=10,
            header_text='Showing 1-10 out of 12 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

        self.bookmarks_page.press_next_page_button()
        self._verify_pagination_info(
            bookmark_count_on_current_page=2,
            header_text='Showing 11-12 out of 12 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

    def test_previous_page_button(self):
        """
        Scenario: Previous button is working as expected for bookmarks list pagination

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 12 units available
        And I click on Bookmarks button

        Then I click on next page button in footer
        And I should be navigated to second page
        And I should see a bookmarked list with 2 items
        And I should see paging header and footer with correct info

        Then I click on previous page button
        And I should be navigated to first page
        And I should see paging header and footer with correct info
        """
        self._test_setup(num_chapters=12)
        self._bookmark_units(num_units=12)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())

        self.bookmarks_page.press_next_page_button()
        self._verify_pagination_info(
            bookmark_count_on_current_page=2,
            header_text='Showing 11-12 out of 12 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

        self.bookmarks_page.press_previous_page_button()
        self._verify_pagination_info(
            bookmark_count_on_current_page=10,
            header_text='Showing 1-10 out of 12 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    def test_pagination_with_valid_page_number(self):
        """
        Scenario: Bookmarks list pagination works as expected for valid page number

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 12 units available

        Then I click on Bookmarks button
        And I should see a bookmarked list
        And I should see total page value is 2
        Then I enter 2 in the page number input
        And I should be navigated to page 2
        """
        self._test_setup(num_chapters=11)
        self._bookmark_units(num_units=11)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.get_total_pages, 2)

        self.bookmarks_page.go_to_page(2)
        self._verify_pagination_info(
            bookmark_count_on_current_page=1,
            header_text='Showing 11-11 out of 11 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

    def test_pagination_with_invalid_page_number(self):
        """
        Scenario: Bookmarks list pagination works as expected for invalid page number

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 11 units available
        Then I click on Bookmarks button
        And I should see a bookmarked list
        And I should see total page value is 2
        Then I enter 3 in the page number input
        And I should stay at page 1
        """
        self._test_setup(num_chapters=11)
        self._bookmark_units(num_units=11)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.get_total_pages, 2)

        self.bookmarks_page.go_to_page(3)
        self._verify_pagination_info(
            bookmark_count_on_current_page=10,
            header_text='Showing 1-10 out of 11 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    @flaky  # TODO fix this flaky test
    def test_bookmarked_unit_accessed_event(self):
        """
        Scenario: Bookmark events are emitted with correct data when we access/visit a bookmarked unit.

        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked a unit
        When I click on bookmarked unit
        Then `edx.course.bookmark.accessed` event is emitted
        """
        self._test_setup(num_chapters=1)
        self.reset_event_tracking()

        # create expected event data
        xblocks = self.course_fixture.get_nested_xblocks(category="vertical")
        event_data = [
            {
                'event': {
                    'bookmark_id': '{},{}'.format(self.USERNAME, xblocks[0].locator),
                    'component_type': xblocks[0].category,
                    'component_usage_id': xblocks[0].locator,
                }
            }
        ]
        self._bookmark_units(num_units=1)
        self.bookmarks_page.click_bookmarks_button()

        self._verify_pagination_info(
            bookmark_count_on_current_page=1,
            header_text='Showing 1 out of 1 total',
            previous_button_enabled=False,
            next_button_enabled=False,
            current_page_number=1,
            total_pages=1
        )

        self.bookmarks_page.click_bookmarked_block(0)
        self.verify_event_data('edx.bookmark.accessed', event_data)
