"""
Tests for discussion pages
"""

import datetime
from uuid import uuid4

from nose.plugins.attrib import attr
from pytz import UTC
from flaky import flaky

from common.test.acceptance.tests.discussion.helpers import BaseDiscussionTestCase
from common.test.acceptance.tests.helpers import UniqueCourseTest
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.discussion import (
    DiscussionTabSingleThreadPage,
    InlineDiscussionPage,
    InlineDiscussionThreadPage,
    DiscussionUserProfilePage,
    DiscussionTabHomePage,
    DiscussionSortPreferencePage,
)
from common.test.acceptance.pages.lms.learner_profile import LearnerProfilePage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.fixtures.discussion import (
    SingleThreadViewFixture,
    UserProfileViewFixture,
    SearchResultFixture,
    Thread,
    Response,
    Comment,
    SearchResult,
    MultipleThreadFixture,
)

from common.test.acceptance.tests.discussion.helpers import BaseDiscussionMixin
from common.test.acceptance.tests.helpers import skip_if_browser


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


@attr(shard=2)
class DiscussionHomePageTest(BaseDiscussionTestCase):
    """
    Tests for the discussion home page.
    """

    SEARCHED_USERNAME = "gizmo"

    def setUp(self):
        super(DiscussionHomePageTest, self).setUp()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.page = DiscussionTabHomePage(self.browser, self.course_id)
        self.page.visit()

    @attr(shard=2)
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

    def test_receive_update_checkbox(self):
        """
        Scenario: I can save the receive update email notification checkbox
                on Discussion home page.
            Given that I am on the Discussion home page
            When I click on the 'Receive update' checkbox
            Then it should always shown selected.
        """
        receive_updates_selector = '.email-setting'
        receive_updates_checkbox = self.page.is_element_visible(receive_updates_selector)
        self.assertTrue(receive_updates_checkbox)

        self.assertFalse(self.page.is_checkbox_selected(receive_updates_selector))
        self.page.click_element(receive_updates_selector)

        self.assertTrue(self.page.is_checkbox_selected(receive_updates_selector))
        self.page.refresh_and_wait_for_load()
        self.assertTrue(self.page.is_checkbox_selected(receive_updates_selector))

    @attr('a11y')
    def test_page_accessibility(self):
        self.page.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
            ]
        })
        self.page.a11y_audit.check_for_accessibility_errors()


@attr(shard=2)
class DiscussionNavigationTest(BaseDiscussionTestCase):
    """
    Tests for breadcrumbs navigation in the Discussions page nav bar
    """

    def setUp(self):
        super(DiscussionNavigationTest, self).setUp()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

        thread_id = "test_thread_{}".format(uuid4().hex)
        thread_fixture = SingleThreadViewFixture(
            Thread(
                id=thread_id,
                body=THREAD_CONTENT_WITH_LATEX,
                commentable_id=self.discussion_id
            )
        )
        thread_fixture.push()
        self.thread_page = DiscussionTabSingleThreadPage(
            self.browser,
            self.course_id,
            self.discussion_id,
            thread_id
        )
        self.thread_page.visit()

    def test_breadcrumbs_push_topic(self):
        topic_button = self.thread_page.q(
            css=".forum-nav-browse-menu-item[data-discussion-id='{}']".format(self.discussion_id)
        )
        self.assertTrue(topic_button.visible)
        topic_button.click()

        # Verify the thread's topic has been pushed to breadcrumbs
        breadcrumbs = self.thread_page.q(css=".breadcrumbs .nav-item")
        self.assertEqual(len(breadcrumbs), 2)
        self.assertEqual(breadcrumbs[1].text, "Test Discussion Topic")

    def test_breadcrumbs_back_to_all_topics(self):
        topic_button = self.thread_page.q(
            css=".forum-nav-browse-menu-item[data-discussion-id='{}']".format(self.discussion_id)
        )
        self.assertTrue(topic_button.visible)
        topic_button.click()

        # Verify clicking the first breadcrumb takes you back to all topics
        self.thread_page.q(css=".breadcrumbs .nav-item")[0].click()
        self.assertEqual(len(self.thread_page.q(css=".breadcrumbs .nav-item")), 1)

    def test_breadcrumbs_clear_search(self):
        self.thread_page.q(css=".search-input").fill("search text")
        self.thread_page.q(css=".search-btn").click()

        # Verify that clicking the first breadcrumb clears your search
        self.thread_page.q(css=".breadcrumbs .nav-item")[0].click()
        self.assertEqual(self.thread_page.q(css=".search-input").text[0], "")


@attr(shard=2)
class DiscussionTabSingleThreadTest(BaseDiscussionTestCase, DiscussionResponsePaginationTestMixin):
    """
    Tests for the discussion page displaying a single thread
    """

    def setUp(self):
        super(DiscussionTabSingleThreadTest, self).setUp()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.tab_nav = TabNavPage(self.browser)

    def setup_thread_page(self, thread_id):
        self.thread_page = self.create_single_thread_page(thread_id)  # pylint: disable=attribute-defined-outside-init
        self.thread_page.visit()

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
        self.thread_page.verify_mathjax_preview_available()
        self.thread_page.verify_mathjax_rendered()

    def test_markdown_reference_link(self):
        """
        Check markdown editor renders reference link correctly
        and colon(:) in reference link is not converted to %3a
        """
        sample_link = "http://example.com/colon:test"
        thread_content = """[enter link description here][1]\n[1]: http://example.com/colon:test"""
        thread_id = "test_thread_{}".format(uuid4().hex)
        thread_fixture = SingleThreadViewFixture(
            Thread(
                id=thread_id,
                body=thread_content,
                commentable_id=self.discussion_id,
                thread_type="discussion"
            )
        )
        thread_fixture.push()
        self.setup_thread_page(thread_id)
        self.assertEqual(self.thread_page.get_link_href(), sample_link)

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

    def test_discussion_blackout_period(self):
        """
        Verify that new discussion can not be started during course blackout period.

        Blackout period is the period between which students cannot post new or contribute
        to existing discussions.
        """
        now = datetime.datetime.now(UTC)
        # Update course advance settings with a valid blackout period.
        self.course_fixture.add_advanced_settings(
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
        self.course_fixture._add_advanced_settings()  # pylint: disable=protected-access
        self.browser.refresh()
        thread = Thread(id=uuid4().hex, commentable_id=self.discussion_id)
        thread_fixture = SingleThreadViewFixture(thread)
        thread_fixture.addResponse(
            Response(id="response1"),
            [Comment(id="comment1")])
        thread_fixture.push()
        self.setup_thread_page(thread.get("id"))  # pylint: disable=no-member

        # Verify that `Add a Post` is not visible on course tab nav.
        self.assertFalse(self.tab_nav.has_new_post_button_visible_on_tab())

        # Verify that `Add a response` button is not visible.
        self.assertFalse(self.thread_page.has_add_response_button())

        # Verify user can not add new responses or modify existing responses.
        self.assertFalse(self.thread_page.has_discussion_reply_editor())
        self.assertFalse(self.thread_page.is_response_editable("response1"))
        self.assertFalse(self.thread_page.is_response_deletable("response1"))

        # Verify that user can not add new comment to a response or modify existing responses.
        self.assertFalse(self.thread_page.is_add_comment_visible("response1"))
        self.assertFalse(self.thread_page.is_comment_editable("comment1"))
        self.assertFalse(self.thread_page.is_comment_deletable("comment1"))


class DiscussionTabMultipleThreadTest(BaseDiscussionTestCase, BaseDiscussionMixin):
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

    @attr('a11y')
    def test_page_accessibility(self):
        self.thread_page_1.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
            ]
        })

        self.thread_page_1.a11y_audit.check_for_accessibility_errors()

        self.thread_page_2.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
            ]
        })

        self.thread_page_2.a11y_audit.check_for_accessibility_errors()


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

    @attr(shard=2)
    def test_originally_open_thread_vote_display(self):
        page = self.setup_openclosed_thread_page()
        self.assertFalse(page.is_element_visible('.thread-main-wrapper .action-vote'))
        self.assertTrue(page.is_element_visible('.thread-main-wrapper .display-vote'))
        self.assertFalse(page.is_element_visible('.response_response1 .action-vote'))
        self.assertTrue(page.is_element_visible('.response_response1 .display-vote'))

    @attr(shard=2)
    def test_originally_closed_thread_vote_display(self):
        page = self.setup_openclosed_thread_page(True)
        self.assertTrue(page.is_element_visible('.thread-main-wrapper .action-vote'))
        self.assertFalse(page.is_element_visible('.thread-main-wrapper .display-vote'))
        self.assertTrue(page.is_element_visible('.response_response1 .action-vote'))
        self.assertFalse(page.is_element_visible('.response_response1 .display-vote'))

    @attr('a11y')
    def test_page_accessibility(self):
        page = self.setup_openclosed_thread_page()
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'color-contrast',  # Commented out for now because they reproducibly fail on Jenkins but not locally
            ]
        })
        page.a11y_audit.check_for_accessibility_errors()

        page = self.setup_openclosed_thread_page(True)
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'color-contrast',  # Commented out for now because they reproducibly fail on Jenkins but not locally
            ]
        })
        page.a11y_audit.check_for_accessibility_errors()


@attr(shard=2)
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
            Response(id="response1"), [
                Comment(id="comment_other_author"),
                Comment(id="comment_self_author", user_id=self.user_id, thread_id="comment_deletion_test_thread")
            ]
        )
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

    @attr(shard=2)
    def test_edit_response_add_link(self):
        """
        Scenario: User submits valid input to the 'add link' form
            Given I am editing a response on a discussion page
            When I click the 'add link' icon in the editor toolbar
            And enter a valid url to the URL input field
            And enter a valid string in the Description input field
            And click the 'OK' button
            Then the edited response should contain the new link
        """
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()

        response_id = "response_self_author"
        url = "http://example.com"
        description = "example"

        page.start_response_edit(response_id)
        page.set_response_editor_value(response_id, "")
        page.add_content_via_editor_button(
            "link", response_id, url, description)
        page.submit_response_edit(response_id, description)

        expected_response_html = (
            '<p><a href="{}">{}</a></p>'.format(url, description)
        )
        actual_response_html = page.q(
            css=".response_{} .response-body".format(response_id)
        ).html[0]
        self.assertEqual(expected_response_html, actual_response_html)

    @attr(shard=2)
    def test_edit_response_add_image(self):
        """
        Scenario: User submits valid input to the 'add image' form
            Given I am editing a response on a discussion page
            When I click the 'add image' icon in the editor toolbar
            And enter a valid url to the URL input field
            And enter a valid string in the Description input field
            And click the 'OK' button
            Then the edited response should contain the new image
        """
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()

        response_id = "response_self_author"
        url = "http://www.example.com/something.png"
        description = "image from example.com"

        page.start_response_edit(response_id)
        page.set_response_editor_value(response_id, "")
        page.add_content_via_editor_button(
            "image", response_id, url, description)
        page.submit_response_edit(response_id, '')

        expected_response_html = (
            '<p><img src="{}" alt="{}" title=""></p>'.format(url, description)
        )
        actual_response_html = page.q(
            css=".response_{} .response-body".format(response_id)
        ).html[0]
        self.assertEqual(expected_response_html, actual_response_html)

    @attr(shard=2)
    def test_edit_response_add_image_error_msg(self):
        """
        Scenario: User submits invalid input to the 'add image' form
            Given I am editing a response on a discussion page
            When I click the 'add image' icon in the editor toolbar
            And enter an invalid url to the URL input field
            And enter an empty string in the Description input field
            And click the 'OK' button
            Then I should be shown 2 error messages
        """
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()
        page.start_response_edit("response_self_author")
        page.add_content_via_editor_button(
            "image", "response_self_author", '', '')
        page.verify_link_editor_error_messages_shown()

    @attr(shard=2)
    def test_edit_response_add_decorative_image(self):
        """
        Scenario: User submits invalid input to the 'add image' form
            Given I am editing a response on a discussion page
            When I click the 'add image' icon in the editor toolbar
            And enter a valid url to the URL input field
            And enter an empty string in the Description input field
            And I check the 'image is decorative' checkbox
            And click the 'OK' button
            Then the edited response should contain the new image
        """
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()

        response_id = "response_self_author"
        url = "http://www.example.com/something.png"
        description = ""

        page.start_response_edit(response_id)
        page.set_response_editor_value(response_id, "Some content")
        page.add_content_via_editor_button(
            "image", response_id, url, description, is_decorative=True)
        page.submit_response_edit(response_id, "Some content")

        expected_response_html = (
            '<p>Some content<img src="{}" alt="{}" title=""></p>'.format(
                url, description)
        )
        actual_response_html = page.q(
            css=".response_{} .response-body".format(response_id)
        ).html[0]
        self.assertEqual(expected_response_html, actual_response_html)

    @attr(shard=2)
    def test_edit_response_add_link_error_msg(self):
        """
        Scenario: User submits invalid input to the 'add link' form
            Given I am editing a response on a discussion page
            When I click the 'add link' icon in the editor toolbar
            And enter an invalid url to the URL input field
            And enter an empty string in the Description input field
            And click the 'OK' button
            Then I should be shown 2 error messages
        """
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.visit()
        page.start_response_edit("response_self_author")
        page.add_content_via_editor_button(
            "link", "response_self_author", '', '')
        page.verify_link_editor_error_messages_shown()

    @attr(shard=2)
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

    @attr(shard=2)
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

    @attr(shard=2)
    @flaky  # TODO fix this, see TNL-5453
    def test_vote_report_endorse_after_edit(self):
        """
        Scenario: Moderator should be able to vote, report or endorse after editing the response.
            Given that I am on discussion page with moderator logged in
            When I try to edit the response created by moderator
            Then the response should be edited and rendered successfully
            And I try to edit the response created by other users
            Then the response should be edited and rendered successfully
            And I try to vote the response created by moderator
            Then the response should not be able to be voted
            And I try to vote the response created by other users
            Then the response should be voted successfully
            And I try to report the response created by moderator
            Then the response should not be able to be reported
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
        page.cannot_vote_response('response_self_author')
        page.vote_response('response_other_author')
        page.cannot_report_response('response_self_author')
        page.report_response('response_other_author')
        page.endorse_response('response_self_author')
        page.endorse_response('response_other_author')

    @attr('a11y')
    def test_page_accessibility(self):
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
            ]
        })
        page.visit()
        page.a11y_audit.check_for_accessibility_errors()


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

    @attr(shard=2)
    def test_edit_comment_as_student(self):
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_visible("comment_other_author"))
        self.assertFalse(page.is_comment_editable("comment_other_author"))
        self.edit_comment(page, "comment_self_author")

    @attr(shard=2)
    def test_edit_comment_as_moderator(self):
        self.setup_user(roles=["Moderator"])
        self.setup_view()
        page = self.create_single_thread_page("comment_edit_test_thread")
        page.visit()
        self.assertTrue(page.is_comment_editable("comment_self_author"))
        self.assertTrue(page.is_comment_editable("comment_other_author"))
        self.edit_comment(page, "comment_self_author")
        self.edit_comment(page, "comment_other_author")

    @attr(shard=2)
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

    @attr(shard=2)
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

    @attr('a11y')
    def test_page_accessibility(self):
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("comment_edit_test_thread")
        page.visit()
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
            ]
        })
        page.a11y_audit.check_for_accessibility_errors()


@attr(shard=2)
class DiscussionEditorPreviewTest(UniqueCourseTest):
    def setUp(self):
        super(DiscussionEditorPreviewTest, self).setUp()
        CourseFixture(**self.course_info).install()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.page = DiscussionTabHomePage(self.browser, self.course_id)
        self.page.visit()
        self.page.click_new_post_button()

    def test_text_rendering(self):
        """When I type plain text into the editor, it should be rendered as plain text in the preview box"""
        self.page.set_new_post_editor_value("Some plain text")
        self.assertEqual(self.page.get_new_post_preview_value(), "<p>Some plain text</p>")

    def test_markdown_rendering(self):
        """When I type Markdown into the editor, it should be rendered as formatted Markdown in the preview box"""
        self.page.set_new_post_editor_value(
            "Some markdown\n"
            "\n"
            "- line 1\n"
            "- line 2"
        )

        self.assertEqual(self.page.get_new_post_preview_value(), (
            "<p>Some markdown</p>\n"
            "\n"
            "<ul>\n"
            "<li>line 1</li>\n"
            "<li>line 2</li>\n"
            "</ul>"
        ))

    def test_mathjax_rendering_in_order(self):
        """
        Tests that mathjax is rendered in proper order.

        When user types mathjax expressions into discussion editor, it should render in the proper
        order.
        """
        self.page.set_new_post_editor_value(
            'Text line 1 \n'
            '$$e[n]=d_1$$ \n'
            'Text line 2 \n'
            '$$e[n]=d_2$$'
        )

        self.assertEqual(self.page.get_new_post_preview_text(), 'Text line 1\nText line 2')


@attr(shard=2)
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
        self.discussion_page.show_thread(thread_id)
        self.thread_page = self.discussion_page.thread_page  # pylint: disable=attribute-defined-outside-init

    @attr('a11y')
    def test_inline_a11y(self):
        """
        Tests Inline Discussion for accessibility issues.
        """
        self.setup_multiple_threads(thread_count=3)

        # First test the a11y of the expanded list of threads
        self.discussion_page.expand_discussion()
        self.discussion_page.a11y_audit.config.set_rules({
            'ignore': [
                'section'
            ]
        })
        self.discussion_page.a11y_audit.check_for_accessibility_errors()

        # Now show the first thread and test the a11y again
        self.discussion_page.show_thread(self.thread_ids[0])
        self.discussion_page.a11y_audit.check_for_accessibility_errors()

        # Finally show the new post form and test its a11y
        self.discussion_page.click_new_post_button()
        self.discussion_page.a11y_audit.check_for_accessibility_errors()

    def test_add_a_post_is_present_if_can_create_thread_when_expanded(self):
        self.discussion_page.expand_discussion()
        # Add a Post link is present
        self.assertTrue(self.discussion_page.q(css='.new-post-btn').present)

    def test_initial_render(self):
        self.assertFalse(self.discussion_page.is_discussion_expanded())

    def test_expand_discussion_empty(self):
        self.discussion_page.expand_discussion()
        self.assertEqual(self.discussion_page.get_num_displayed_threads(), 0)

    def check_anonymous_to_peers(self, is_staff):
        thread = Thread(id=uuid4().hex, anonymous_to_peers=True, commentable_id=self.discussion_id)
        thread_fixture = SingleThreadViewFixture(thread)
        thread_fixture.push()
        self.setup_thread_page(thread.get("id"))  # pylint: disable=no-member
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
        self.setup_thread_page(thread.get("id"))  # pylint: disable=no-member
        self.assertFalse(self.thread_page.has_add_response_button())
        self.assertFalse(self.thread_page.is_element_visible("action-more"))

    def test_dual_discussion_xblock(self):
        """
        Scenario: Two discussion xblocks in one unit shouldn't override their actions
        Given that I'm on a courseware page where there are two inline discussion
        When I click on the first discussion block's new post button
        Then I should be shown only the new post form for the first block
        When I click on the second discussion block's new post button
        Then I should be shown both new post forms
        When I cancel the first form
        Then I should be shown only the new post form for the second block
        When I cancel the second form
        And I click on the first discussion block's new post button
        Then I should be shown only the new post form for the first block
        When I cancel the first form
        Then I should be shown none of the forms
        """
        self.discussion_page.wait_for_page()
        self.additional_discussion_page.wait_for_page()

        # Expand the first discussion, click to add a post
        self.discussion_page.expand_discussion()
        self.discussion_page.click_new_post_button()

        # Verify that only the first discussion's form is shown
        self.assertIsNotNone(self.discussion_page.new_post_form)
        self.assertIsNone(self.additional_discussion_page.new_post_form)

        # Expand the second discussion, click to add a post
        self.additional_discussion_page.expand_discussion()
        self.additional_discussion_page.click_new_post_button()

        # Verify that both discussion's forms are shown
        self.assertIsNotNone(self.discussion_page.new_post_form)
        self.assertIsNotNone(self.additional_discussion_page.new_post_form)

        # Cancel the first form
        self.discussion_page.click_cancel_new_post()

        # Verify that only the second discussion's form is shown
        self.assertIsNone(self.discussion_page.new_post_form)
        self.assertIsNotNone(self.additional_discussion_page.new_post_form)

        # Cancel the second form and click to show the first one
        self.additional_discussion_page.click_cancel_new_post()
        self.discussion_page.click_new_post_button()

        # Verify that only the first discussion's form is shown
        self.assertIsNotNone(self.discussion_page.new_post_form)
        self.assertIsNone(self.additional_discussion_page.new_post_form)

        # Cancel the first form
        self.discussion_page.click_cancel_new_post()

        # Verify that neither discussion's forms are shwon
        self.assertIsNone(self.discussion_page.new_post_form)
        self.assertIsNone(self.additional_discussion_page.new_post_form)


@attr(shard=2)
class DiscussionUserProfileTest(UniqueCourseTest):
    """
    Tests for user profile page in discussion tab.
    """

    PAGE_SIZE = 20  # discussion.views.THREADS_PER_PAGE
    PROFILED_USERNAME = "profiled-user"

    def setUp(self):
        super(DiscussionUserProfileTest, self).setUp()
        self.setup_course()
        # The following line creates a user enrolled in our course, whose
        # threads will be viewed, but not the one who will view the page.
        # It isn't necessary to log them in, but using the AutoAuthPage
        # saves a lot of code.
        self.profiled_user_id = self.setup_user(username=self.PROFILED_USERNAME)
        # now create a second user who will view the profile.
        self.user_id = self.setup_user()

    def setup_course(self):
        """
        Set up the for the course discussion user-profile tests.
        """
        return CourseFixture(**self.course_info).install()

    def setup_user(self, roles=None, **user_info):
        """
        Helper method to create and authenticate a user.
        """
        roles_str = ''
        if roles:
            roles_str = ','.join(roles)
        return AutoAuthPage(self.browser, course_id=self.course_id, roles=roles_str, **user_info).visit().get_user_id()

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
        for __ in range(current_page, total_pages):
            _check_page()
            if current_page < total_pages:
                page.click_on_page(current_page + 1)
                current_page += 1

        # click all the way back down
        for __ in range(current_page, 0, -1):
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

    def test_learner_profile_roles(self):
        """
        Test that on the learner profile page user roles are correctly listed according to the course.
        """
        # Setup a learner with roles in a Course-A.
        expected_student_roles = ['Administrator', 'Community TA', 'Moderator', 'Student']
        self.profiled_user_id = self.setup_user(
            roles=expected_student_roles,
            username=self.PROFILED_USERNAME
        )

        # Visit the page and verify the roles are listed correctly.
        page = self.check_pages(1)
        student_roles = page.get_user_roles()
        self.assertEqual(student_roles, ', '.join(expected_student_roles))

        # Save the course_id of Course-A before setting up a new course.
        old_course_id = self.course_id

        # Setup Course-B and set user do not have additional roles and test roles are displayed correctly.
        self.course_info['number'] = self.unique_id
        self.setup_course()
        new_course_id = self.course_id

        # Set the user to have no extra role in the Course-B and verify the existing
        # user is updated.
        profiled_student_user_id = self.setup_user(roles=None, username=self.PROFILED_USERNAME)
        self.assertEqual(self.profiled_user_id, profiled_student_user_id)
        self.assertNotEqual(old_course_id, new_course_id)

        # Visit the user profile in course discussion page of Course-B. Make sure the
        # roles are listed correctly.
        page = self.check_pages(1)
        self.assertEqual(page.get_user_roles(), u'Student')


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

    @attr(shard=2)
    def test_no_rewrite(self):
        self.setup_corrected_text(None)
        self.page.perform_search()
        self.check_search_alert_messages(["no posts"])

    @attr(shard=2)
    def test_rewrite_dismiss(self):
        self.setup_corrected_text("foo")
        self.page.perform_search()
        self.check_search_alert_messages(["foo"])
        self.page.dismiss_alert_message("foo")
        self.check_search_alert_messages([])

    @attr(shard=2)
    def test_new_search(self):
        self.setup_corrected_text("foo")
        self.page.perform_search()
        self.check_search_alert_messages(["foo"])

        self.setup_corrected_text("bar")
        self.page.perform_search()
        self.check_search_alert_messages(["bar"])

        self.setup_corrected_text(None)
        self.page.perform_search()
        self.check_search_alert_messages(["no posts"])

    @attr(shard=2)
    def test_rewrite_and_user(self):
        self.setup_corrected_text("foo")
        self.page.perform_search(self.SEARCHED_USERNAME)
        self.check_search_alert_messages(["foo", self.SEARCHED_USERNAME])

    @attr(shard=2)
    def test_user_only(self):
        self.setup_corrected_text(None)
        self.page.perform_search(self.SEARCHED_USERNAME)
        self.check_search_alert_messages(["no posts", self.SEARCHED_USERNAME])
        # make sure clicking the link leads to the user profile page
        UserProfileViewFixture([]).push()
        self.page.get_search_alert_links().first.click()
        DiscussionUserProfilePage(
            self.browser,
            self.course_id,
            self.searched_user_id,
            self.SEARCHED_USERNAME
        ).wait_for_page()

    @attr('a11y')
    def test_page_accessibility(self):
        self.page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
            ]
        })
        self.page.a11y_audit.check_for_accessibility_errors()


@attr(shard=2)
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
        self.sort_page.show_all_discussions()

    def test_default_sort_preference(self):
        """
        Test to check the default sorting preference of user. (Default = date )
        """
        selected_sort = self.sort_page.get_selected_sort_preference()
        self.assertEqual(selected_sort, "activity")

    @skip_if_browser('chrome')  # TODO TE-1542 and TE-1543
    def test_change_sort_preference(self):
        """
        Test that if user sorting preference is changing properly.
        """
        selected_sort = ""
        for sort_type in ["votes", "comments", "activity"]:
            self.assertNotEqual(selected_sort, sort_type)
            self.sort_page.change_sort_preference(sort_type)
            selected_sort = self.sort_page.get_selected_sort_preference()
            self.assertEqual(selected_sort, sort_type)

    @skip_if_browser('chrome')  # TODO TE-1542 and TE-1543
    def test_last_preference_saved(self):
        """
        Test that user last preference is saved.
        """
        selected_sort = ""
        for sort_type in ["votes", "comments", "activity"]:
            self.assertNotEqual(selected_sort, sort_type)
            self.sort_page.change_sort_preference(sort_type)
            selected_sort = self.sort_page.get_selected_sort_preference()
            self.assertEqual(selected_sort, sort_type)
            self.sort_page.refresh_page()
            self.sort_page.show_all_discussions()
            selected_sort = self.sort_page.get_selected_sort_preference()
            self.assertEqual(selected_sort, sort_type)
