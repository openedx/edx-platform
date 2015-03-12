"""
This file contains implementation override of SearchFilterGenerator which will allow
    * Filter by all courses in which the user is enrolled in
"""

from search.filter_generator import SearchFilterGenerator

from lms.djangoapps.courseware.courses import get_courses


class LmsSearchFilterGenerator(SearchFilterGenerator):
    """ SearchFilterGenerator for LMS Search """

    def field_dictionary(self, **kwargs):
        """ add course if provided otherwise add courses in which the user is enrolled in """
        field_dictionary = super(LmsSearchFilterGenerator, self).field_dictionary(**kwargs)
        if "course_id" not in kwargs:
            field_dictionary['courses'] = [unicode(course.id) for course in get_courses(kwargs['user'])]

        return field_dictionary
