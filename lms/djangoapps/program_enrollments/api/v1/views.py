# -*- coding: utf-8 -*-
"""
ProgramEnrollment Views
"""
from __future__ import absolute_import, unicode_literals

import logging
from collections import Counter, OrderedDict
from datetime import datetime, timedelta
from functools import wraps
from pytz import UTC

from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from six import iteritems

from bulk_email.api import is_bulk_email_feature_enabled, is_user_opted_out_for_course
from edx_when.api import get_dates_for_course
from lms.djangoapps.certificates.api import get_certificate_for_user
from lms.djangoapps.program_enrollments.api.v1.constants import (
    CourseEnrollmentResponseStatuses,
    CourseRunProgressStatuses,
    MAX_ENROLLMENT_RECORDS,
    REQUEST_STUDENT_KEY,
)
from lms.djangoapps.program_enrollments.api.v1.serializers import (
    CourseRunOverviewListSerializer,
    ProgramCourseEnrollmentListSerializer,
    ProgramCourseEnrollmentRequestSerializer,
    ProgramEnrollmentListSerializer,
    ProgramEnrollmentSerializer,
)
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from lms.djangoapps.program_enrollments.utils import get_user_by_program_id
from student.helpers import get_resume_urls_for_enrollments
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, PaginatedAPIView, verify_course_exists
from util.query import use_read_replica_if_available

logger = logging.getLogger(__name__)


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


class ProgramEnrollmentsView(DeveloperErrorViewMixin, PaginatedAPIView):
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
                'status': A choice of the following statuses: ['enrolled', 'pending', 'withdrawn', 'suspended'],
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
                    "status": "withdrawn",
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
                * 'withdrawn'
                * 'suspended'
            * failure statuses:
                * 'duplicated' - the request body listed the same learner twice
                * 'conflict' - there is an existing enrollment for that learner, curriculum and program combo
                * 'invalid-status' - a status other than 'enrolled', 'pending', 'withdrawn', 'suspended' was entered
      * 201: CREATED - All students were successfully enrolled.
        * Example json response:
            {
                '123': 'enrolled',
                '456': 'pending',
                '789': 'withdrawn,
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
                'status': A choice of the following statuses: ['enrolled', 'pending', 'withdrawn', 'suspended'],
                student_key: string representation of a learner in partner systems
            }
        Example:
            [
                {
                    "status": "enrolled",
                    "external_user_key": "123",
                },{
                    "status": "withdrawn",
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
                * 'withdrawn'
                * 'suspended'
            * failure statuses:
                * 'duplicated' - the request body listed the same learner twice
                * 'conflict' - there is an existing enrollment for that learner, curriculum and program combo
                * 'invalid-status' - a status other than 'enrolled', 'pending', 'withdrawn', 'suspended' was entered
                * 'not-in-program' - the user is not in the program and cannot be updated
      * 201: CREATED - All students were successfully enrolled.
        * Example json response:
            {
                '123': 'enrolled',
                '456': 'pending',
                '789': 'withdrawn,
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

    @verify_program_exists
    def get(self, request, program_uuid=None):
        """ Defines the GET list endpoint for ProgramEnrollment objects. """
        enrollments = use_read_replica_if_available(
            ProgramEnrollment.objects.filter(program_uuid=program_uuid)
        )
        paginated_enrollments = self.paginate_queryset(enrollments)
        serializer = ProgramEnrollmentListSerializer(paginated_enrollments, many=True)
        return self.get_paginated_response(serializer.data)

    @verify_program_exists
    def post(self, request, *args, **kwargs):
        """
        Create program enrollments for a list of learners
        """
        if len(request.data) > MAX_ENROLLMENT_RECORDS:
            return Response(
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content_type='application/json',
            )

        program_uuid = kwargs['program_uuid']
        student_data = self._request_data_by_student_key(request, program_uuid)

        response_data = {}
        response_data.update(self._remove_duplicate_entries(request, student_data))
        response_data.update(self._remove_existing_entries(program_uuid, student_data))

        enrollments_to_create = {}

        for student_key, data in student_data.items():
            curriculum_uuid = data['curriculum_uuid']
            existing_user = get_user_by_program_id(student_key, program_uuid)

            if existing_user:
                data['user'] = existing_user.id

            serializer = ProgramEnrollmentSerializer(data=data)
            if serializer.is_valid():
                enrollments_to_create[(student_key, curriculum_uuid)] = serializer
                response_data[student_key] = data.get('status')
            else:
                if 'status' in serializer.errors and serializer.errors['status'][0].code == 'invalid_choice':
                    response_data[student_key] = CourseEnrollmentResponseStatuses.INVALID_STATUS
                else:
                    return Response(
                        'invalid enrollment record',
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    )

        # TODO: make this a bulk save - https://openedx.atlassian.net/browse/EDUCATOR-4305
        for (student_key, _), enrollment_serializer in enrollments_to_create.items():
            enrollment_serializer.save()

        return self._get_created_or_updated_response(request, enrollments_to_create, response_data)

    @verify_program_exists
    def patch(self, request, **kwargs):
        """
        Modify the program enrollments for a list of learners
        """
        if len(request.data) > MAX_ENROLLMENT_RECORDS:
            return Response(
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content_type='application/json',
            )

        program_uuid = kwargs['program_uuid']
        student_data = self._request_data_by_student_key(request, program_uuid)

        response_data = {}
        response_data.update(self._remove_duplicate_entries(request, student_data))

        existing_enrollments = {
            enrollment.external_user_key: enrollment
            for enrollment in
            ProgramEnrollment.bulk_read_by_student_key(program_uuid, student_data)
        }

        enrollments_to_create = {}

        for external_user_key in student_data.keys():
            if external_user_key not in existing_enrollments:
                student_data.pop(external_user_key)
                response_data[external_user_key] = CourseEnrollmentResponseStatuses.NOT_IN_PROGRAM

        for external_user_key, enrollment in existing_enrollments.items():
            student = {key: value for key, value in student_data[external_user_key].items() if key == 'status'}
            enrollment_serializer = ProgramEnrollmentSerializer(enrollment, data=student, partial=True)
            if enrollment_serializer.is_valid():
                enrollments_to_create[(external_user_key, enrollment.curriculum_uuid)] = enrollment_serializer
                enrollment_serializer.save()
                response_data[external_user_key] = student['status']
            else:
                serializer_is_invalid = enrollment_serializer.errors['status'][0].code == 'invalid_choice'
                if 'status' in enrollment_serializer.errors and serializer_is_invalid:
                    response_data[external_user_key] = CourseEnrollmentResponseStatuses.INVALID_STATUS

        return self._get_created_or_updated_response(request, enrollments_to_create, response_data, status.HTTP_200_OK)

    def _remove_duplicate_entries(self, request, student_data):
        """ Helper method to remove duplicate entries (based on student key) from request data. """
        result = {}
        key_counter = Counter([enrollment.get(REQUEST_STUDENT_KEY) for enrollment in request.data])
        for student_key, count in key_counter.items():
            if count > 1:
                result[student_key] = CourseEnrollmentResponseStatuses.DUPLICATED
                student_data.pop(student_key)
        return result

    def _request_data_by_student_key(self, request, program_uuid):
        """
        Helper method that returns an OrderedDict of rows from request.data,
        keyed by the `external_user_key`.
        """
        return OrderedDict((
            row.get(REQUEST_STUDENT_KEY),
            {
                'program_uuid': program_uuid,
                'curriculum_uuid': row.get('curriculum_uuid'),
                'status': row.get('status'),
                'external_user_key': row.get(REQUEST_STUDENT_KEY),
            })
            for row in request.data
        )

    def _remove_existing_entries(self, program_uuid, student_data):
        """ Helper method to remove entries that have existing ProgramEnrollment records. """
        result = {}
        existing_enrollments = ProgramEnrollment.bulk_read_by_student_key(program_uuid, student_data)
        for enrollment in existing_enrollments:
            result[enrollment.external_user_key] = CourseEnrollmentResponseStatuses.CONFLICT
            student_data.pop(enrollment.external_user_key)
        return result

    def _get_created_or_updated_response(
            self, request, created_or_updated_data, response_data, default_status=status.HTTP_201_CREATED
    ):
        """
        Helper method to determine an appropirate HTTP response status code.
        """
        response_status = default_status

        if not created_or_updated_data:
            response_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif len(request.data) != len(created_or_updated_data):
            response_status = status.HTTP_207_MULTI_STATUS

        return Response(
            status=response_status,
            data=response_data,
            content_type='application/json',
        )


class LearnerProgramEnrollmentsView(DeveloperErrorViewMixin, APIView):
    """
    A view for checking the currently logged-in learner's program enrollments

    Path: `/api/program_enrollments/v1/programs/enrollments/`

    Returns:
      * 200: OK - Contains a list of all programs in which the learner is enrolled.
      * 401: The requesting user is not authenticated.

    The list will be a list of objects with the following keys:
      * `uuid` - the identifier of the program in which the learner is enrolled.
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

    def get(self, request):
        """
        How to respond to a GET request to this endpoint
        """
        program_enrollments = ProgramEnrollment.objects.filter(
            user=request.user,
            status__in=('enrolled', 'pending')
        )

        uuids = [enrollment.program_uuid for enrollment in program_enrollments]

        catalog_data_of_programs = get_programs(uuids=uuids) or []
        programs_in_which_learner_is_enrolled = [{'uuid': program['uuid'], 'slug': program['marketing_slug']}
                                                 for program
                                                 in catalog_data_of_programs]

        return Response(programs_in_which_learner_is_enrolled, status.HTTP_200_OK)


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

    def check_course_existence_and_membership(self):
        """
        Attempting to look up the course and program will trigger 404 responses if:
        - The program does not exist
        - The course run (course_key) does not exist
        - The course run is not part of the program
        """
        self.course_run  # pylint: disable=pointless-statement

    @property
    def course_run(self):
        """
        The course run specified by the `course_id` URL parameter.
        """
        try:
            CourseOverview.get_from_id(self.course_key)
        except CourseOverview.DoesNotExist:
            raise Http404()
        for course in self.program["courses"]:
            for course_run in course["course_runs"]:
                if self.course_key == CourseKey.from_string(course_run["key"]):
                    return course_run
        raise Http404()

    @property
    def course_key(self):
        """
        The course key for the course run specified by the `course_id` URL parameter.
        """
        return CourseKey.from_string(self.kwargs['course_id'])


# pylint: disable=line-too-long
class ProgramCourseEnrollmentsView(DeveloperErrorViewMixin, ProgramCourseRunSpecificViewMixin, PaginatedAPIView):
    """
    A view for enrolling students in a course through a program,
    modifying program course enrollments, and listing program course
    enrollments.

    Path: ``/api/program_enrollments/v1/programs/{program_uuid}/courses/{course_id}/enrollments/``

    Accepts: [GET, POST]

    For GET requests, the path can contain an optional `page_size?=N` query parameter.
    The default page size is 100.

    ------------------------------------------------------------------------------------
    POST
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
            "previous": "http://testserver.com/api/program_enrollments/v1/programs/{program_uuid}/courses/{course_id}/enrollments/?curor=abcd",
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

    @verify_course_exists
    @verify_program_exists
    def get(self, request, program_uuid=None, course_id=None):
        """ Defines the GET list endpoint for ProgramCourseEnrollment objects. """
        course_key = CourseKey.from_string(course_id)
        enrollments = use_read_replica_if_available(
            ProgramCourseEnrollment.objects.filter(
                program_enrollment__program_uuid=program_uuid, course_key=course_key
            ).select_related(
                'program_enrollment'
            )
        )
        paginated_enrollments = self.paginate_queryset(enrollments)
        serializer = ProgramCourseEnrollmentListSerializer(paginated_enrollments, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, program_uuid=None, course_id=None):
        """
        Enroll a list of students in a course in a program
        """
        return self.create_or_modify_enrollments(
            request,
            program_uuid,
            self.enroll_learner_in_course
        )

    # pylint: disable=unused-argument
    def patch(self, request, program_uuid=None, course_id=None):
        """
        Modify the program course enrollments of a list of learners
        """
        return self.create_or_modify_enrollments(
            request,
            program_uuid,
            self.modify_learner_enrollment_status
        )

    def create_or_modify_enrollments(self, request, program_uuid, operation):
        """
        Process a list of program course enrollment request objects
        and create or modify enrollments based on method
        """
        self.check_course_existence_and_membership()
        results = {}
        seen_student_keys = set()
        enrollments = []

        if not isinstance(request.data, list):
            return Response('invalid enrollment record', status.HTTP_422_UNPROCESSABLE_ENTITY)
        if len(request.data) > MAX_ENROLLMENT_RECORDS:
            return Response(
                'enrollment limit 25', status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        try:
            for enrollment_request in request.data:
                error_status = self.check_enrollment_request(enrollment_request, seen_student_keys)
                if error_status:
                    results[enrollment_request["student_key"]] = error_status
                else:
                    enrollments.append(enrollment_request)
        except KeyError:  # student_key is not in enrollment_request
            return Response('invalid enrollment record', status.HTTP_422_UNPROCESSABLE_ENTITY)
        except TypeError:  # enrollment_request isn't a dict
            return Response('invalid enrollment record', status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValidationError:  # there was some other error raised by the serializer
            return Response('invalid enrollment record', status.HTTP_422_UNPROCESSABLE_ENTITY)

        program_enrollments = self.get_existing_program_enrollments(program_uuid, enrollments)
        for enrollment in enrollments:
            student_key = enrollment["student_key"]
            if student_key in results and results[student_key] == CourseEnrollmentResponseStatuses.DUPLICATED:
                continue
            try:
                program_enrollment = program_enrollments[student_key]
            except KeyError:
                results[student_key] = CourseEnrollmentResponseStatuses.NOT_IN_PROGRAM
            else:
                program_course_enrollment = program_enrollment.get_program_course_enrollment(self.course_key)
                results[student_key] = operation(enrollment, program_enrollment, program_course_enrollment)

        good_count = sum(1 for _, v in results.items() if v not in CourseEnrollmentResponseStatuses.ERROR_STATUSES)
        if not good_count:
            return Response(results, status.HTTP_422_UNPROCESSABLE_ENTITY)
        if good_count != len(results):
            return Response(results, status.HTTP_207_MULTI_STATUS)
        else:
            return Response(results)

    def check_enrollment_request(self, enrollment, seen_student_keys):
        """
        Checks that the given enrollment record is valid and hasn't been duplicated
        """
        student_key = enrollment['student_key']
        if student_key in seen_student_keys:
            return CourseEnrollmentResponseStatuses.DUPLICATED
        seen_student_keys.add(student_key)
        enrollment_serializer = ProgramCourseEnrollmentRequestSerializer(data=enrollment)
        try:
            enrollment_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            if enrollment_serializer.has_invalid_status():
                return CourseEnrollmentResponseStatuses.INVALID_STATUS
            else:
                raise e

    def get_existing_program_enrollments(self, program_uuid, enrollments):
        """
        Parameters:
            - enrollments: A list of enrollment requests
        Returns:
            - Dictionary mapping all student keys in the enrollment requests
              to that user's existing program enrollment in <self.program>
        """
        external_user_keys = [e["student_key"] for e in enrollments]
        existing_enrollments = ProgramEnrollment.objects.filter(
            external_user_key__in=external_user_keys,
            program_uuid=program_uuid,
        )
        existing_enrollments = existing_enrollments.prefetch_related('program_course_enrollments')
        return {enrollment.external_user_key: enrollment for enrollment in existing_enrollments}

    def enroll_learner_in_course(self, enrollment_request, program_enrollment, program_course_enrollment):
        """
        Attempts to enroll the specified user into the course as a part of the
         given program enrollment with the given status

        Returns the actual status
        """
        if program_course_enrollment:
            return CourseEnrollmentResponseStatuses.CONFLICT
        return ProgramCourseEnrollment.enroll(
            program_enrollment,
            self.course_key,
            enrollment_request['status']
        )

    # pylint: disable=unused-argument
    def modify_learner_enrollment_status(self, enrollment_request, program_enrollment, program_course_enrollment):
        """
        Attempts to modify the specified user's enrollment in the given course
        in the given program
        """
        if program_course_enrollment is None:
            return CourseEnrollmentResponseStatuses.NOT_FOUND
        return program_course_enrollment.change_status(enrollment_request['status'])


class ProgramCourseEnrollmentOverviewView(DeveloperErrorViewMixin, ProgramSpecificViewMixin, APIView):
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
            * resume_course_run_url: the url that takes the user back to their position in the course run;
                if absent, user has not made progress in the course
            * course_run_url: the url for the course run
            * start_date: the start date for the course run; null if no start date
            * end_date: the end date for the course run' null if no end date
            * course_status: the status of the course; one of "in-progress", "upcoming", and "completed"
            * emails_enabled: boolean representing whether emails are enabled for the course;
                if absent, the bulk email feature is either not enable at the platform level or is not enabled for the course;
                if True or False, bulk email feature is enabled, and value represents whether or not user wants to receive emails
            * due_dates: a list of subsection due dates for the course run:
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
                    "course_status": "completed"
                    "emails_enabled": true,
                    "due_dates": [
                        {
                            "name": "Introduction: What even is an aardvark?",
                            "url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Aardvarks/jump_to/block-v1:edX+AnimalsX+Aardvarks+type@chapter+block@1414ffd5143b4b508f739b563ab468b7",
                            "date": "2017-05-01T05:00:00Z"
                        },
                        {
                            "name": "Quiz: Aardvark or Anteater?",
                            "url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Aardvarks/jump_to/block-v1:edX+AnimalsX+Aardvarks+type@sequential+block@edx_introduction",
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
                    "course_status": "in-progress"
                    "emails_enabled": false,
                    "due_dates": [],
                    "micromasters_title": "Animals",
                    "certificate_download_url": "https://courses.edx.org/certificates/123",
                    "resume_course_run_url": "https://courses.edx.org/courses/course-v1:edX+AnimalsX+Baboons/jump_to/block-v1:edX+AnimalsX+Baboons+type@sequential+block@edx_introduction"
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

        user_program_enrollment = ProgramEnrollment.objects.filter(
            program_uuid=program_uuid,
            user=user,
            status='enrolled',
        ).order_by(
            '-modified',
        )

        user_program_enrollment_count = user_program_enrollment.count()

        if user_program_enrollment_count > 1:
            # in the unusual and unlikely case of a user having two
            # active program enrollments for the same program,
            # choose the most recently modified enrollment and log
            # a warning
            user_program_enrollment = user_program_enrollment[0]
            logger.warning(
                ('User with user_id {} has more than program enrollment'
                 'with an enrolled status for program uuid {}.').format(
                    user.id,
                    program_uuid,
                )
            )
        elif user_program_enrollment_count == 0:
            # if the user is not enrolled in the program, they are not authorized
            # to view the information returned by this endpoint
            raise PermissionDenied

        user_program_course_enrollments = ProgramCourseEnrollment.objects.filter(
            program_enrollment=user_program_enrollment
        ).select_related('course_enrollment')

        enrollment_dict = {enrollment.course_key: enrollment.course_enrollment for enrollment in user_program_course_enrollments}

        overviews = CourseOverview.get_from_ids_if_exists(enrollment_dict.keys())

        resume_course_run_urls = get_resume_urls_for_enrollments(user, enrollment_dict.values())

        response = {
            'course_runs': [],
        }

        for enrollment in user_program_course_enrollments:
            overview = overviews[enrollment.course_key]

            certificate_download_url = None
            is_certificate_passing = None
            certificate_creation_date = None
            certificate_info = get_certificate_for_user(user.username, enrollment.course_key)

            if certificate_info:
                certificate_download_url = certificate_info['download_url']
                is_certificate_passing = certificate_info['is_passing']
                certificate_creation_date = certificate_info['created']

            course_run_dict = {
                'course_run_id': enrollment.course_key,
                'display_name': overview.display_name_with_default,
                'course_run_status': self.get_course_run_status(overview, is_certificate_passing, certificate_creation_date),
                'course_run_url': self.get_course_run_url(request, enrollment.course_key),
                'start_date': overview.start,
                'end_date': overview.end,
                'due_dates': self.get_due_dates(request, enrollment.course_key, user),
            }

            if certificate_download_url:
                course_run_dict['certificate_download_url'] = certificate_download_url

            emails_enabled = self.get_emails_enabled(user, enrollment.course_key)
            if emails_enabled is not None:
                course_run_dict['emails_enabled'] = emails_enabled

            micromasters_title = self.program['title'] if self.program['type'] == 'MicroMasters' else None
            if micromasters_title:
                course_run_dict['micromasters_title'] = micromasters_title

            # if the url is '', then the url is None so we can omit it from the response
            resume_course_run_url = resume_course_run_urls[enrollment.course_key]
            if resume_course_run_url:
                course_run_dict['resume_course_run_url'] = resume_course_run_url

            response['course_runs'].append(course_run_dict)

        serializer = CourseRunOverviewListSerializer(response)
        return Response(serializer.data)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
        else:
            return None

    @staticmethod
    def get_course_run_status(course_overview, is_certificate_passing, certificate_creation_date):
        """
        Get the progress status of a course run.

        Arguments:
            course_overview (CourseOverview): the overview for the course run
            is_certificate_passing (bool): True if the user has a passing certificate in
                this course run; False otherwise
            certificate_creation_date: the date the certificate was created

        Returns:
            status: one of CourseRunProgressStatuses.COMPLETE,
                CourseRunProgressStatuses.IN_PROGRESS,
                or CourseRunProgressStatuses.UPCOMING
        """
        if course_overview.pacing == 'instructor':
            if course_overview.has_ended():
                return CourseRunProgressStatuses.COMPLETED
            elif course_overview.has_started():
                return CourseRunProgressStatuses.IN_PROGRESS
            else:
                return CourseRunProgressStatuses.UPCOMING
        elif course_overview.pacing == 'self':
            has_ended = course_overview.has_ended()
            thirty_days_ago = datetime.now(UTC) - timedelta(30)
            # a self paced course run is completed when either the course run has ended
            # OR the user has earned a certificate 30 days ago or more
            if has_ended or is_certificate_passing and (certificate_creation_date and certificate_creation_date <= thirty_days_ago):
                return CourseRunProgressStatuses.COMPLETED
            elif course_overview.has_started():
                return CourseRunProgressStatuses.IN_PROGRESS
            else:
                return CourseRunProgressStatuses.UPCOMING
        return None
