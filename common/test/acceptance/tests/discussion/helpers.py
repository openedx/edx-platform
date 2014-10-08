"""
Helper functions and classes for discussion tests.
"""

from uuid import uuid4

from ...fixtures.discussion import (
    SingleThreadViewFixture,
    Thread,
    Response,
)
from ...fixtures import LMS_BASE_URL


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


class CohortTestMixin(object):
    """
    Mixin for tests of cohorted courses
    """
    def setup_cohort_config(self, course_fixture, auto_cohort_groups=None):
        """
        Sets up the course to use cohorting with the given list of auto_cohort_groups.
        If auto_cohort_groups is None, no auto cohort groups are set.
        """
        course_fixture._update_xblock(course_fixture._course_location, {
            "metadata": {
                u"cohort_config": {
                    "auto_cohort_groups": auto_cohort_groups or [],
                    "cohorted_discussions": [],
                    "cohorted": True
                },
            },
        })

    def add_manual_cohort(self, course_fixture, cohort_name):
        """
        Adds a cohort group by name, returning the ID for the group.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + '/cohorts/add'
        data = {"name": cohort_name}
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        self.assertTrue(response.ok, "Failed to create cohort")
        return response.json()['cohort']['id']

    def add_user_to_cohort(self, course_fixture, username, cohort_id):
        """
        Adds a user to the specified cohort group.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + "/cohorts/{}/add".format(cohort_id)
        data = {"users": username}
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        self.assertTrue(response.ok, "Failed to add user to cohort")
