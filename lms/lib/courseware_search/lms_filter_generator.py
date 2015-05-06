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
from courseware.masquerade import setup_masquerade
from courseware.access import has_access


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

            staff_access = has_access(user, 'staff', course_key)
            if staff_access and 'request' in kwargs and kwargs['request']:
                request = kwargs['request']
                masquerade = setup_masquerade(request, course_key, staff_access)
                if masquerade.role != 'staff':
                    filter_dictionary['content_groups'] = masquerade.group_id
            else:
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
