# -*- coding: utf-8 -*-
"""
End-to-end tests for the courseware unit bookmarks.
"""

from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.bookmarks import BookmarksPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.common.logout import LogoutPage

from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ..helpers import EventsTestMixin, UniqueCourseTest, is_404_page


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

    def _test_setup(self, num_chapters=2):
        """
        Setup test settings.

        Arguments:
            num_chapters: number of chapters to create in course
        """
        self.create_course_fixture(num_chapters)

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL, course_id=self.course_id).visit()

        self.courseware_page.visit()

    def _bookmark_unit(self, index):
        """
        Bookmark a unit

        Arguments:
            index: unit index to bookmark
        """
        self.course_nav.go_to_section('TestSection{}'.format(index), 'TestSubsection{}'.format(index))
        self.courseware_page.click_bookmark_unit_button()

    def _bookmark_units(self, num_units):
        """
        Bookmark first `num_units` units by visiting them

        Arguments:
            num_units(int): Number of units to bookmarks
        """
        for index in range(num_units):
            self._bookmark_unit(index)

    def _breadcrumb(self, num_units):
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
                    'TestVertical{}'.format(index)
                ]
            )
        return breadcrumbs

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
        self.assertEqual(self.bookmarks_page.paging_header_text, header_text)
        self.assertEqual(self.bookmarks_page.paging_footer_button_state('previous'), previous_button_enabled)
        self.assertEqual(self.bookmarks_page.paging_footer_button_state('next'), next_button_enabled)
        self.assertEqual(self.bookmarks_page.paging_footer_button_value('current'), current_page_number)
        self.assertEqual(self.bookmarks_page.paging_footer_button_value('total'), total_pages)

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
        self.assertEqual(self.bookmarks_page.results_header_text(), 'MY BOOKMARKS')
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

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.results_header_text(), 'MY BOOKMARKS')
        self.assertEqual(self.bookmarks_page.count(), 2)

        bookmarked_breadcrumbs = self.bookmarks_page.breadcrumbs()

        # Verify bookmarked breadcrumbs and bookmarks order (most recently bookmarked unit should come first)
        breadcrumbs = self._breadcrumb(2)
        breadcrumbs.reverse()
        self.assertEqual(bookmarked_breadcrumbs, breadcrumbs)

        # get usage ids for units
        xblocks = self.course_fixture.get_nested_xblocks(category="vertical")
        xblock_usage_ids = [xblock.locator for xblock in xblocks]
        # Verify link navigation
        for index in range(2):
            self.bookmarks_page.click_bookmarked_block(index)
            self.courseware_page.wait_for_page()
            self.assertTrue(self.courseware_page.active_usage_id() in xblock_usage_ids)
            self.courseware_page.visit().wait_for_page()
            self.bookmarks_page.click_bookmarks_button()

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
        self._test_setup()
        self._bookmark_units(2)
        self._delete_section(0)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.count(), 2)

        self.bookmarks_page.click_bookmarked_block(1)
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

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.count(), 10)

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

    def test_pagination_with_multiple_pages(self):
        """
        Scenario: Bookmarks list pagination is working as expected for multiple pages
        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 12 units available
        Then I click on Bookmarks button
        And I should see a bookmarked list of 10 items
        And I should see paging header and footer with correct data
        And previous page button is disabled in footer
        And next page button is enabled in footer
        Then I click on next page button in footer
        And I should be navigated to second page
        And I should see a bookmarked list with 2 items
        And I should see paging header and footer with correct data
        And next page button is disabled in footer
        And previous page button is enabled in footer
        Then I click on previous page button
        And I should be navigated to first page
        And I should see paging header and footer with correct data
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

        self.bookmarks_page.click_paging_footer_button('next')

        self._verify_pagination_info(
            bookmark_count_on_current_page=2,
            header_text='Showing 11-12 out of 12 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

        self.bookmarks_page.click_paging_footer_button('previous')

        self._verify_pagination_info(
            bookmark_count_on_current_page=10,
            header_text='Showing 1-10 out of 12 total',
            previous_button_enabled=False,
            next_button_enabled=True,
            current_page_number=1,
            total_pages=2
        )

    def test_pagination_with_page_number(self):
        """
        Scenario: Bookmarks list pagination navigation works as expected by page
            number for valid and invalid values
        Given that I am a registered user
        And I visit my courseware page
        And I have bookmarked all the 121 units available
        Then I click on Bookmarks button
        And I should see a bookmarked list
        And I should see total page value is 2
        Then I enter 2 in the page number input
        And I should be navigated to page 2
        Then I enter 3 in the page number input
        And I should stay at page 2
        """
        self._test_setup(num_chapters=11)
        self._bookmark_units(num_units=11)

        self.bookmarks_page.click_bookmarks_button()
        self.assertTrue(self.bookmarks_page.results_present())
        self.assertEqual(self.bookmarks_page.paging_footer_button_value('total'), 2)

        self.bookmarks_page.goto_page_number(2)
        self._verify_pagination_info(
            bookmark_count_on_current_page=1,
            header_text='Showing 11-11 out of 11 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

        self.bookmarks_page.goto_page_number(3, wait_for_page_change=False)
        self._verify_pagination_info(
            bookmark_count_on_current_page=1,
            header_text='Showing 11-11 out of 11 total',
            previous_button_enabled=True,
            next_button_enabled=False,
            current_page_number=2,
            total_pages=2
        )

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
        self._bookmark_unit(0)
        self.bookmarks_page.click_bookmarks_button()
        self.bookmarks_page.click_bookmarked_block(0)
        self.verify_event_data('edx.bookmark.accessed', event_data)
