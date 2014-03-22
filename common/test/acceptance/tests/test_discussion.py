"""
Tests for discussion pages
"""

from .helpers import UniqueCourseTest
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.lms.discussion_single_thread import DiscussionSingleThreadPage
from ..fixtures.course import CourseFixture
from ..fixtures.discussion import SingleThreadViewFixture, Thread, Response, Comment


class DiscussionSingleThreadTest(UniqueCourseTest):
    """
    Tests for the discussion page displaying a single thread
    """

    def setUp(self):
        super(DiscussionSingleThreadTest, self).setUp()

        # Create a course to register for
        CourseFixture(**self.course_info).install()

        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id).visit().get_user_id()

    def setup_thread(self, thread, num_responses):
        view = SingleThreadViewFixture(thread=thread)
        for i in range(num_responses):
            view.addResponse(Response(id=str(i), body=str(i)))
        view.push()

    def test_no_responses(self):
        self.setup_thread(Thread(id="0_responses"), 0)
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "0_responses")
        page.visit()
        self.assertEqual(page.get_response_total_text(), "0 responses")
        self.assertFalse(page.has_add_response_button())
        self.assertEqual(page.get_num_displayed_responses(), 0)
        self.assertEqual(page.get_shown_responses_text(), None)
        self.assertIsNone(page.get_load_responses_button_text())

    def test_few_responses(self):
        self.setup_thread(Thread(id="5_responses"), 5)
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "5_responses")
        page.visit()
        self.assertEqual(page.get_response_total_text(), "5 responses")
        self.assertEqual(page.get_num_displayed_responses(), 5)
        self.assertEqual(page.get_shown_responses_text(), "Showing all responses")
        self.assertIsNone(page.get_load_responses_button_text())

    def test_two_response_pages(self):
        self.setup_thread(Thread(id="50_responses"), 50)
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
        self.setup_thread(Thread(id="150_responses"), 150)
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
        self.setup_thread(Thread(id="5_responses"), 5)
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "5_responses")
        page.visit()
        self.assertTrue(page.has_add_response_button())
        page.click_add_response_button()

    def test_add_response_button_closed_thread(self):
        self.setup_thread(Thread(id="5_responses_closed", closed=True), 5)
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "5_responses_closed")
        page.visit()
        self.assertFalse(page.has_add_response_button())


class DiscussionCommentDeletionTest(UniqueCourseTest):
    """
    Tests for deleting comments displayed beneath responses in the single thread view.
    """

    def setUp(self):
        super(DiscussionCommentDeletionTest, self).setUp()

        # Create a course to register for
        CourseFixture(**self.course_info).install()

    def setup_user(self, roles=[]):
        roles_str = ','.join(roles)
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str).visit().get_user_id()

    def setup_view(self):
        view = SingleThreadViewFixture(Thread(id="comment_deletion_test_thread"))
        view.addResponse(
            Response(id="response1"),
            [Comment(id="comment_other_author", user_id="other"), Comment(id="comment_self_author", user_id=self.user_id)])
        view.push()

    def test_comment_deletion_as_student(self):
        self.setup_user()
        self.setup_view()
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "comment_deletion_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_deletable("comment_self_author"))
        self.assertTrue(page.is_comment_visible("comment_other_author"))
        self.assertFalse(page.is_comment_deletable("comment_other_author"))
        page.delete_comment("comment_self_author")

    def test_comment_deletion_as_moderator(self):
        self.setup_user(roles=['Moderator'])
        self.setup_view()
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "comment_deletion_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_deletable("comment_self_author"))
        self.assertTrue(page.is_comment_deletable("comment_other_author"))
        page.delete_comment("comment_self_author")
        page.delete_comment("comment_other_author")


class DiscussionCommentEditTest(UniqueCourseTest):
    """
    Tests for editing comments displayed beneath responses in the single thread view.
    """

    def setUp(self):
        super(DiscussionCommentEditTest, self).setUp()

        # Create a course to register for
        CourseFixture(**self.course_info).install()

    def setup_user(self, roles=[]):
        roles_str = ','.join(roles)
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str).visit().get_user_id()

    def setup_view(self):
        view = SingleThreadViewFixture(Thread(id="comment_edit_test_thread"))
        view.addResponse(
            Response(id="response1"),
            [Comment(id="comment_other_author", user_id="other"), Comment(id="comment_self_author", user_id=self.user_id)])
        view.push()

    def edit_comment(self, page, comment_id):
        page.start_comment_edit(comment_id)
        new_comment = "edited body"
        page.set_comment_editor_value(comment_id, new_comment)
        page.submit_comment_edit(comment_id, new_comment)

    def test_edit_comment_as_student(self):
        self.setup_user()
        self.setup_view()
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_visible("comment_other_author"))
        self.assertFalse(page.is_comment_editable("comment_other_author"))
        self.edit_comment(page, "comment_self_author")

    def test_edit_comment_as_moderator(self):
        self.setup_user(roles=["Moderator"])
        self.setup_view()
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_editable("comment_other_author"))
        self.edit_comment(page, "comment_self_author")
        self.edit_comment(page, "comment_other_author")

    def test_cancel_comment_edit(self):
        self.setup_user()
        self.setup_view()
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        original_body = page.get_comment_body("comment_self_author")
        page.start_comment_edit("comment_self_author")
        page.set_comment_editor_value("comment_self_author", "edited body")
        page.cancel_comment_edit("comment_self_author", original_body)

    def test_editor_visibility(self):
        """Only one editor should be visible at a time within a single response"""
        self.setup_user(roles=["Moderator"])
        self.setup_view()
        page = DiscussionSingleThreadPage(self.browser, self.course_id, "comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_editable("comment_other_author"))
        self.assertTrue(page.is_add_comment_visible("response1"))
        original_body = page.get_comment_body("comment_self_author")
        page.start_comment_edit("comment_self_author")
        self.assertFalse(page.is_add_comment_visible("response1"))
        self.assertTrue(page.is_comment_editor_visible("comment_self_author"))
        page.set_comment_editor_value("comment_self_author", "edited body")
        page.start_comment_edit("comment_other_author")
        self.assertFalse(page.is_comment_editor_visible("comment_self_author"))
        self.assertTrue(page.is_comment_editor_visible("comment_other_author"))
        self.assertEqual(page.get_comment_body("comment_self_author"), original_body)
        page.start_response_edit("response1")
        self.assertFalse(page.is_comment_editor_visible("comment_other_author"))
        self.assertTrue(page.is_response_editor_visible("response1"))
        original_body = page.get_comment_body("comment_self_author")
        page.start_comment_edit("comment_self_author")
        self.assertFalse(page.is_response_editor_visible("response1"))
        self.assertTrue(page.is_comment_editor_visible("comment_self_author"))
        page.cancel_comment_edit("comment_self_author", original_body)
        self.assertFalse(page.is_comment_editor_visible("comment_self_author"))
        self.assertTrue(page.is_add_comment_visible("response1"))
