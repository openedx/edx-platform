"""
This file contains implementation override of SearchFilterGenerator which will allow
    * Filter by all courses in which the user is enrolled in
"""
from microsite_configuration import microsite

from student.models import CourseEnrollment
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore

from search.filter_generator import SearchFilterGenerator
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from courseware.access import get_user_role


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

    def filter_dictionary(self, **kwargs):
        """ LMS implementation, adds filtering by user partition, course id and user """

        def get_group_for_user_partition(user_partition, course_key, user):
            """ Returns the specified user's group for user partition """
            if user_partition.scheme in SCHEME_SUPPORTS_ASSIGNMENT:
                return user_partition.scheme.get_group_for_user(
                    course_key,
                    user,
                    user_partition,
                    assign=False,
                )
            else:
                return user_partition.scheme.get_group_for_user(
                    course_key,
                    user,
                    user_partition,
                )

        def get_group_ids_for_user(course, user):
            """ Collect user partition group ids for user for this course """
            partition_groups = []
            for user_partition in course.user_partitions:
                if user_partition.scheme in INCLUDE_SCHEMES:
                    group = get_group_for_user_partition(user_partition, course.id, user)
                    if group:
                        partition_groups.append(group)
            partition_group_ids = [unicode(partition_group.id) for partition_group in partition_groups]
            return partition_group_ids if partition_group_ids else None

        filter_dictionary = super(LmsSearchFilterGenerator, self).filter_dictionary(**kwargs)
        if 'user' in kwargs:
            user = kwargs['user']

            if 'course_id' in kwargs and kwargs['course_id']:
                try:
                    course_key = CourseKey.from_string(kwargs['course_id'])
                except InvalidKeyError:
                    course_key = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])

                # Staff user looking at course as staff user
                if get_user_role(user, course_key) == 'staff':
                    return filter_dictionary
                # Need to check course exist (if course gets deleted enrollments don't get cleaned up)
                course = modulestore().get_course(course_key)
                if course:
                    filter_dictionary['content_groups'] = get_group_ids_for_user(course, user)
            else:
                user_enrollments = self._enrollments_for_user(user)
                content_groups = []
                for enrollment in user_enrollments:
                    course = modulestore().get_course(enrollment.course_id)
                    if course:
                        enrollment_group_ids = get_group_ids_for_user(course, user)
                        if enrollment_group_ids:
                            content_groups.extend(enrollment_group_ids)

                filter_dictionary['content_groups'] = content_groups if content_groups else None

        return filter_dictionary

    def field_dictionary(self, **kwargs):
        """ add course if provided otherwise add courses in which the user is enrolled in """
        field_dictionary = super(LmsSearchFilterGenerator, self).field_dictionary(**kwargs)
        if not kwargs.get('user'):
            field_dictionary['course'] = []
        elif not kwargs.get('course_id'):
            user_enrollments = self._enrollments_for_user(kwargs['user'])
            field_dictionary['course'] = [unicode(enrollment.course_id) for enrollment in user_enrollments]

        # if we have an org filter, only include results for this org filter
        course_org_filter = microsite.get_value('course_org_filter')
        if course_org_filter:
            field_dictionary['org'] = course_org_filter

        return field_dictionary

    def exclude_dictionary(self, **kwargs):
        """ If we are not on a microsite, then exclude any microsites that are defined """
        exclude_dictionary = super(LmsSearchFilterGenerator, self).exclude_dictionary(**kwargs)
        course_org_filter = microsite.get_value('course_org_filter')
        # If we have a course filter we are ensuring that we only get those courses above
        if not course_org_filter:
            org_filter_out_set = microsite.get_all_orgs()
            if org_filter_out_set:
                exclude_dictionary['org'] = list(org_filter_out_set)

        return exclude_dictionary
