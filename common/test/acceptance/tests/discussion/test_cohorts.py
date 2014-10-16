"""
Tests related to the cohorting feature.
"""
from uuid import uuid4

from helpers import BaseDiscussionMixin
from ...pages.lms.auto_auth import AutoAuthPage
from ..helpers import UniqueCourseTest
from ...fixtures.course import (CourseFixture, XBlockFixtureDesc)
from ...fixtures import LMS_BASE_URL

from ...pages.lms.discussion import (DiscussionTabSingleThreadPage, InlineDiscussionThreadPage, InlineDiscussionPage)
from ...pages.lms.courseware import CoursewarePage

from nose.plugins.attrib import attr


class NonCohortedDiscussionTestMixin(BaseDiscussionMixin):
    """
    Mixin for tests of non-cohorted courses.
    """
    def setup_cohorts(self):
        """
        No cohorts are desired for this mixin.
        """
        pass

    def test_non_cohort_visibility_label(self):
        self.setup_thread(1)
        self.assertEquals(self.thread_page.get_group_visibility_label(), "This post is visible to everyone.")


class CohortedDiscussionTestMixin(BaseDiscussionMixin):
    """
    Mixin for tests of cohorted courses.
    """
    def add_cohort(self, name):
        """
        Adds a cohort group by name, returning the ID for the group.
        """
        url = LMS_BASE_URL + "/courses/" + self.course_fixture._course_key + '/cohorts/add'
        data = {"name": name}
        response = self.course_fixture.session.post(url, data=data, headers=self.course_fixture.headers)
        self.assertTrue(response.ok, "Failed to create cohort")
        return response.json()['cohort']['id']

    def setup_cohorts(self):
        """
        Sets up the course to use cohorting with a single defined cohort group.
        """
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"cohort_config": {
                    "auto_cohort_groups": [],
                    "auto_cohort": False,
                    "cohorted_discussions": [],
                    "cohorted": True
                },
            },
        })
        self.cohort_1_name = "Cohort Group 1"
        self.cohort_1_id = self.add_cohort(self.cohort_1_name)

    def test_cohort_visibility_label(self):
        # Must be moderator to view content in a cohort other than your own
        AutoAuthPage(self.browser, course_id=self.course_id, roles="Moderator").visit()
        self.setup_thread(1, group_id=self.cohort_1_id)
        self.assertEquals(
            self.thread_page.get_group_visibility_label(),
            "This post is visible only to {}.".format(self.cohort_1_name)
        )


class DiscussionTabSingleThreadTest(UniqueCourseTest):
    """
    Tests for the discussion page displaying a single thread.
    """
    def setUp(self):
        super(DiscussionTabSingleThreadTest, self).setUp()
        self.discussion_id = "test_discussion_{}".format(uuid4().hex)
        # Create a course to register for
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.setup_cohorts()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def setup_thread_page(self, thread_id):
        self.thread_page = DiscussionTabSingleThreadPage(self.browser, self.course_id, thread_id)  # pylint:disable=W0201
        self.thread_page.visit()


@attr('shard_1')
class CohortedDiscussionTabSingleThreadTest(DiscussionTabSingleThreadTest, CohortedDiscussionTestMixin):
    """
    Tests for the discussion page displaying a single cohorted thread.
    """
    # Actual test method(s) defined in CohortedDiscussionTestMixin.
    pass


@attr('shard_1')
class NonCohortedDiscussionTabSingleThreadTest(DiscussionTabSingleThreadTest, NonCohortedDiscussionTestMixin):
    """
    Tests for the discussion page displaying a single non-cohorted thread.
    """
    # Actual test method(s) defined in NonCohortedDiscussionTestMixin.
    pass


class InlineDiscussionTest(UniqueCourseTest):
    """
    Tests for inline discussions
    """
    def setUp(self):
        super(InlineDiscussionTest, self).setUp()
        self.discussion_id = "test_discussion_{}".format(uuid4().hex)
        self.course_fixture = CourseFixture(**self.course_info).add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                            metadata={"discussion_id": self.discussion_id}
                        )
                    )
                )
            )
        ).install()
        self.setup_cohorts()

        self.user_id = AutoAuthPage(self.browser, course_id=self.course_id).visit().get_user_id()

    def setup_thread_page(self, thread_id):
        CoursewarePage(self.browser, self.course_id).visit()
        discussion_page = InlineDiscussionPage(self.browser, self.discussion_id)
        discussion_page.expand_discussion()
        self.assertEqual(discussion_page.get_num_displayed_threads(), 1)
        self.thread_page = InlineDiscussionThreadPage(self.browser, thread_id)  # pylint:disable=W0201
        self.thread_page.expand()


@attr('shard_1')
class CohortedInlineDiscussionTest(InlineDiscussionTest, CohortedDiscussionTestMixin):
    """
    Tests for cohorted inline discussions.
    """
    # Actual test method(s) defined in CohortedDiscussionTestMixin.
    pass


@attr('shard_1')
class NonCohortedInlineDiscussionTest(InlineDiscussionTest, NonCohortedDiscussionTestMixin):
    """
    Tests for non-cohorted inline discussions.
    """
    # Actual test method(s) defined in NonCohortedDiscussionTestMixin.
    pass
