# -*- coding: utf-8 -*-
"""
ProgramEnrollment Views
"""
from __future__ import absolute_import, unicode_literals

from functools import wraps

from django.http import Http404
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.pagination import CursorPagination

from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.lib.api.view_utils import verify_course_exists


def verify_program_exists(view_func):
    """
    Raises:
        An API error if the `program_uuid` kwarg in the wrapped function
        does not exist in the catalog programs cache.
    """
    @wraps(view_func)
    def wrapped_function(self, request, **kwargs):
        """
        Wraps the given view_function.
        """
        program_uuid = kwargs['program_uuid']
        program = get_programs(uuid=program_uuid)
        if not program:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='no program exists with given key',
                error_code='program_does_not_exist'
            )
        return view_func(self, request, **kwargs)
    return wrapped_function


def verify_course_exists_and_in_program(view_func):
    """
    Raises:
        An api error if the course run specified by the `course_key` kwarg
        in the wrapped function is not part of the curriculum of the program
        specified by the `program_uuid` kwarg

    Assumes that the program exists and that a program has exactly one active curriculum
    """
    @wraps(view_func)
    @verify_course_exists
    def wrapped_function(self, request, **kwargs):
        """
        Wraps view function
        """
        course_key = CourseKey.from_string(kwargs['course_id'])
        program_uuid = kwargs['program_uuid']
        program = get_programs(uuid=program_uuid)
        active_curricula = [c for c in program['curricula'] if c['is_active']]
        if not active_curricula:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="the program does not have an active curriculum",
                error_code='no_active_curriculum'
            )

        curriculum = active_curricula[0]

        if not is_course_in_curriculum(curriculum, course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="the program's curriculum does not contain the given course",
                error_code='course_not_in_program'
            )
        return view_func(self, request, **kwargs)

    def is_course_in_curriculum(curriculum, course_key):
        for course in curriculum['courses']:
            for course_run in course['course_runs']:
                if CourseKey.from_string(course_run["key"]) == course_key:
                    return True

    return wrapped_function


class ProgramEnrollmentPagination(CursorPagination):
    """
    Pagination class for Program Enrollments.
    """
    ordering = 'id'
    page_size = 100
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        """
        Get the page size based on the defined page size parameter if defined.
        """
        try:
            page_size_string = request.query_params[self.page_size_query_param]
            return int(page_size_string)
        except (KeyError, ValueError):
            pass

        return self.page_size


class ProgramSpecificViewMixin(object):
    """
    A mixin for views that operate on or within a specific program.
    """

    @property
    def program(self):
        """
        The program specified by the `program_uuid` URL parameter.
        """
        program = get_programs(uuid=self.kwargs['program_uuid'])
        if program is None:
            raise Http404()
        return program


class ProgramCourseRunSpecificViewMixin(ProgramSpecificViewMixin):
    """
    A mixin for views that operate on or within a specific course run in a program
    """

    @property
    def course_key(self):
        """
        The course key for the course run specified by the `course_id` URL parameter.
        """
        return CourseKey.from_string(self.kwargs['course_id'])
