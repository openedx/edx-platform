# -*- coding: utf-8 -*-
"""
ProgramEnrollment Views
"""
from __future__ import absolute_import, unicode_literals

from ccx_keys.locator import CCXLocator
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import transaction
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from organizations.models import Organization
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from course_modes.models import CourseMode
from lms.djangoapps.bulk_email.api import get_emails_enabled
from lms.djangoapps.certificates.api import get_certificate_for_user
from lms.djangoapps.course_api.api import get_course_run_url, get_due_dates
from lms.djangoapps.program_enrollments.api import (
    fetch_program_course_enrollments,
    fetch_program_enrollments,
    fetch_program_enrollments_by_student,
    get_provider_slug,
    get_saml_provider_for_organization,
    iter_program_course_grades,
    write_program_course_enrollments,
    write_program_enrollments
)
from lms.djangoapps.program_enrollments.constants import (
    ProgramCourseOperationStatuses,
    ProgramEnrollmentStatuses,
    ProgramOperationStatuses
)
from lms.djangoapps.program_enrollments.exceptions import ProviderDoesNotExistException
from openedx.core.djangoapps.catalog.utils import (
    course_run_keys_for_program,
    get_programs,
    get_programs_by_type,
    get_programs_for_organization,
    normalize_program_type
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, PaginatedAPIView
from student.helpers import get_resume_urls_for_enrollments
from student.models import CourseEnrollment
from student.roles import CourseInstructorRole, CourseStaffRole, UserBasedRole
from util.query import read_replica_or_default

from .constants import ENABLE_ENROLLMENT_RESET_FLAG, MAX_ENROLLMENT_RECORDS
from .serializers import (
    CourseRunOverviewListSerializer,
    ProgramCourseEnrollmentRequestSerializer,
    ProgramCourseEnrollmentSerializer,
    ProgramCourseGradeSerializer,
    ProgramEnrollmentCreateRequestSerializer,
    ProgramEnrollmentSerializer,
    ProgramEnrollmentUpdateRequestSerializer
)
from .utils import (
    ProgramCourseSpecificViewMixin,
    ProgramEnrollmentPagination,
    ProgramSpecificViewMixin,
    get_course_run_status,
    get_enrollment_http_code,
    verify_course_exists_and_in_program,
    verify_program_exists
)


class EnrollmentWriteMixin(object):
    """
    Common functionality for viewsets with enrollment-writing POST/PATCH/PUT methods.

    Provides a `handle_write_request` utility method, which depends on the
    definitions of `serializer_class_by_write_method`, `ok_write_statuses`,
    and `perform_enrollment_write`.
    """
    create_update_by_write_method = {
        'POST': (True, False),
        'PATCH': (False, True),
        'PUT': (True, True),
    }

    # Set in subclasses
    serializer_class_by_write_method = "set-me-to-a-dict-with-http-method-keys"
    ok_write_statuses = "set-me-to-a-set"

    def handle_write_request(self):
        """
        Create/modify program enrollments.
        Returns: Response
        """
        serializer_class = self.serializer_class_by_write_method[self.request.method]
        serializer = serializer_class(data=self.request.data, many=True)
        serializer.is_valid(raise_exception=True)
        num_requests = len(self.request.data)
        if num_requests > MAX_ENROLLMENT_RECORDS:
            return Response(
                '{} enrollments requested, but limit is {}.'.format(
                    MAX_ENROLLMENT_RECORDS, num_requests
                ),
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        create, update = self.create_update_by_write_method[self.request.method]
        results = self.perform_enrollment_write(
            serializer.validated_data, create, update
        )
        http_code = get_enrollment_http_code(
            results.values(), self.ok_write_statuses
        )
        return Response(status=http_code, data=results, content_type='application/json')

    def perform_enrollment_write(self, enrollment_requests, create, update):
        """
        Perform the write operation. Implemented in subclasses.

        Arguments:
            enrollment_requests: list[dict]
            create (bool)
            update (bool)

        Returns: dict[str: str]
            Map from external keys to enrollment write statuses.
        """
        raise NotImplementedError()


class ProgramEnrollmentsView(
        EnrollmentWriteMixin,
        DeveloperErrorViewMixin,
        ProgramSpecificViewMixin,
        PaginatedAPIView,
):
    """
    A view for Create/Read/Update methods on Program Enrollment data.

    Path: `/api/program_enrollments/v1/programs/{program_uuid}/enrollments/`
    The path can contain an optional `page_size?=N` query parameter.  The default page size is 100.

    Returns:
      * 200: OK - Contains a paginated set of program enrollment data.
      * 401: The requesting user is not authenticated.
      * 403: The requesting user lacks access for the given program.
      * 404: The requested program does not exist.

    Response:
    In the case of a 200 response code, the response will include a paginated
    data set.  The `results` section of the response consists of a list of
    program enrollment records, where each record contains the following keys:
      * student_key: The identifier of the student enrolled in the program.
      * status: The student's enrollment status.
      * account_exists: A boolean indicating if the student has created an edx-platform user account.
      * curriculum_uuid: The curriculum UUID of the enrollment record for the (student, program).

    Example:
    {
        "next": null,
        "previous": "http://testserver.com/api/program_enrollments/v1/programs/{program_uuid}/enrollments/?curor=abcd",
        "results": [
            {
                "student_key": "user-0", "status": "pending",
                "account_exists": False, "curriculum_uuid": "00000000-1111-2222-3333-444444444444"
            },
            {
                "student_key": "user-1", "status": "pending",
                "account_exists": False, "curriculum_uuid": "00000001-1111-2222-3333-444444444444"
            },
            {
                "student_key": "user-2", "status": "enrolled",
                "account_exists": True, "curriculum_uuid": "00000002-1111-2222-3333-444444444444"
            },
            {
                "student_key": "user-3", "status": "enrolled",
                "account_exists": True, "curriculum_uuid": "00000003-1111-2222-3333-444444444444"
            },
        ],
    }

    Create
    ==========
    Path: `/api/program_enrollments/v1/programs/{program_uuid}/enrollments/`
    Where the program_uuid will be the uuid for a program.

    Request body:
        * The request body will be a list of one or more students to enroll with the following schema:
            {
                'status': A choice of the following statuses: ['enrolled', 'pending', 'canceled', 'suspended', 'ended'],
                student_key: string representation of a learner in partner systems,
                'curriculum_uuid': string representation of a curriculum
            }
        Example:
            [
                {
                    "status": "enrolled",
                    "external_user_key": "123",
                    "curriculum_uuid": "2d7de549-b09e-4e50-835d-4c5c5080c566"
                },{
                    "status": "canceled",
                    "external_user_key": "456",
                    "curriculum_uuid": "2d7de549-b09e-4e50-835d-4c5c5080c566"
                },{
                    "status": "pending",
                    "external_user_key": "789",
                    "curriculum_uuid": "2d7de549-b09e-4e50-835d-4c5c5080c566"
                },{
                    "status": "suspended",
                    "external_user_key": "abc",
                    "curriculum_uuid": "2d7de549-b09e-4e50-835d-4c5c5080c566"
                },
            ]

    Returns:
      * Response Body: {<external_user_key>: <status>} with as many keys as there were in the request body
        * external_user_key - string representation of a learner in partner systems
        * status - the learner's registration status
            * success statuses:
                * 'enrolled'
                * 'pending'
                * 'canceled'
                * 'suspended'
                * 'ended'
            * failure statuses:
                * 'duplicated' - the request body listed the same learner twice
                * 'conflict' - there is an existing enrollment for that learner, curriculum and program combo
                * 'invalid-status' - a status other than 'enrolled', 'pending', 'canceled', 'suspended',
                  or 'ended' was entered
      * 200: OK - All students were successfully enrolled.
        * Example json response:
            {
                '123': 'enrolled',
                '456': 'pending',
                '789': 'canceled,
                'abc': 'suspended'
            }
      * 207: MULTI-STATUS - Some students were successfully enrolled while others were not.
      Details are included in the JSON response data.
        * Example json response:
            {
                '123': 'duplicated',
                '456': 'conflict',
                '789': 'invalid-status,
                'abc': 'suspended'
            }
      * 403: FORBIDDEN - The requesting user lacks access to enroll students in the given program.
      * 404: NOT FOUND - The requested program does not exist.
      * 413: PAYLOAD TOO LARGE - Over 25 students supplied
      * 422: Unprocesable Entity - None of the students were successfully listed.

    Update
    ==========
    Path: `/api/program_enrollments/v1/programs/{program_uuid}/enrollments/`
    Where the program_uuid will be the uuid for a program.

    Request body:
        * The request body will be a list of one or more students with their updated enrollment status:
            {
                'status': A choice of the following statuses: [
                    'enrolled',
                    'pending',
                    'canceled',
                    'suspended',
                    'ended',
                ],
                student_key: string representation of a learner in partner systems
            }
        Example:
            [
                {
                    "status": "enrolled",
                    "external_user_key": "123",
                },{
                    "status": "canceled",
                    "external_user_key": "456",
                },{
                    "status": "pending",
                    "external_user_key": "789",
                },{
                    "status": "suspended",
                    "external_user_key": "abc",
                },
            ]

    Returns:
      * Response Body: {<external_user_key>: <status>} with as many keys as there were in the request body
        * external_user_key - string representation of a learner in partner systems
        * status - the learner's registration status
            * success statuses:
                * 'enrolled'
                * 'pending'
                * 'canceled'
                * 'suspended'
                * 'ended'
            * failure statuses:
                * 'duplicated' - the request body listed the same learner twice
                * 'conflict' - there is an existing enrollment for that learner, curriculum and program combo
                * 'invalid-status' - a status other than 'enrolled', 'pending', 'canceled', 'suspended', 'ended'
                                     was entered
                * 'not-in-program' - the user is not in the program and cannot be updated
      * 200: OK - All students were successfully enrolled.
        * Example json response:
            {
                '123': 'enrolled',
                '456': 'pending',
                '789': 'canceled,
                'abc': 'suspended'
            }
      * 207: MULTI-STATUS - Some students were successfully enrolled while others were not.
      Details are included in the JSON response data.
        * Example json response:
            {
                '123': 'duplicated',
                '456': 'not-in-program',
                '789': 'invalid-status,
                'abc': 'suspended'
            }
      * 403: FORBIDDEN - The requesting user lacks access to enroll students in the given program.
      * 404: NOT FOUND - The requested program does not exist.
      * 413: PAYLOAD TOO LARGE - Over 25 students supplied
      * 422: Unprocesable Entity - None of the students were successfully updated.
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)
    pagination_class = ProgramEnrollmentPagination

    # Overridden from `EnrollmentWriteMixin`
    serializer_class_by_write_method = {
        'POST': ProgramEnrollmentCreateRequestSerializer,
        'PATCH': ProgramEnrollmentUpdateRequestSerializer,
        'PUT': ProgramEnrollmentCreateRequestSerializer,
    }
    ok_write_statuses = ProgramOperationStatuses.__OK__

    @verify_program_exists
    def get(self, request, program_uuid=None):
        """ Defines the GET list endpoint for ProgramEnrollment objects. """
        enrollments = fetch_program_enrollments(
            self.program_uuid
        ).using(read_replica_or_default())
        paginated_enrollments = self.paginate_queryset(enrollments)
        serializer = ProgramEnrollmentSerializer(paginated_enrollments, many=True)
        return self.get_paginated_response(serializer.data)

    @verify_program_exists
    def post(self, request, program_uuid=None):
        """
        Create program enrollments for a list of learners
        """
        return self.handle_write_request()

    @verify_program_exists
    def patch(self, request, program_uuid=None):  # pylint: disable=unused-argument
        """
        Update program enrollments for a list of learners
        """
        return self.handle_write_request()

    @verify_program_exists
    def put(self, request, program_uuid=None):  # pylint: disable=unused-argument
        """
        Create/update program enrollments for a list of learners
        """
        return self.handle_write_request()

    def perform_enrollment_write(self, enrollment_requests, create, update):
        """
        Perform the program enrollment write operation.
        Overridden from `EnrollmentWriteMixin`.

        Arguments:
            enrollment_requests: list[dict]
            create (bool)
            update (bool)

        Returns: dict[str: str]
            Map from external keys to enrollment write statuses.
        """
        return write_program_enrollments(
            self.program_uuid, enrollment_requests, create=create, update=update
        )


class ProgramCourseEnrollmentsView(
        EnrollmentWriteMixin,
        DeveloperErrorViewMixin,
        ProgramCourseSpecificViewMixin,
        PaginatedAPIView,
):
    """
    A view for enrolling students in a course through a program,
    modifying program course enrollments, and listing program course
    enrollments.

    Path: ``/api/program_enrollments/v1/programs/{program_uuid}/courses/{course_id}/enrollments/``

    Accepts: [GET, POST, PATCH, PUT]

    For GET requests, the path can contain an optional `page_size?=N` query parameter.
    The default page size is 100.

    ------------------------------------------------------------------------------------
    POST, PATCH, PUT
    ------------------------------------------------------------------------------------

    **Returns**

        * 200: Returns a map of students and their enrollment status.
        * 207: Not all students enrolled. Returns resulting enrollment status.
        * 401: User is not authenticated
        * 403: User lacks read access organization of specified program.
        * 404: Program does not exist, or course does not exist in program
        * 422: Invalid request, unable to enroll students.

    ------------------------------------------------------------------------------------
    GET
    ------------------------------------------------------------------------------------

    **Returns**

        * 200: OK - Contains a paginated set of program course enrollment data.
        * 401: The requesting user is not authenticated.
        * 403: The requesting user lacks access for the given program/course.
        * 404: The requested program or course does not exist.

    **Response**

        In the case of a 200 response code, the response will include a paginated
        data set.  The `results` section of the response consists of a list of
        program course enrollment records, where each record contains the following keys:
          * student_key: The identifier of the student enrolled in the program and course.
          * status: The student's course enrollment status.
          * account_exists: A boolean indicating if the student has created an edx-platform user account.
          * curriculum_uuid: The curriculum UUID of the enrollment record for the (student, program).

    **Example**

        {
            "next": null,
            "previous": "http://testserver.com/api/program_enrollments/v1/programs/
                         {program_uuid}/courses/{course_id}/enrollments/?curor=abcd",
            "results": [
                {
                    "student_key": "user-0", "status": "inactive",
                    "account_exists": False, "curriculum_uuid": "00000000-1111-2222-3333-444444444444"
                },
                {
                    "student_key": "user-1", "status": "inactive",
                    "account_exists": False, "curriculum_uuid": "00000001-1111-2222-3333-444444444444"
                },
                {
                    "student_key": "user-2", "status": "active",
                    "account_exists": True, "curriculum_uuid": "00000002-1111-2222-3333-444444444444"
                },
                {
                    "student_key": "user-3", "status": "active",
                    "account_exists": True, "curriculum_uuid": "00000003-1111-2222-3333-444444444444"
                },
            ],
        }

    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)
    pagination_class = ProgramEnrollmentPagination

    # Overridden from `EnrollmentWriteMixin`
    serializer_class_by_write_method = {
        'POST': ProgramCourseEnrollmentRequestSerializer,
        'PATCH': ProgramCourseEnrollmentRequestSerializer,
        'PUT': ProgramCourseEnrollmentRequestSerializer,
    }
    ok_write_statuses = ProgramCourseOperationStatuses.__OK__

    @verify_course_exists_and_in_program
    def get(self, request, program_uuid=None, course_id=None):
        """
        Get a list of students enrolled in a course within a program.
        """
        enrollments = fetch_program_course_enrollments(
            program_uuid, course_id
        ).select_related(
            'program_enrollment'
        ).using(read_replica_or_default())
        paginated_enrollments = self.paginate_queryset(enrollments)
        serializer = ProgramCourseEnrollmentSerializer(paginated_enrollments, many=True)
        return self.get_paginated_response(serializer.data)

    @verify_course_exists_and_in_program
    def post(self, request, program_uuid=None, course_id=None):
        """
        Enroll a list of students in a course in a program
        """
        return self.handle_write_request()

    @verify_course_exists_and_in_program
    # pylint: disable=unused-argument
    def patch(self, request, program_uuid=None, course_id=None):
        """
        Modify the program course enrollments of a list of learners
        """
        return self.handle_write_request()

    @verify_course_exists_and_in_program
    # pylint: disable=unused-argument
    def put(self, request, program_uuid=None, course_id=None):
        """
        Create or Update the program course enrollments of a list of learners
        """
        return self.handle_write_request()

    def perform_enrollment_write(self, enrollment_requests, create, update):
        """
        Perform the program enrollment write operation.
        Overridden from `EnrollmentWriteMixin`.

        Arguments:
            enrollment_requests: list[dict]
            create (bool)
            update (bool)

        Returns: dict[str: str]
            Map from external keys to enrollment write statuses.
        """
        return write_program_course_enrollments(
            self.program_uuid,
            self.course_key,
            enrollment_requests,
            create=create,
            update=update,
        )


class ProgramCourseGradesView(
        DeveloperErrorViewMixin,
        ProgramCourseSpecificViewMixin,
        PaginatedAPIView,
):
    """
    A view for retrieving a paginated list of grades for all students enrolled
    in a given courserun through a given program.

    Path: ``/api/program_enrollments/v1/programs/{program_uuid}/courses/{course_id}/grades/``

    Accepts: [GET]

    For GET requests, the path can contain an optional `page_size?=N` query parameter.
    The default page size is 100.

    ------------------------------------------------------------------------------------
    GET
    ------------------------------------------------------------------------------------

    **Returns**
        * 200: OK - Contains a paginated set of program courserun grades.
        * 204: No Content - No grades to return
        * 207: Mixed result - Contains mixed list of program courserun grades
               and grade-fetching errors
        * 422: All failed - Contains list of grade-fetching errors
        * 401: The requesting user is not authenticated.
        * 403: The requesting user lacks access for the given program/course.
        * 404: The requested program or course does not exist.

    **Response**

        In the case of a 200/207/422 response code, the response will include a
        paginated data set.  The `results` section of the response consists of a
        list of grade records, where each successfully loaded record contains:
          * student_key: The identifier of the student enrolled in the program and course.
          * letter_grade: A letter grade as defined in grading policy
            (e.g. 'A' 'B' 'C' for 6.002x) or None.
          * passed: Boolean representing whether the course has been
            passed according to the course's grading policy.
          * percent: A float representing the overall grade for the course.
        and failed-to-load records contain:
          * student_key
          * error: error message from grades Exception

    **Example**

        207 Multi-Status
        {
            "next": null,
            "previous": "http://example.com/api/program_enrollments/v1/programs/
                         {program_uuid}/courses/{course_id}/grades/?cursor=abcd",
            "results": [;
                {
                    "student_key": "01709bffeae2807b6a7317",
                    "letter_grade": "Pass",
                    "percent": 0.95,
                    "passed": true
                },
                {
                    "student_key": "2cfe15e3380a52e7198237",
                    "error": "Timeout while calculating grade"
                },
                ...
            ],
        }
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)
    pagination_class = ProgramEnrollmentPagination

    @verify_course_exists_and_in_program
    def get(self, request, program_uuid=None, course_id=None):
        """
        Defines the GET list endpoint for ProgramCourseGrade objects.
        """
        grade_results = list(iter_program_course_grades(
            self.program_uuid, self.course_key, self.paginate_queryset
        ))
        serializer = ProgramCourseGradeSerializer(grade_results, many=True)
        response_code = self._calc_response_code(grade_results)
        return self.get_paginated_response(serializer.data, status_code=response_code)

    @staticmethod
    def _calc_response_code(grade_results):
        """
        Returns HTTP status code appropriate for list of results,
        which may be grades or errors.

        Arguments:
            enrollment_grade_results: list[BaseProgramCourseGrade]

        Returns: int
          * 200 for all success
          * 207 for mixed result
          * 422 for all failure
          * 204 for empty
        """
        if not grade_results:
            return status.HTTP_204_NO_CONTENT
        if all(result.is_error for result in grade_results):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        if any(result.is_error for result in grade_results):
            return status.HTTP_207_MULTI_STATUS
        return status.HTTP_200_OK


class UserProgramReadOnlyAccessView(DeveloperErrorViewMixin, PaginatedAPIView):
    """
    A view for checking the currently logged-in user's program read only access
    There are three major categories of users this API is differentiating. See the table below.

    --------------------------------------------------------------------------------------------
    | User Type        | API Returns                                                           |
    --------------------------------------------------------------------------------------------
    | edX staff        | All programs                                                          |
    --------------------------------------------------------------------------------------------
    | course staff     | All programs containing the courses of which the user is course staff |
    --------------------------------------------------------------------------------------------
    | learner          | All programs the learner is enrolled in                               |
    --------------------------------------------------------------------------------------------

    Path: `/api/program_enrollments/v1/programs/enrollments/`

    Returns:
      * 200: OK - Contains a list of all programs in which the user has read only acccess to.
      * 401: The requesting user is not authenticated.

    The list will be a list of objects with the following keys:
      * `uuid` - the identifier of the program in which the user has read only access to.
      * `slug` - the string from which a link to the corresponding program page can be constructed.

    Example:
    [
      {
        'uuid': '00000000-1111-2222-3333-444444444444',
        'slug': 'deadbeef'
      },
      {
        'uuid': '00000000-1111-2222-3333-444444444445',
        'slug': 'undead-cattle'
      }
    ]
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    DEFAULT_PROGRAM_TYPE = 'masters'

    def get(self, request):
        """
        How to respond to a GET request to this endpoint
        """

        request_user = request.user

        programs = []
        requested_program_type = normalize_program_type(request.GET.get('type', self.DEFAULT_PROGRAM_TYPE))

        if request_user.is_staff:
            programs = get_programs_by_type(request.site, requested_program_type)
        elif self.is_course_staff(request_user):
            programs = self.get_programs_user_is_course_staff_for(request_user, requested_program_type)
        else:
            program_enrollments = fetch_program_enrollments_by_student(
                user=request.user,
                program_enrollment_statuses=ProgramEnrollmentStatuses.__ACTIVE__,
            )
            uuids = [enrollment.program_uuid for enrollment in program_enrollments]
            programs = get_programs(uuids=uuids) or []

        programs_in_which_user_has_access = [
            {'uuid': program['uuid'], 'slug': program['marketing_slug']}
            for program in programs
        ]

        return Response(programs_in_which_user_has_access, status.HTTP_200_OK)

    def is_course_staff(self, user):
        """
        Returns true if the user is a course_staff member of any course within a program
        """
        staff_course_keys = self.get_course_keys_user_is_staff_for(user)
        return len(staff_course_keys)

    def get_course_keys_user_is_staff_for(self, user):
        """
        Return all the course keys the user is course instructor or course staff role for
        """
        # Get all the courses of which the user is course staff for. If None, return false
        def filter_ccx(course_access):
            """ CCXs cannot be edited in Studio and should not be filtered """
            return not isinstance(course_access.course_id, CCXLocator)

        instructor_courses = UserBasedRole(user, CourseInstructorRole.ROLE).courses_with_role()
        staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
        all_courses = list(filter(filter_ccx, instructor_courses | staff_courses))
        course_keys = {}
        for course_access in all_courses:
            if course_access.course_id is not None:
                course_keys[course_access.course_id] = course_access.course_id

        return list(course_keys.values())

    def get_programs_user_is_course_staff_for(self, user, program_type_filter):
        """
        Return a list of programs the user is course staff for.
        This function would take a list of course runs the user is staff of, and then
        try to get the Masters program associated with each course_runs.
        """
        program_list = []
        for course_key in self.get_course_keys_user_is_staff_for(user):
            course_run_programs = get_programs(course=course_key)
            for course_run_program in course_run_programs:
                if course_run_program and course_run_program.get('type').lower() == program_type_filter:
                    program_list.append(course_run_program)

        return program_list


class ProgramCourseEnrollmentOverviewView(
        DeveloperErrorViewMixin,
        ProgramSpecificViewMixin,
        APIView,
):
    """
    A view for getting data associated with a user's course enrollments
    as part of a program enrollment.

    Path: ``/api/program_enrollments/v1/programs/{program_uuid}/overview/``

    Accepts: [GET]

    ------------------------------------------------------------------------------------
    GET
    ------------------------------------------------------------------------------------

    **Returns**

        * 200: OK - Contains an object of user program course enrollment data.
        * 401: Unauthorized - The requesting user is not authenticated.
        * 403: Forbidden -The requesting user lacks access for the given program.
        * 404: Not Found - The requested program does not exist.

    **Response**

        In the case of a 200 response code, the response will include a
        data set.  The `course_runs` section of the response consists of a list of
        program course enrollment overview, where each overview contains the following keys:
            * course_run_id: the id for the course run
            * display_name: display name of the course run
            * resume_course_run_url: the absolute url that takes the user back to
                their position in the course run;
                if absent, user has not made progress in the course
            * course_run_url: the absolute url for the course run
            * start_date: the start date for the course run; null if no start date
            * end_date: the end date for the course run' null if no end date
            * course_run_status: the status of the course; one of "in_progress",
                "upcoming", and "completed"
            * emails_enabled: boolean representing whether emails are enabled for the course;
                if absent, the bulk email feature is either not enable at the platform
                level or is not enabled for the course; if True or False, bulk email
                feature is enabled, and value represents whether or not user wants
                to receive emails due_dates: a list of subsection due dates for the
                course run:
                ** name: name of the subsection
                ** url: deep link to the subsection
                ** date: due date for the subsection
            * micromasters_title: title of the MicroMasters program that the course run is a part of;
                if absent, the course run is not a part of a MicroMasters program
            * certificate_download_url: url to download a certificate, if available;
                if absent, certificate is not downloadable

    **Example**

        {
            "course_runs": [
                {
                    "course_run_id": "edX+AnimalsX+Aardvarks",
                    "display_name": "Astonishing Aardvarks",
                    "course_run_url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Aardvarks/course/",
                    "start_date": "2017-02-05T05:00:00Z",
                    "end_date": "2018-02-05T05:00:00Z",
                    "course_run_status": "completed"
                    "emails_enabled": true,
                    "due_dates": [
                        {
                            "name": "Introduction: What even is an aardvark?",
                            "url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Aardvarks/jump_to/
                                  block-v1:edX+AnimalsX+Aardvarks+type@chapter+block@1414ffd5143b4b508f739b563ab468b7",
                            "date": "2017-05-01T05:00:00Z"
                        },
                        {
                            "name": "Quiz: Aardvark or Anteater?",
                            "url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Aardvarks/jump_to/
                                    block-v1:edX+AnimalsX+Aardvarks+type@sequential+block@edx_introduction",
                            "date": "2017-03-05T00:00:00Z"
                        }
                    ],
                    "micromasters_title": "Animals",
                    "certificate_download_url": "https://courses.edx.org/certificates/123"
                },
                {
                    "course_run_id": "edX+AnimalsX+Baboons",
                    "display_name": "Breathtaking Baboons",
                    "course_run_url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Baboons/course/",
                    "start_date": "2018-02-05T05:00:00Z",
                    "end_date": null,
                    "course_run_status": "in_progress"
                    "emails_enabled": false,
                    "due_dates": [],
                    "micromasters_title": "Animals",
                    "certificate_download_url": "https://courses.edx.org/certificates/123",
                    "resume_course_run_url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Baboons/jump_to/
                                               block-v1:edX+AnimalsX+Baboons+type@sequential+block@edx_introduction"
                }
            ]
        }
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    @verify_program_exists
    def get(self, request, program_uuid=None):
        """
        Defines the GET endpoint for overviews of course enrollments
        for a user as part of a program.
        """
        user = request.user
        self._check_program_enrollment_exists(user, program_uuid)

        course_run_keys = [
            CourseKey.from_string(key)
            for key in course_run_keys_for_program(self.program)
        ]

        course_enrollments = CourseEnrollment.objects.filter(
            user=user,
            course_id__in=course_run_keys,
            mode__in=[CourseMode.VERIFIED, CourseMode.MASTERS],
            is_active=True,
        )

        overviews = CourseOverview.get_from_ids_if_exists(course_run_keys)

        course_run_resume_urls = get_resume_urls_for_enrollments(user, course_enrollments)

        course_runs = []

        for enrollment in course_enrollments:
            overview = overviews[enrollment.course_id]

            certificate_info = get_certificate_for_user(user.username, enrollment.course_id) or {}

            course_run_dict = {
                'course_run_id': enrollment.course_id,
                'display_name': overview.display_name_with_default,
                'course_run_status': get_course_run_status(overview, certificate_info),
                'course_run_url': get_course_run_url(request, enrollment.course_id),
                'start_date': overview.start,
                'end_date': overview.end,
                'due_dates': get_due_dates(request, enrollment.course_id, user),
            }

            emails_enabled = get_emails_enabled(user, enrollment.course_id)
            if emails_enabled is not None:
                course_run_dict['emails_enabled'] = emails_enabled

            if certificate_info.get('download_url'):
                course_run_dict['certificate_download_url'] = request.build_absolute_uri(
                    certificate_info['download_url']
                )

            if self.program['type'] == 'MicroMasters':
                course_run_dict['micromasters_title'] = self.program['title']

            if course_run_resume_urls.get(enrollment.course_id):
                relative_resume_course_run_url = course_run_resume_urls.get(
                    enrollment.course_id
                )
                course_run_dict['resume_course_run_url'] = request.build_absolute_uri(
                    relative_resume_course_run_url
                )

            course_runs.append(course_run_dict)

        serializer = CourseRunOverviewListSerializer({'course_runs': course_runs})
        return Response(serializer.data)

    @staticmethod
    def _check_program_enrollment_exists(user, program_uuid):
        """
        Raises ``PermissionDenied`` if the user is not enrolled in the program with the given UUID.
        """
        user_enrollment_qs = fetch_program_enrollments(
            program_uuid=program_uuid,
            users={user},
            program_enrollment_statuses={ProgramEnrollmentStatuses.ENROLLED},
        )
        if not user_enrollment_qs.exists():
            raise PermissionDenied


class EnrollmentDataResetView(APIView):
    """
    Resets enrollments and users for a given organization and set of programs.
    Note, this will remove ALL users from the input organization.

    Path: ``/api/program_enrollments/v1/integration-reset/``

    Accepts: [POST]

    ------------------------------------------------------------------------------------
    POST
    ------------------------------------------------------------------------------------

    **Returns**
        * 200: OK - Enrollments and users sucessfully deleted
        * 400: Bad Requeset - Program does not match the requested organization
        * 401: Unauthorized - The requesting user is not authenticated.
        * 404: Not Found - A requested program does not exist.

    **Response**
    """
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

    @transaction.atomic
    def post(self, request):
        """
        Reset enrollment and user data for organization
        """
        if not settings.FEATURES.get(ENABLE_ENROLLMENT_RESET_FLAG):
            return Response('reset not enabled on this environment', status.HTTP_501_NOT_IMPLEMENTED)

        try:
            org_key = request.data['organization']
        except KeyError:
            return Response("missing required body content 'organization'", status.HTTP_400_BAD_REQUEST)

        try:
            organization = Organization.objects.get(short_name=org_key)
        except Organization.DoesNotExist:
            return Response('organization {} not found'.format(org_key), status.HTTP_404_NOT_FOUND)

        try:
            provider = get_saml_provider_for_organization(organization)
        except ProviderDoesNotExistException:
            pass
        else:
            idp_slug = get_provider_slug(provider)
            call_command('remove_social_auth_users', idp_slug, force=True)

        programs = get_programs_for_organization(organization=organization.short_name)
        if programs:
            call_command('reset_enrollment_data', ','.join(programs), force=True)

        return Response('success')
