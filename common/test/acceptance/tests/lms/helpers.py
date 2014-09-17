"""
Helper functions and classes for LMS tests.
"""

from ...fixtures import LMS_BASE_URL


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

    def add_manual_cohort(self, course_fixture, name):
        """
        Adds a cohort group by name, returning the ID for the group.
        """
        url = LMS_BASE_URL + "/courses/" + course_fixture._course_key + '/cohorts/add'
        data = {"name": name}
        response = course_fixture.session.post(url, data=data, headers=course_fixture.headers)
        self.assertTrue(response.ok, "Failed to create cohort")
        return response.json()['cohort']['id']
