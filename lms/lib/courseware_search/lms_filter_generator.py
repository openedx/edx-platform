"""
This file contains implementation override of SearchFilterGenerator which will allow
    * Filter by all courses in which the user is enrolled in
"""
from student.models import CourseEnrollment
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

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
                filter_dictionary['content_groups'] = unicode(partition_group.id) if partition_group else None
        return filter_dictionary

    def field_dictionary(self, **kwargs):
        """ add course if provided otherwise add courses in which the user is enrolled in """
        field_dictionary = super(LmsSearchFilterGenerator, self).field_dictionary(**kwargs)
        if not kwargs.get('user'):
            field_dictionary['course'] = []
        elif not kwargs.get('course_id'):
            user_enrollments = CourseEnrollment.enrollments_for_user(kwargs['user'])
            field_dictionary['course'] = [unicode(enrollment.course_id) for enrollment in user_enrollments]

        return field_dictionary
