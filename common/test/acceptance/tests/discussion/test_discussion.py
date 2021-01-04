"""
Tests for discussion pages
"""


from uuid import uuid4

import pytest

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.fixtures.discussion import (
    Comment,
    Response,
    SingleThreadViewFixture,
    Thread,
)
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.discussion import (
    DiscussionTabHomePage,
    DiscussionTabSingleThreadPage,
)
from common.test.acceptance.tests.discussion.helpers import BaseDiscussionMixin, BaseDiscussionTestCase
from common.test.acceptance.tests.helpers import UniqueCourseTest
from openedx.core.lib.tests import attr

THREAD_CONTENT_WITH_LATEX = u"""Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
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

    @attr('a11y')
    def test_page_accessibility(self):
        self.page.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region'  # TODO: AC-932
            ]
        })
        self.page.a11y_audit.check_for_accessibility_errors()


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
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })

        self.thread_page_1.a11y_audit.check_for_accessibility_errors()

        self.thread_page_2.a11y_audit.config.set_rules({
            "ignore": [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'region'  # TODO: AC-932
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

    @attr('a11y')
    def test_page_accessibility(self):
        page = self.setup_openclosed_thread_page()
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'color-contrast',  # Commented out for now because they reproducibly fail on Jenkins but not locally
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        page.a11y_audit.check_for_accessibility_errors()

        page = self.setup_openclosed_thread_page(True)
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'color-contrast',  # Commented out for now because they reproducibly fail on Jenkins but not locally
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        page.a11y_audit.check_for_accessibility_errors()


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

    @attr('a11y')
    def test_page_accessibility(self):
        self.setup_user()
        self.setup_view()
        page = self.create_single_thread_page("response_edit_test_thread")
        page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
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
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        page.a11y_audit.check_for_accessibility_errors()

    @attr('a11y')
    @pytest.mark.skip(reason='This test is too flaky to run at all. TNL-6215')
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

    @attr('a11y')
    def test_page_accessibility(self):
        self.page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # TODO: AC-491
                'aria-required-children',  # TODO: AC-534
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.page.a11y_audit.check_for_accessibility_errors()
