"""
This file contains implementation override of SearchFilterGenerator which will allow
    * Filter by all courses in which the user is enrolled in
"""

from student.models import CourseEnrollment
from search.filter_generator import SearchFilterGenerator
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

INCLUDE_SCHEMES = [CohortPartitionScheme, RandomUserPartitionScheme, ]
SCHEME_SUPPORTS_ASSIGNMENT = [RandomUserPartitionScheme, ]


class LmsSearchFilterGenerator(SearchFilterGenerator):
    """ SearchFilterGenerator for LMS Search """

    _user_enrollments = {}

    def _enrollments_for_user(self, user):
        """ Return the specified user's course enrollments """
        if user not in self._user_enrollments:
            self._user_enrollments[user] = CourseEnrollment.enrollments_for_user(user)
        return self._user_enrollments[user]

    def field_dictionary(self, **kwargs):
        """ add course if provided otherwise add courses in which the user is enrolled in """
        field_dictionary = super(LmsSearchFilterGenerator, self).field_dictionary(**kwargs)
        if not kwargs.get('user'):
            field_dictionary['course'] = []
        elif not kwargs.get('course_id'):
            user_enrollments = self._enrollments_for_user(kwargs['user'])
            field_dictionary['course'] = [unicode(enrollment.course_id) for enrollment in user_enrollments]

        # if we have an org filter, only include results for this org filter
        course_org_filter = configuration_helpers.get_value('course_org_filter')
        if course_org_filter:
            field_dictionary['org'] = course_org_filter

        return field_dictionary

    def exclude_dictionary(self, **kwargs):
        """
            Exclude any courses defined outside the current org.
        """
        exclude_dictionary = super(LmsSearchFilterGenerator, self).exclude_dictionary(**kwargs)
        course_org_filter = configuration_helpers.get_value('course_org_filter')
        # If we have a course filter we are ensuring that we only get those courses above
        if not course_org_filter:
            org_filter_out_set = configuration_helpers.get_all_orgs()
            if org_filter_out_set:
                exclude_dictionary['org'] = list(org_filter_out_set)

        return exclude_dictionary
