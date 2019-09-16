# -*- coding: utf-8 -*-
"""
ProgramEnrollment V1 API internal utilities.
"""
from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
from functools import wraps

from django.urls import reverse
from django.utils.functional import cached_property
from edx_when.api import get_dates_for_course
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import status
from six import iteritems

from bulk_email.api import is_bulk_email_feature_enabled, is_user_opted_out_for_course
from lms.djangoapps.grades.rest_api.v1.utils import CourseEnrollmentPagination
from openedx.core.djangoapps.catalog.utils import get_programs, is_course_run_in_program
from openedx.core.lib.api.view_utils import verify_course_exists
from xmodule.modulestore.django import modulestore

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


def get_enrollment_http_code(result_statuses, ok_statuses):
    """
    Given a set of enrollment create/update statuses,
    return the appropriate HTTP status code.

    Arguments:
        result_statuses (sequence[str]): set of enrollment operation statuses
            (for example, 'enrolled', 'not-in-program', etc.)
        ok_statuses: sequence[str]: set of 'OK' (non-error) statuses
    """
    result_status_set = set(result_statuses)
    ok_status_set = set(ok_statuses)
    if not result_status_set:
        return status.HTTP_204_NO_CONTENT
    if result_status_set.issubset(ok_status_set):
        return status.HTTP_200_OK
    elif result_status_set & ok_status_set:
        return status.HTTP_207_MULTI_STATUS
    else:
        return status.HTTP_422_UNPROCESSABLE_ENTITY


def get_due_dates(request, course_key, user):
    """
    Get due date information for a user for blocks in a course.

    Arguments:
        request: the request object
        course_key (CourseKey): the CourseKey for the course
        user: the user object for which we want due date information

    Returns:
        due_dates (list): a list of dictionaries containing due date information
            keys:
                name: the display name of the block
                url: the deep link to the block
                date: the due date for the block
    """
    dates = get_dates_for_course(
        course_key,
        user,
    )

    store = modulestore()

    due_dates = []
    for (block_key, date_type), date in iteritems(dates):
        if date_type == 'due':
            block = store.get_item(block_key)

            # get url to the block in the course
            block_url = reverse('jump_to', args=[course_key, block_key])
            block_url = request.build_absolute_uri(block_url)

            due_dates.append({
                'name': block.display_name,
                'url': block_url,
                'date': date,
            })
    return due_dates


def get_course_run_url(request, course_id):
    """
    Get the URL to a course run.

    Arguments:
        request: the request object
        course_id (string): the course id of the course

    Returns:
        (string): the URL to the course run associated with course_id
    """
    course_run_url = reverse('openedx.course_experience.course_home', args=[course_id])
    return request.build_absolute_uri(course_run_url)


def get_emails_enabled(user, course_id):
    """
    Get whether or not emails are enabled in the context of a course.

    Arguments:
        user: the user object for which we want to check whether emails are enabled
        course_id (string): the course id of the course

    Returns:
        (bool): True if emails are enabled for the course associated with course_id for the user;
        False otherwise
    """
    if is_bulk_email_feature_enabled(course_id=course_id):
        return not is_user_opted_out_for_course(user=user, course_id=course_id)
    return None


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
