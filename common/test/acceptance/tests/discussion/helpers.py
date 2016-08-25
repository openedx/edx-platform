"""
Helper functions and classes for discussion tests.
"""

from uuid import uuid4
import json

from common.test.acceptance.fixtures import LMS_BASE_URL
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.fixtures.discussion import (
    SingleThreadViewFixture,
    Thread,
    Response,
)
from common.test.acceptance.pages.lms.discussion import DiscussionTabSingleThreadPage
from common.test.acceptance.tests.helpers import UniqueCourseTest


class BaseDiscussionMixin(object):
    """
    A mixin containing methods common to discussion tests.
    """
    def setup_thread(self, num_responses, **thread_kwargs):
        """
        Create a test thread with the given number of responses, passing all
        keyword arguments through to the Thread fixture, then invoke
        setup_thread_page.
        """
        thread_id = "test_thread_{}".format(uuid4().hex)
        thread_fixture = SingleThreadViewFixture(
            Thread(id=thread_id, commentable_id=self.discussion_id, **thread_kwargs)
        )
        for i in range(num_responses):
            thread_fixture.addResponse(Response(id=str(i), body=str(i)))
        thread_fixture.push()
        self.setup_thread_page(thread_id)
        return thread_id


class CohortTestMixin(object):
    """
    Mixin for tests of cohorted courses
    """
    def setup_cohort_config(self, course_fixture, auto_cohort_groups=None):
        """
        Sets up the course to use cohorting with the given list of auto_cohort_groups.
        If auto_cohort_groups is None, no auto cohorts are set.
        """
        course_fixture._update_xblock(course_fixture._course_location, {
            "metadata": {
                u"cohort_config": {
                    "auto_cohort_groups": auto_cohort_groups or [],
                    "cohorted_discussions": [],
                    "cohorted": True,
                },
            },
        })

    def disable_cohorting(self, course_fixture):
        """
        Disables cohorting for the current course fixture.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + '/cohorts/settings'  # pylint: disable=protected-access
        data = json.dumps({'is_cohorted': False})
        response = course_fixture.session.patch(url, data=data, headers=course_fixture.headers)
        self.assertTrue(response.ok, "Failed to disable cohorts")

    def add_manual_cohort(self, course_fixture, cohort_name):
        """
        Adds a cohort by name, returning its ID.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + '/cohorts/'
        data = json.dumps({"name": cohort_name, 'assignment_type': 'manual'})
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        self.assertTrue(response.ok, "Failed to create cohort")
        return response.json()['id']

    def add_user_to_cohort(self, course_fixture, username, cohort_id):
        """
        Adds a user to the specified cohort.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + "/cohorts/{}/add".format(cohort_id)
        data = {"users": username}
        course_fixture.headers['Content-type'] = 'application/x-www-form-urlencoded'
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        self.assertTrue(response.ok, "Failed to add user to cohort")


class BaseDiscussionTestCase(UniqueCourseTest):
    def setUp(self):
        super(BaseDiscussionTestCase, self).setUp()

        self.discussion_id = "test_discussion_{}".format(uuid4().hex)
        self.course_fixture = CourseFixture(**self.course_info)
        self.course_fixture.add_advanced_settings(
            {'discussion_topics': {'value': {'Test Discussion Topic': {'id': self.discussion_id}}}}
        )
        self.course_fixture.install()

    def create_single_thread_page(self, thread_id):
        """
        Sets up a `DiscussionTabSingleThreadPage` for a given
        `thread_id`.
        """
        return DiscussionTabSingleThreadPage(self.browser, self.course_id, self.discussion_id, thread_id)
