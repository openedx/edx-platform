# -*- coding: utf-8 -*-
"""
ProgramEnrollment V1 API internal utilities.
"""
from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
from functools import wraps

from django.utils.functional import cached_property
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import status

from bulk_email.api import is_bulk_email_feature_enabled, is_user_opted_out_for_course
from lms.djangoapps.grades.rest_api.v1.utils import CourseEnrollmentPagination
from openedx.core.djangoapps.catalog.utils import get_programs, is_course_run_in_program
from openedx.core.lib.api.view_utils import verify_course_exists

from .constants import CourseRunProgressStatuses


class ProgramEnrollmentPagination(CourseEnrollmentPagination):
    """
    Pagination class for views in the Program Enrollments app.
    """
    page_size = 100


class ProgramSpecificViewMixin(object):
    """
    A mixin for views that operate on or within a specific program.

    Requires `program_uuid` to be one of the kwargs to the view.
    """

    @cached_property
    def program(self):
        """
        The program specified by the `program_uuid` URL parameter.
        """
        return get_programs(uuid=self.program_uuid)

    @property
    def program_uuid(self):
        """
        The program specified by the `program_uuid` URL parameter.
        """
        return self.kwargs['program_uuid']


class ProgramCourseSpecificViewMixin(ProgramSpecificViewMixin):
    """
    A mixin for views that operate on or within a specific course run in a program

    Requires `course_id` to be one of the kwargs to the view.
    """

    @cached_property
    def course_key(self):
        """
        The course key for the course run specified by the `course_id` URL parameter.
        """
        return CourseKey.from_string(self.kwargs['course_id'])


def verify_program_exists(view_func):
    """
    Raises:
        An API error if the `program_uuid` kwarg in the wrapped function
        does not exist in the catalog programs cache.

    Expects to be used within a ProgramSpecificViewMixin subclass.
    """
    @wraps(view_func)
    def wrapped_function(self, request, **kwargs):
        """
        Wraps the given view_function.
        """
        if self.program is None:
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
        An api error if the course run specified by the `course_id` kwarg
        in the wrapped function is not part of the curriculum of the program
        specified by the `program_uuid` kwarg

    This decorator guarantees existance of the program and course, so wrapping
    alongside `verify_{program,course}_exists` is redundant.

    Expects to be used within a subclass of ProgramCourseSpecificViewMixin.
    """
    @wraps(view_func)
    @verify_program_exists
    @verify_course_exists
    def wrapped_function(self, request, **kwargs):
        """
        Wraps view function
        """
        if not is_course_run_in_program(self.course_key, self.program):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="the program's curriculum does not contain the given course",
                error_code='course_not_in_program'
            )
        return view_func(self, request, **kwargs)
    return wrapped_function


def get_course_run_status(course_overview, certificate_info):
    """
    Get the progress status of a course run, given the state of a user's
    certificate in the course.

    In the case of self-paced course runs, the run is considered completed when
    either the courserun has ended OR the user has earned a passing certificate
    30 days ago or longer.

    Arguments:
        course_overview (CourseOverview): the overview for the course run
        certificate_info: A dict containing the following keys:
            ``is_passing``: whether the  user has a passing certificate in the course run
            ``created``: the date the certificate was created

    Returns:
        status: one of (
            CourseRunProgressStatuses.COMPLETE,
            CourseRunProgressStatuses.IN_PROGRESS,
            CourseRunProgressStatuses.UPCOMING,
        )
    """
    is_certificate_passing = certificate_info.get('is_passing', False)
    certificate_creation_date = certificate_info.get('created', datetime.max)

    if course_overview.pacing == 'instructor':
        if course_overview.has_ended():
            return CourseRunProgressStatuses.COMPLETED
        elif course_overview.has_started():
            return CourseRunProgressStatuses.IN_PROGRESS
        else:
            return CourseRunProgressStatuses.UPCOMING
    elif course_overview.pacing == 'self':
        thirty_days_ago = datetime.now(UTC) - timedelta(30)
        certificate_completed = is_certificate_passing and (
            certificate_creation_date <= thirty_days_ago
        )
        if course_overview.has_ended() or certificate_completed:
            return CourseRunProgressStatuses.COMPLETED
        elif course_overview.has_started():
            return CourseRunProgressStatuses.IN_PROGRESS
        else:
            return CourseRunProgressStatuses.UPCOMING
    return None
