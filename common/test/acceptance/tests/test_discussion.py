"""
Tests for discussion pages
"""

from .helpers import UniqueCourseTest
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.lms.discussion_single_thread import DiscussionSingleThreadPage
from ..fixtures.course import CourseFixture


class DiscussionSingleThreadTest(UniqueCourseTest):
    """
    Tests for the discussion page displaying a single thread
    """

    def setUp(self):
        super(DiscussionSingleThreadTest, self).setUp()

        # Create a course to register for
        CourseFixture(**self.course_info).install()

        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_no_responses(self):
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "0_responses")
        page.visit()
        self.assertEqual(page.get_response_total_text(), "0 responses")
        self.assertFalse(page.has_add_response_button())
        self.assertEqual(page.get_num_displayed_responses(), 0)
        self.assertEqual(page.get_shown_responses_text(), None)
        self.assertIsNone(page.get_load_responses_button_text())

    def test_few_responses(self):
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "5_responses")
        page.visit()
        self.assertEqual(page.get_response_total_text(), "5 responses")
        self.assertEqual(page.get_num_displayed_responses(), 5)
        self.assertEqual(page.get_shown_responses_text(), "Showing all responses")
        self.assertIsNone(page.get_load_responses_button_text())

    def test_two_response_pages(self):
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "50_responses")
        page.visit()
        self.assertEqual(page.get_response_total_text(), "50 responses")
        self.assertEqual(page.get_num_displayed_responses(), 25)
        self.assertEqual(page.get_shown_responses_text(), "Showing first 25 responses")
        self.assertEqual(page.get_load_responses_button_text(), "Load all responses")

        page.load_more_responses()
        self.assertEqual(page.get_num_displayed_responses(), 50)
        self.assertEqual(page.get_shown_responses_text(), "Showing all responses")
        self.assertEqual(page.get_load_responses_button_text(), None)

    def test_three_response_pages(self):
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "150_responses")
        page.visit()
        self.assertEqual(page.get_response_total_text(), "150 responses")
        self.assertEqual(page.get_num_displayed_responses(), 25)
        self.assertEqual(page.get_shown_responses_text(), "Showing first 25 responses")
        self.assertEqual(page.get_load_responses_button_text(), "Load next 100 responses")

        page.load_more_responses()
        self.assertEqual(page.get_num_displayed_responses(), 125)
        self.assertEqual(page.get_shown_responses_text(), "Showing first 125 responses")
        self.assertEqual(page.get_load_responses_button_text(), "Load all responses")

        page.load_more_responses()
        self.assertEqual(page.get_num_displayed_responses(), 150)
        self.assertEqual(page.get_shown_responses_text(), "Showing all responses")
        self.assertEqual(page.get_load_responses_button_text(), None)

    def test_add_response_button(self):
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "5_responses")
        page.visit()
        self.assertTrue(page.has_add_response_button())
        page.click_add_response_button()

    def test_add_response_button_closed_thread(self):
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "5_responses_closed")
        page.visit()
        self.assertFalse(page.has_add_response_button())
