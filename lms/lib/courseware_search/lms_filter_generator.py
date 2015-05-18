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
from xmodule.split_test_module import get_split_user_partitions

from search.filter_generator import SearchFilterGenerator
from openedx.core.djangoapps.course_groups.partition_scheme import get_cohorted_user_partition
from courseware.access import get_user_role


class LmsSearchFilterGenerator(SearchFilterGenerator):
    """ SearchFilterGenerator for LMS Search """

    def filter_dictionary(self, **kwargs):
        """ base implementation which filters via start_date """
        filter_dictionary = super(LmsSearchFilterGenerator, self).filter_dictionary(**kwargs)
        if 'user' in kwargs and 'course_id' in kwargs and kwargs['course_id']:
            user = kwargs['user']

            content_groups = []
            try:
                course_key = CourseKey.from_string(kwargs['course_id'])
            except InvalidKeyError:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])

            # Staff user looking at course as staff user
            if get_user_role(user, course_key) == 'staff':
                return filter_dictionary

            cohorted_user_partition = get_cohorted_user_partition(course_key)
            if cohorted_user_partition:
                partition_group = cohorted_user_partition.scheme.get_group_for_user(
                    course_key,
                    user,
                    cohorted_user_partition,
                )

                if partition_group:
                    content_groups.append(unicode(partition_group.id))

            course = modulestore().get_course(course_key)

            for split_test_user_partition in get_split_user_partitions(course.user_partitions):
                partition_group = split_test_user_partition.scheme.get_group_for_user(
                    course_key,
                    user,
                    split_test_user_partition,
                    assign=False,
                )

                if partition_group:
                    content_groups.append(unicode(partition_group.id))

            filter_dictionary['content_groups'] = content_groups if content_groups else None
        return filter_dictionary

    def field_dictionary(self, **kwargs):
        """ add course if provided otherwise add courses in which the user is enrolled in """
        field_dictionary = super(LmsSearchFilterGenerator, self).field_dictionary(**kwargs)
        if not kwargs.get('user'):
            field_dictionary['course'] = []
        elif not kwargs.get('course_id'):
            user_enrollments = CourseEnrollment.enrollments_for_user(kwargs['user'])
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
        org_filter_out_set = microsite.get_all_orgs()
        if not course_org_filter and org_filter_out_set:
            exclude_dictionary['org'] = list(org_filter_out_set)

        return exclude_dictionary
