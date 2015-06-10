"""
Tests for discussion pages
"""

import datetime
from pytz import UTC
from uuid import uuid4
from nose.plugins.attrib import attr
from flaky import flaky

from .helpers import BaseDiscussionTestCase
from ..helpers import UniqueCourseTest
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.discussion import (
    DiscussionTabSingleThreadPage,
    InlineDiscussionPage,
    InlineDiscussionThreadPage,
    DiscussionUserProfilePage,
    DiscussionTabHomePage,
    DiscussionSortPreferencePage,
)
from ...pages.lms.learner_profile import LearnerProfilePage

from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...fixtures.discussion import (
    SingleThreadViewFixture,
    UserProfileViewFixture,
    SearchResultFixture,
    Thread,
    Response,
    Comment,
    SearchResult,
    MultipleThreadFixture)

from .helpers import BaseDiscussionMixin


THREAD_CONTENT_WITH_LATEX = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               \n\n----------\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur. (b).\n\n
                               **(a)** $H_1(e^{j\\omega}) = \\sum_{n=-\\infty}^{\\infty}h_1[n]e^{-j\\omega n} =
                               \\sum_{n=-\\infty} ^{\\infty}h[n]e^{-j\\omega n}+\\delta_2e^{-j\\omega n_0}$
                               $= H(e^{j\\omega})+\\delta_2e^{-j\\omega n_0}=A_e (e^{j\\omega}) e^{-j\\omega n_0}
                               +\\delta_2e^{-j\\omega n_0}=e^{-j\\omega n_0} (A_e(e^{j\\omega})+\\delta_2)
                               $H_3(e^{j\\omega})=A_e(e^{j\\omega})+\\delta_2$. Dummy $A_e(e^{j\\omega})$ dummy post $.
                               $A_e(e^{j\\omega}) \\ge -\\delta_2$, it follows that $H_3(e^{j\\omega})$ is real and
                               $H_3(e^{j\\omega})\\ge 0$.\n\n**(b)** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.\n\n
                               **Case 1:** If $re^{j\\theta}$ is a Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               \n\n**Case 3:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               Lorem $H_3(e^{j\\omega}) = P(cos\\omega)(cos\\omega - cos\\theta)^k$,
                               Lorem Lorem Lorem Lorem Lorem Lorem $P(cos\\omega)$ has no
                               $(cos\\omega - cos\\theta)$ factor.
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               $P(cos\\theta) \\neq 0$. Since $P(cos\\omega)$ this is a dummy data post $\\omega$,
                               dummy $\\delta > 0$ such that for all $\\omega$ dummy $|\\omega - \\theta|
                               < \\delta$, $P(cos\\omega)$ Lorem ipsum dolor sit amet, consectetur adipiscing elit,
                               sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
                               veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
                               consequat. Duis aute irure dolor in reprehenderit in voluptate velit sse cillum dolore
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
                               ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                               ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
                               reprehenderit in voluptate velit sse cillum dolore eu fugiat nulla pariatur.
                               """


class DiscussionResponsePaginationTestMixin(BaseDiscussionMixin):
    """
    A mixin containing tests for response pagination for use by both inline
    discussion and the discussion tab
    """
    def assert_response_display_correct(self, response_total, displayed_responses):
        """
        Assert that various aspects of the display of responses are all correct:
        * Text indicating total number of responses
        * Presence of "Add a response" button
        * Number of responses actually displayed
        * Presence and text of indicator of how many responses are shown
        * Presence and text of button to load more responses
        """
        self.assertEqual(
            self.thread_page.get_response_total_text(),
            str(response_total) + " responses"
        )
        self.assertEqual(self.thread_page.has_add_response_button(), response_total != 0)
        self.assertEqual(self.thread_page.get_num_displayed_responses(), displayed_responses)
        self.assertEqual(
            self.thread_page.get_shown_responses_text(),
            (
                None if response_total == 0 else
                "Showing all responses" if response_total == displayed_responses else
                "Showing first {} responses".format(displayed_responses)
            )
        )
        self.assertEqual(
            self.thread_page.get_load_responses_button_text(),
            (
                None if response_total == displayed_responses else
                "Load all responses" if response_total - displayed_responses < 100 else
                "Load next 100 responses"
            )
        )

    def test_pagination_no_responses(self):
        self.setup_thread(0)
        self.assert_response_display_correct(0, 0)

    def test_pagination_few_responses(self):
        self.setup_thread(5)
        self.assert_response_display_correct(5, 5)

    def test_pagination_two_response_pages(self):
        self.setup_thread(50)
        self.assert_response_display_correct(50, 25)

        self.thread_page.load_more_responses()
        self.assert_response_display_correct(50, 50)

    def test_pagination_exactly_two_response_pages(self):
        self.setup_thread(125)
        self.assert_response_display_correct(125, 25)

        self.thread_page.load_more_responses()
        self.assert_response_display_correct(125, 125)

    def test_pagination_three_response_pages(self):
        self.setup_thread(150)
        self.assert_response_display_correct(150, 25)

        self.thread_page.load_more_responses()
        self.assert_response_display_correct(150, 125)

        self.thread_page.load_more_responses()
        self.assert_response_display_correct(150, 150)

    def test_add_response_button(self):
        self.setup_thread(5)
        self.assertTrue(self.thread_page.has_add_response_button())
        self.thread_page.click_add_response_button()

    def test_add_response_button_closed_thread(self):
        self.setup_thread(5, closed=True)
        self.assertFalse(self.thread_page.has_add_response_button())


@attr('shard_2')
class DiscussionHomePageTest(UniqueCourseTest):
    """
    Tests for the discussion home page.
    """

    SEARCHED_USERNAME = "gizmo"

    def setUp(self):
        super(DiscussionHomePageTest, self).setUp()
        CourseFixture(**self.course_info).install()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.page = DiscussionTabHomePage(self.browser, self.course_id)
        self.page.visit()

    def test_new_post_button(self):
        """
        Scenario: I can create new posts from the Discussion home page.
            Given that I am on the Discussion home page
            When I click on the 'New Post' button
            Then I should be shown the new post form
        """
        self.assertIsNotNone(self.page.new_post_button)
        self.page.click_new_post_button()
        self.assertIsNotNone(self.page.new_post_form)


@attr('shard_2')
class DiscussionTabSingleThreadTest(BaseDiscussionTestCase, DiscussionResponsePaginationTestMixin):
    """
    Tests for the discussion page displaying a single thread
    """

    def setUp(self):
        super(DiscussionTabSingleThreadTest, self).setUp()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def setup_thread_page(self, thread_id):
        self.thread_page = self.create_single_thread_page(thread_id)  # pylint: disable=attribute-defined-outside-init
        self.thread_page.visit()

    @flaky  # TODO fix this, see TNL-2419
    def test_mathjax_rendering(self):
        thread_id = "test_thread_{}".format(uuid4().hex)

        thread_fixture = SingleThreadViewFixture(
            Thread(
                id=thread_id,
                body=THREAD_CONTENT_WITH_LATEX,
                commentable_id=self.discussion_id,
                thread_type="discussion"
            )
        )
        thread_fixture.push()
        self.setup_thread_page(thread_id)
        self.assertTrue(self.thread_page.is_discussion_body_visible())
        self.assertTrue(self.thread_page.is_mathjax_preview_available())
        self.assertTrue(self.thread_page.is_mathjax_rendered())

    def test_marked_answer_comments(self):
        thread_id = "test_thread_{}".format(uuid4().hex)
        response_id = "test_response_{}".format(uuid4().hex)
        comment_id = "test_comment_{}".format(uuid4().hex)
        thread_fixture = SingleThreadViewFixture(
            Thread(id=thread_id, commentable_id=self.discussion_id, thread_type="question")
        )
        thread_fixture.addResponse(
            Response(id=response_id, endorsed=True),
            [Comment(id=comment_id)]
        )
        thread_fixture.push()
        self.setup_thread_page(thread_id)
        self.assertFalse(self.thread_page.is_comment_visible(comment_id))
        self.assertFalse(self.thread_page.is_add_comment_visible(response_id))
        self.assertTrue(self.thread_page.is_show_comments_visible(response_id))
        self.thread_page.show_comments(response_id)
        self.assertTrue(self.thread_page.is_comment_visible(comment_id))
        self.assertTrue(self.thread_page.is_add_comment_visible(response_id))
        self.assertFalse(self.thread_page.is_show_comments_visible(response_id))


@attr('shard_2')
class DiscussionTabMultipleThreadTest(BaseDiscussionTestCase):
    """
    Tests for the discussion page with multiple threads
    """
    def setUp(self):
        super(DiscussionTabMultipleThreadTest, self).setUp()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.thread_count = 2
        self.thread_ids = []
        self.setup_multiple_threads(thread_count=self.thread_count)

        self.thread_page_1 = DiscussionTabSingleThreadPage(
            self.browser,
            self.course_id,
            self.discussion_id,
            self.thread_ids[0]
        )
        self.thread_page_2 = DiscussionTabSingleThreadPage(
            self.browser,
            self.course_id,
            self.discussion_id,
            self.thread_ids[1]
        )
        self.thread_page_1.visit()

    def setup_multiple_threads(self, thread_count):
        threads = []
        for i in range(thread_count):
            thread_id = "test_thread_{}_{}".format(i, uuid4().hex)
            thread_body = "Dummy Long text body." * 50
            threads.append(
                Thread(id=thread_id, commentable_id=self.discussion_id, body=thread_body),
            )
            self.thread_ids.append(thread_id)
        view = MultipleThreadFixture(threads)
        view.push()

    def test_page_scroll_on_thread_change_view(self):
        """
        Check switching between threads changes the page to scroll to bottom
        """
        # verify threads are rendered on the page
        self.assertTrue(
            self.thread_page_1.check_threads_rendered_successfully(thread_count=self.thread_count)
        )

        # From the thread_page_1 open & verify next thread
        self.thread_page_1.click_and_open_thread(thread_id=self.thread_ids[1])
        self.assertTrue(self.thread_page_2.is_browser_on_page())

        # Verify that window is on top of page.
        self.thread_page_2.check_window_is_on_top()


@attr('shard_2')
class DiscussionOpenClosedThreadTest(BaseDiscussionTestCase):
    """
    Tests for checking the display of attributes on open and closed threads
    """

    def setUp(self):
        super(DiscussionOpenClosedThreadTest, self).setUp()

        self.thread_id = "test_thread_{}".format(uuid4().hex)

    def setup_user(self, roles=[]):
        roles_str = ','.join(roles)
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str).visit().get_user_id()

    def setup_view(self, **thread_kwargs):
        thread_kwargs.update({'commentable_id': self.discussion_id})
        view = SingleThreadViewFixture(
            Thread(id=self.thread_id, **thread_kwargs)
        )
        view.addResponse(Response(id="response1"))
        view.push()

    def setup_openclosed_thread_page(self, closed=False):
        self.setup_user(roles=['Moderator'])
        if closed:
            self.setup_view(closed=True)
        else:
            self.setup_view()
        page = self.create_single_thread_page(self.thread_id)
        page.visit()
        page.close_open_thread()
        return page

    def test_originally_open_thread_vote_display(self):
        page = self.setup_openclosed_thread_page()
        self.assertFalse(page._is_element_visible('.forum-thread-main-wrapper .action-vote'))
        self.assertTrue(page._is_element_visible('.forum-thread-main-wrapper .display-vote'))
        self.assertFalse(page._is_element_visible('.response_response1 .action-vote'))
        self.assertTrue(page._is_element_visible('.response_response1 .display-vote'))

    def test_originally_closed_thread_vote_display(self):
        page = self.setup_openclosed_thread_page(True)
        self.assertTrue(page._is_element_visible('.forum-thread-main-wrapper .action-vote'))
        self.assertFalse(page._is_element_visible('.forum-thread-main-wrapper .display-vote'))
        self.assertTrue(page._is_element_visible('.response_response1 .action-vote'))
        self.assertFalse(page._is_element_visible('.response_response1 .display-vote'))


@attr('shard_2')
class DiscussionCommentDeletionTest(BaseDiscussionTestCase):
    """
    Tests for deleting comments displayed beneath responses in the single thread view.
    """
    def setup_user(self, roles=[]):
        roles_str = ','.join(roles)
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str).visit().get_user_id()

    def setup_view(self):
        view = SingleThreadViewFixture(Thread(id="comment_deletion_test_thread", commentable_id=self.discussion_id))
        view.addResponse(
            Response(id="response1"),
            [Comment(id="comment_other_author", user_id="other"), Comment(id="comment_self_author", user_id=self.user_id)])
        view.push()

    def test_comment_deletion_as_student(self):
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("comment_deletion_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_deletable("comment_self_author"))
        self.assertTrue(page.is_comment_visible("comment_other_author"))
        self.assertFalse(page.is_comment_deletable("comment_other_author"))
        page.delete_comment("comment_self_author")

    def test_comment_deletion_as_moderator(self):
        self.setup_user(roles=['Moderator'])
        self.setup_view()
        page = self.create_single_thread_page("comment_deletion_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_deletable("comment_self_author"))
        self.assertTrue(page.is_comment_deletable("comment_other_author"))
        page.delete_comment("comment_self_author")
        page.delete_comment("comment_other_author")


@attr('shard_2')
class DiscussionResponseEditTest(BaseDiscussionTestCase):
    """
    Tests for editing responses displayed beneath thread in the single thread view.
    """
    def setup_user(self, roles=[]):
        roles_str = ','.join(roles)
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str).visit().get_user_id()

    def setup_view(self):
        view = SingleThreadViewFixture(Thread(id="response_edit_test_thread", commentable_id=self.discussion_id))
        view.addResponse(
            Response(id="response_other_author", user_id="other", thread_id="response_edit_test_thread"),
        )
        view.addResponse(
            Response(id="response_self_author", user_id=self.user_id, thread_id="response_edit_test_thread"),
        )
        view.push()

    def edit_response(self, page, response_id):
        self.assertTrue(page.is_response_editable(response_id))
        page.start_response_edit(response_id)
        new_response = "edited body"
        page.set_response_editor_value(response_id, new_response)
        page.submit_response_edit(response_id, new_response)

    def test_edit_response_as_student(self):
        """
        Scenario: Students should be able to edit the response they created not responses of other users
            Given that I am on discussion page with student logged in
            When I try to edit the response created by student
            Then the response should be edited and rendered successfully
            And responses from other users should be shown over there
            And the student should be able to edit the response of other people
        """
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_response_visible("response_other_author"))
        self.assertFalse(page.is_response_editable("response_other_author"))
        self.edit_response(page, "response_self_author")

    def test_edit_response_as_moderator(self):
        """
        Scenario: Moderator should be able to edit the response they created and responses of other users
            Given that I am on discussion page with moderator logged in
            When I try to edit the response created by moderator
            Then the response should be edited and rendered successfully
            And I try to edit the response created by other users
            Then the response should be edited and rendered successfully
        """
        self.setup_user(roles=["Moderator"])
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()
        self.edit_response(page, "response_self_author")
        self.edit_response(page, "response_other_author")

    def test_vote_report_endorse_after_edit(self):
        """
        Scenario: Moderator should be able to vote, report or endorse after editing the response.
            Given that I am on discussion page with moderator logged in
            When I try to edit the response created by moderator
            Then the response should be edited and rendered successfully
            And I try to edit the response created by other users
            Then the response should be edited and rendered successfully
            And I try to vote the response created by moderator
            Then the response should be voted successfully
            And I try to vote the response created by other users
            Then the response should be voted successfully
            And I try to report the response created by moderator
            Then the response should be reported successfully
            And I try to report the response created by other users
            Then the response should be reported successfully
            And I try to endorse the response created by moderator
            Then the response should be endorsed successfully
            And I try to endorse the response created by other users
            Then the response should be endorsed successfully
        """
        self.setup_user(roles=["Moderator"])
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()
        self.edit_response(page, "response_self_author")
        self.edit_response(page, "response_other_author")
        page.vote_response('response_self_author')
        page.vote_response('response_other_author')
        page.report_response('response_self_author')
        page.report_response('response_other_author')
        page.endorse_response('response_self_author')
        page.endorse_response('response_other_author')


@attr('shard_2')
class DiscussionCommentEditTest(BaseDiscussionTestCase):
    """
    Tests for editing comments displayed beneath responses in the single thread view.
    """
    def setup_user(self, roles=[]):
        roles_str = ','.join(roles)
        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str).visit().get_user_id()

    def setup_view(self):
        view = SingleThreadViewFixture(Thread(id="comment_edit_test_thread", commentable_id=self.discussion_id))
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
        page = self.create_single_thread_page("comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_visible("comment_other_author"))
        self.assertFalse(page.is_comment_editable("comment_other_author"))
        self.edit_comment(page, "comment_self_author")

    def test_edit_comment_as_moderator(self):
        self.setup_user(roles=["Moderator"])
        self.setup_view()
        page = self.create_single_thread_page("comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_editable("comment_other_author"))
        self.edit_comment(page, "comment_self_author")
        self.edit_comment(page, "comment_other_author")

    def test_cancel_comment_edit(self):
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("comment_edit_test_thread")
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
        page = self.create_single_thread_page("comment_edit_test_thread")
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


@attr('shard_2')
class InlineDiscussionTest(UniqueCourseTest, DiscussionResponsePaginationTestMixin):
    """
    Tests for inline discussions
    """

    def setUp(self):
        super(InlineDiscussionTest, self).setUp()
        self.thread_ids = []
        self.discussion_id = "test_discussion_{}".format(uuid4().hex)
        self.additional_discussion_id = "test_discussion_{}".format(uuid4().hex)
        self.course_fix = CourseFixture(**self.course_info).add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                            metadata={"discussion_id": self.discussion_id}
                        ),
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion 1",
                            metadata={"discussion_id": self.additional_discussion_id}
                        )
                    )
                )
            )
        ).install()

        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id).visit().get_user_id()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.courseware_page.visit()
        self.discussion_page = InlineDiscussionPage(self.browser, self.discussion_id)
        self.additional_discussion_page = InlineDiscussionPage(self.browser, self.additional_discussion_id)

    def setup_thread_page(self, thread_id):
        self.discussion_page.expand_discussion()
        self.assertEqual(self.discussion_page.get_num_displayed_threads(), 1)
        self.thread_page = InlineDiscussionThreadPage(self.browser, thread_id)  # pylint: disable=attribute-defined-outside-init
        self.thread_page.expand()

    def setup_multiple_inline_threads(self, thread_count):
        """
        Set up multiple treads on the page by passing 'thread_count'
        """
        threads = []
        for i in range(thread_count):
            thread_id = "test_thread_{}_{}".format(i, uuid4().hex)
            threads.append(
                Thread(id=thread_id, commentable_id=self.discussion_id),
            )
            self.thread_ids.append(thread_id)
        thread_fixture = MultipleThreadFixture(threads)
        thread_fixture.add_response(
            Response(id="response1"),
            [Comment(id="comment1", user_id="other"), Comment(id="comment2", user_id=self.user_id)],
            threads[0]
        )
        thread_fixture.push()

    def test_page_while_expanding_inline_discussion(self):
        """
        Tests for the Inline Discussion page with multiple treads. Page should not focus 'thread-wrapper'
        after loading responses.
        """
        self.setup_multiple_inline_threads(thread_count=3)
        self.discussion_page.expand_discussion()
        thread_page = InlineDiscussionThreadPage(self.browser, self.thread_ids[0])
        thread_page.expand()

        # Check if 'thread-wrapper' is focused after expanding thread
        self.assertFalse(thread_page.check_if_selector_is_focused(selector='.thread-wrapper'))

    def test_initial_render(self):
        self.assertFalse(self.discussion_page.is_discussion_expanded())

    def test_expand_discussion_empty(self):
        self.discussion_page.expand_discussion()
        self.assertEqual(self.discussion_page.get_num_displayed_threads(), 0)

    def check_anonymous_to_peers(self, is_staff):
        thread = Thread(id=uuid4().hex, anonymous_to_peers=True, commentable_id=self.discussion_id)
        thread_fixture = SingleThreadViewFixture(thread)
        thread_fixture.push()
        self.setup_thread_page(thread.get("id"))
        self.assertEqual(self.thread_page.is_thread_anonymous(), not is_staff)

    def test_anonymous_to_peers_threads_as_staff(self):
        AutoAuthPage(self.browser, course_id=self.course_id, roles="Administrator").visit()
        self.courseware_page.visit()
        self.check_anonymous_to_peers(True)

    def test_anonymous_to_peers_threads_as_peer(self):
        self.check_anonymous_to_peers(False)

    def test_discussion_blackout_period(self):
        now = datetime.datetime.now(UTC)
        self.course_fix.add_advanced_settings(
            {
                u"discussion_blackouts": {
                    "value": [
                        [
                            (now - datetime.timedelta(days=14)).isoformat(),
                            (now + datetime.timedelta(days=2)).isoformat()
                        ]
                    ]
                }
            }
        )
        self.course_fix._add_advanced_settings()
        self.browser.refresh()
        thread = Thread(id=uuid4().hex, commentable_id=self.discussion_id)
        thread_fixture = SingleThreadViewFixture(thread)
        thread_fixture.addResponse(
            Response(id="response1"),
            [Comment(id="comment1", user_id="other"), Comment(id="comment2", user_id=self.user_id)])
        thread_fixture.push()
        self.setup_thread_page(thread.get("id"))
        self.assertFalse(self.discussion_page.element_exists(".new-post-btn"))
        self.assertFalse(self.thread_page.has_add_response_button())
        self.assertFalse(self.thread_page.is_response_editable("response1"))
        self.assertFalse(self.thread_page.is_add_comment_visible("response1"))
        self.assertFalse(self.thread_page.is_comment_editable("comment1"))
        self.assertFalse(self.thread_page.is_comment_editable("comment2"))
        self.assertFalse(self.thread_page.is_comment_deletable("comment1"))
        self.assertFalse(self.thread_page.is_comment_deletable("comment2"))

    def test_dual_discussion_module(self):
        """
        Scenario: Two discussion module in one unit shouldn't override their actions
        Given that I'm on courseware page where there are two inline discussion
        When I click on one discussion module new post button
        Then it should add new post form of that module in DOM
        And I should be shown new post form of that module
        And I shouldn't be shown second discussion module new post form
        And I click on second discussion module new post button
        Then it should add new post form of second module in DOM
        And I should be shown second discussion new post form
        And I shouldn't be shown first discussion module new post form
        And I have two new post form in the DOM
        When I click back on first module new post button
        And I should be shown new post form of that module
        And I shouldn't be shown second discussion module new post form
        """
        self.discussion_page.wait_for_page()
        self.additional_discussion_page.wait_for_page()
        self.discussion_page.click_new_post_button()
        with self.discussion_page.handle_alert():
            self.discussion_page.click_cancel_new_post()
        self.additional_discussion_page.click_new_post_button()
        self.assertFalse(self.discussion_page._is_element_visible(".new-post-article"))
        with self.additional_discussion_page.handle_alert():
            self.additional_discussion_page.click_cancel_new_post()
        self.discussion_page.click_new_post_button()
        self.assertFalse(self.additional_discussion_page._is_element_visible(".new-post-article"))


@attr('shard_2')
class DiscussionUserProfileTest(UniqueCourseTest):
    """
    Tests for user profile page in discussion tab.
    """

    PAGE_SIZE = 20  # django_comment_client.forum.views.THREADS_PER_PAGE
    PROFILED_USERNAME = "profiled-user"

    def setUp(self):
        super(DiscussionUserProfileTest, self).setUp()
        CourseFixture(**self.course_info).install()
        # The following line creates a user enrolled in our course, whose
        # threads will be viewed, but not the one who will view the page.
        # It isn't necessary to log them in, but using the AutoAuthPage
        # saves a lot of code.
        self.profiled_user_id = AutoAuthPage(
            self.browser,
            username=self.PROFILED_USERNAME,
            course_id=self.course_id
        ).visit().get_user_id()
        # now create a second user who will view the profile.
        self.user_id = AutoAuthPage(
            self.browser,
            course_id=self.course_id
        ).visit().get_user_id()

    def check_pages(self, num_threads):
        # set up the stub server to return the desired amount of thread results
        threads = [Thread(id=uuid4().hex) for _ in range(num_threads)]
        UserProfileViewFixture(threads).push()
        # navigate to default view (page 1)
        page = DiscussionUserProfilePage(
            self.browser,
            self.course_id,
            self.profiled_user_id,
            self.PROFILED_USERNAME
        )
        page.visit()

        current_page = 1
        total_pages = max(num_threads - 1, 1) / self.PAGE_SIZE + 1
        all_pages = range(1, total_pages + 1)
        return page

        def _check_page():
            # ensure the page being displayed as "current" is the expected one
            self.assertEqual(page.get_current_page(), current_page)
            # ensure the expected threads are being shown in the right order
            threads_expected = threads[(current_page - 1) * self.PAGE_SIZE:current_page * self.PAGE_SIZE]
            self.assertEqual(page.get_shown_thread_ids(), [t["id"] for t in threads_expected])
            # ensure the clickable page numbers are the expected ones
            self.assertEqual(page.get_clickable_pages(), [
                p for p in all_pages
                if p != current_page
                and p - 2 <= current_page <= p + 2
                or (current_page > 2 and p == 1)
                or (current_page < total_pages and p == total_pages)
            ])
            # ensure the previous button is shown, but only if it should be.
            # when it is shown, make sure it works.
            if current_page > 1:
                self.assertTrue(page.is_prev_button_shown(current_page - 1))
                page.click_prev_page()
                self.assertEqual(page.get_current_page(), current_page - 1)
                page.click_next_page()
                self.assertEqual(page.get_current_page(), current_page)
            else:
                self.assertFalse(page.is_prev_button_shown())
            # ensure the next button is shown, but only if it should be.
            if current_page < total_pages:
                self.assertTrue(page.is_next_button_shown(current_page + 1))
            else:
                self.assertFalse(page.is_next_button_shown())

        # click all the way up through each page
        for i in range(current_page, total_pages):
            _check_page()
            if current_page < total_pages:
                page.click_on_page(current_page + 1)
                current_page += 1

        # click all the way back down
        for i in range(current_page, 0, -1):
            _check_page()
            if current_page > 1:
                page.click_on_page(current_page - 1)
                current_page -= 1

    def test_0_threads(self):
        self.check_pages(0)

    def test_1_thread(self):
        self.check_pages(1)

    def test_20_threads(self):
        self.check_pages(20)

    def test_21_threads(self):
        self.check_pages(21)

    def test_151_threads(self):
        self.check_pages(151)

    def test_pagination_window_reposition(self):
        page = self.check_pages(50)
        page.click_next_page()
        page.wait_for_ajax()
        self.assertTrue(page.is_window_on_top())

    def test_redirects_to_learner_profile(self):
        """
        Scenario: Verify that learner-profile link is present on forum discussions page and we can navigate to it.

        Given that I am on discussion forum user's profile page.
        And I can see a username on left sidebar
        When I click on my username.
        Then I will be navigated to Learner Profile page.
        And I can my username on Learner Profile page
        """
        learner_profile_page = LearnerProfilePage(self.browser, self.PROFILED_USERNAME)

        page = self.check_pages(1)
        page.click_on_sidebar_username()

        learner_profile_page.wait_for_page()
        self.assertTrue(learner_profile_page.field_is_visible('username'))


@attr('shard_2')
class DiscussionSearchAlertTest(UniqueCourseTest):
    """
    Tests for spawning and dismissing alerts related to user search actions and their results.
    """

    SEARCHED_USERNAME = "gizmo"

    def setUp(self):
        super(DiscussionSearchAlertTest, self).setUp()
        CourseFixture(**self.course_info).install()
        # first auto auth call sets up a user that we will search for in some tests
        self.searched_user_id = AutoAuthPage(
            self.browser,
            username=self.SEARCHED_USERNAME,
            course_id=self.course_id
        ).visit().get_user_id()
        # this auto auth call creates the actual session user
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.page = DiscussionTabHomePage(self.browser, self.course_id)
        self.page.visit()

    def setup_corrected_text(self, text):
        SearchResultFixture(SearchResult(corrected_text=text)).push()

    def check_search_alert_messages(self, expected):
        actual = self.page.get_search_alert_messages()
        self.assertTrue(all(map(lambda msg, sub: msg.lower().find(sub.lower()) >= 0, actual, expected)))

    def test_no_rewrite(self):
        self.setup_corrected_text(None)
        self.page.perform_search()
        self.check_search_alert_messages(["no threads"])

    def test_rewrite_dismiss(self):
        self.setup_corrected_text("foo")
        self.page.perform_search()
        self.check_search_alert_messages(["foo"])
        self.page.dismiss_alert_message("foo")
        self.check_search_alert_messages([])

    def test_new_search(self):
        self.setup_corrected_text("foo")
        self.page.perform_search()
        self.check_search_alert_messages(["foo"])

        self.setup_corrected_text("bar")
        self.page.perform_search()
        self.check_search_alert_messages(["bar"])

        self.setup_corrected_text(None)
        self.page.perform_search()
        self.check_search_alert_messages(["no threads"])

    def test_rewrite_and_user(self):
        self.setup_corrected_text("foo")
        self.page.perform_search(self.SEARCHED_USERNAME)
        self.check_search_alert_messages(["foo", self.SEARCHED_USERNAME])

    def test_user_only(self):
        self.setup_corrected_text(None)
        self.page.perform_search(self.SEARCHED_USERNAME)
        self.check_search_alert_messages(["no threads", self.SEARCHED_USERNAME])
        # make sure clicking the link leads to the user profile page
        UserProfileViewFixture([]).push()
        self.page.get_search_alert_links().first.click()
        DiscussionUserProfilePage(
            self.browser,
            self.course_id,
            self.searched_user_id,
            self.SEARCHED_USERNAME
        ).wait_for_page()


@attr('shard_2')
class DiscussionSortPreferenceTest(UniqueCourseTest):
    """
    Tests for the discussion page displaying a single thread.
    """

    def setUp(self):
        super(DiscussionSortPreferenceTest, self).setUp()

        # Create a course to register for.
        CourseFixture(**self.course_info).install()

        AutoAuthPage(self.browser, course_id=self.course_id).visit()

        self.sort_page = DiscussionSortPreferencePage(self.browser, self.course_id)
        self.sort_page.visit()

    def test_default_sort_preference(self):
        """
        Test to check the default sorting preference of user. (Default = date )
        """
        selected_sort = self.sort_page.get_selected_sort_preference()
        self.assertEqual(selected_sort, "date")

    def test_change_sort_preference(self):
        """
        Test that if user sorting preference is changing properly.
        """
        selected_sort = ""
        for sort_type in ["votes", "comments", "date"]:
            self.assertNotEqual(selected_sort, sort_type)
            self.sort_page.change_sort_preference(sort_type)
            selected_sort = self.sort_page.get_selected_sort_preference()
            self.assertEqual(selected_sort, sort_type)

    def test_last_preference_saved(self):
        """
        Test that user last preference is saved.
        """
        selected_sort = ""
        for sort_type in ["votes", "comments", "date"]:
            self.assertNotEqual(selected_sort, sort_type)
            self.sort_page.change_sort_preference(sort_type)
            selected_sort = self.sort_page.get_selected_sort_preference()
            self.assertEqual(selected_sort, sort_type)
            self.sort_page.refresh_page()
            selected_sort = self.sort_page.get_selected_sort_preference()
            self.assertEqual(selected_sort, sort_type)
