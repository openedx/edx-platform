"""
ProgramEnrollment V1 API internal utilities.
"""
from datetime import datetime, timedelta
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.utils.functional import cached_property
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import status
from rest_framework.pagination import CursorPagination

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.helpers import get_resume_urls_for_enrollments
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.bulk_email.api import get_emails_enabled
from lms.djangoapps.certificates.api import get_certificates_for_user_by_course_keys
from lms.djangoapps.course_api.api import get_course_run_url, get_due_dates
from lms.djangoapps.program_enrollments.api import fetch_program_enrollments
from lms.djangoapps.program_enrollments.constants import ProgramEnrollmentStatuses
from openedx.core.djangoapps.catalog.utils import course_run_keys_for_program, get_programs, is_course_run_in_program
from openedx.core.lib.api.view_utils import verify_course_exists

from .constants import CourseRunProgressStatuses


class ProgramEnrollmentPagination(CursorPagination):
    """
    Pagination class for views in the Program Enrollments app.
    """
    ordering = 'id'
    page_size = 100
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data, status_code=200, **kwargs):  # pylint: disable=arguments-differ
        """
        Return a response given serialized page data, optional status_code (defaults to 200),
        and kwargs. Each key-value pair of kwargs is added to the response data.
        """
        resp = super().get_paginated_response(data)
        for (key, value) in kwargs.items():
            resp.data[key] = value
        resp.status_code = status_code
        return resp


class UserProgramCourseEnrollmentPagination(CursorPagination):
    """
    Pagination parameters for UserProgramCourseEnrollmentView.
    """
    page_size = 10
    max_page_size = 25
    page_size_query_param = 'page_size'
    ordering = 'id'


class ProgramSpecificViewMixin:
    """
    A mixin for views that operate on or within a specific program.

    Requires `program_uuid` to be one of the kwargs to the view.
    """

    @cached_property
    def program(self):
        """
        The program specified by the `program_uuid` URL parameter.

        Returns: dict
        """
        return get_programs(uuid=self.program_uuid)

    @property
    def program_uuid(self):
        """
        The program specified by the `program_uuid` URL parameter.

        Returns: str
        """
        return self.kwargs['program_uuid']


class UserProgramSpecificViewMixin(ProgramSpecificViewMixin):
    """
    A mixin for views that operate on a specific program in the context of a user.

    Requires `program_uuid` to be one of the kwargs to the view.

    The property `target_user` returns the user that that we should operate with.
    """
    @property
    def target_user(self):
        """
        The user that this view's operations should operate in the context of.

        By default, this is the requesting user.

        This can be overriden in order to implement "user-parameterized" views,
        which, for example, a global staff member could use to see API responses
        in the context of a specific learner. This could be used to help implement
        masquerading.
        """
        return self.request.user


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
    def wrapped_function(self, *args, **kwargs):
        """
        Wraps the given view_function.
        """
        if self.program is None:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='no program exists with given key',
                error_code='program_does_not_exist'
            )
        return view_func(self, *args, **kwargs)
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
    @verify_course_exists()
    def wrapped_function(self, *args, **kwargs):
        """
        Wraps view function
        """
        if not is_course_run_in_program(self.course_key, self.program):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="the program's curriculum does not contain the given course",
                error_code='course_not_in_program'
            )
        return view_func(self, *args, **kwargs)
    return wrapped_function


def verify_user_enrolled_in_program(view_func):
    """
    Raised PermissionDenied if the `target_user` is not enrolled in the program.

    Expects to be used within a UserProgramViewMixin subclass.
    """
    @wraps(view_func)
    def wrapped_function(self, *args, **kwargs):
        """
        Wraps the given view_function.
        """
        user_enrollment_qs = fetch_program_enrollments(
            program_uuid=self.program_uuid,
            users={self.target_user},
            program_enrollment_statuses={ProgramEnrollmentStatuses.ENROLLED},
        )
        if not user_enrollment_qs.exists():
            raise PermissionDenied
        return view_func(self, *args, **kwargs)
    return wrapped_function


def get_enrollments_for_courses_in_program(user, program):
    """
    Get a user's active enrollments for course runs with the given program.

    Note that this is distinct from the user's *program course enrollments*,
    which refers to courses that were enrollmed in *through* a program.

    In the case of this function, the course runs themselves must be part of the
    program, but the enrollments do not need to be associated with a program enrollment.

    Arguments:
        user (User)
        program (dict)

    Returns QuerySet[CourseEnrollment]
    """
    course_keys = [
        CourseKey.from_string(key)
        for key in course_run_keys_for_program(program)
    ]
    return CourseEnrollment.objects.filter(
        user=user,
        course_id__in=course_keys,
        mode__in=[
            CourseMode.VERIFIED, CourseMode.MASTERS, CourseMode.EXECUTIVE_EDUCATION,
            CourseMode.PAID_EXECUTIVE_EDUCATION, CourseMode.PAID_BOOTCAMP
        ],
        is_active=True,
    )


def get_enrollment_overviews(user, program, enrollments, request):
    """
    Get a list of overviews for a user's course run enrollments within a program.

    Arguments:
        user (User)
        program (dict)
        enrollments (iterable[CourseEnrollment])
        request (HttpRequest): Source HTTP request. Needed for URL generation.

    Returns list[dict]
    """
    overviews_by_course_key = {
        enrollment.course.id: enrollment.course for enrollment in enrollments
    }
    course_keys = list(overviews_by_course_key.keys())
    certficates_by_course_key = get_certificates_for_user_by_course_keys(user, course_keys)
    resume_urls_by_course_key = get_resume_urls_for_enrollments(user, enrollments)
    return [
        get_single_enrollment_overview(
            user=user,
            program=program,
            course_overview=overviews_by_course_key[enrollment.course_id],
            certificate_info=certficates_by_course_key.get(enrollment.course_id, {}),
            relative_resume_url=resume_urls_by_course_key.get(enrollment.course_id),
            request=request,
        )
        for enrollment in enrollments
    ]


def get_single_enrollment_overview(
        user,
        program,
        course_overview,
        certificate_info,
        relative_resume_url,
        request,
):
    """
    Get an overview of a user's enrollment in a course run within a program.

    Arguments:
        user (User)
        program (Program)
        course_overview (CourseOverview)
        certificate_info (dict): Info about a user's certificate in this course run.
        relative_resume_url (str): URL to resume course. Relative to LMS root.
        request (HttpRequest): Source HTTP request. Needed for URL generation.

    Returns: dict
    """
    course_key = course_overview.id
    course_run_status = get_course_run_status(course_overview, certificate_info)
    due_dates = (
        get_due_dates(request, course_key, user)
        if course_run_status == CourseRunProgressStatuses.IN_PROGRESS
        else []
    )
    result = {
        'course_run_id': str(course_key),
        'display_name': course_overview.display_name_with_default,
        'course_run_status': course_run_status,
        'course_run_url': get_course_run_url(request, course_key),
        'start_date': course_overview.start,
        'end_date': course_overview.end,
        'due_dates': due_dates,
    }
    emails_enabled = get_emails_enabled(user, course_key)
    if emails_enabled is not None:
        result['emails_enabled'] = emails_enabled
    download_url = certificate_info.get('download_url')
    if download_url:
        result['certificate_download_url'] = request.build_absolute_uri(
            certificate_info['download_url']
        )
    if program['type'] == 'MicroMasters':
        result['micromasters_title'] = program['title']
    if relative_resume_url:
        result['resume_course_run_url'] = request.build_absolute_uri(relative_resume_url)
    return result


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
