# -*- coding: utf-8 -*-
"""
ProgramEnrollment Views
"""
from __future__ import absolute_import, unicode_literals

import logging
from datetime import datetime, timedelta
from pytz import UTC

from django.core.exceptions import PermissionDenied
from django.urls import reverse
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
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
    ProgramEnrollmentResponseStatuses,
)
from lms.djangoapps.program_enrollments.api.v1.serializers import (
    CourseRunOverviewListSerializer,
    ProgramCourseEnrollmentListSerializer,
    ProgramCourseEnrollmentRequestSerializer,
    ProgramEnrollmentCreateRequestSerializer,
    ProgramEnrollmentListSerializer,
    ProgramEnrollmentModifyRequestSerializer,
)
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from lms.djangoapps.program_enrollments.utils import get_user_by_program_id, ProviderDoesNotExistException
from student.helpers import get_resume_urls_for_enrollments
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, PaginatedAPIView, verify_course_exists
from util.query import use_read_replica_if_available

from .utils import (
    ProgramCourseRunSpecificViewMixin,
    ProgramEnrollmentPagination,
    ProgramSpecificViewMixin,
    verify_course_exists_and_in_program,
    verify_program_exists,
)

logger = logging.getLogger(__name__)


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
                'status': A choice of the following statuses: ['enrolled', 'pending', 'canceled', 'suspended'],
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
            * failure statuses:
                * 'duplicated' - the request body listed the same learner twice
                * 'conflict' - there is an existing enrollment for that learner, curriculum and program combo
                * 'invalid-status' - a status other than 'enrolled', 'pending', 'canceled', 'suspended' was entered
      * 201: CREATED - All students were successfully enrolled.
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
                'status': A choice of the following statuses: ['enrolled', 'pending', 'canceled', 'suspended'],
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
            * failure statuses:
                * 'duplicated' - the request body listed the same learner twice
                * 'conflict' - there is an existing enrollment for that learner, curriculum and program combo
                * 'invalid-status' - a status other than 'enrolled', 'pending', 'canceled', 'suspended' was entered
                * 'not-in-program' - the user is not in the program and cannot be updated
      * 201: CREATED - All students were successfully enrolled.
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
        return self.create_or_modify_enrollments(
            request,
            kwargs['program_uuid'],
            ProgramEnrollmentCreateRequestSerializer,
            self.create_program_enrollment,
            status.HTTP_201_CREATED,
        )

    @verify_program_exists
    def patch(self, request, **kwargs):
        """
        Modify program enrollments for a list of learners
        """
        return self.create_or_modify_enrollments(
            request,
            kwargs['program_uuid'],
            ProgramEnrollmentModifyRequestSerializer,
            self.modify_program_enrollment,
            status.HTTP_200_OK,
        )

    @verify_program_exists
    def put(self, request, **kwargs):
        """
        Create/modify program enrollments for a list of learners
        """
        return self.create_or_modify_enrollments(
            request,
            kwargs['program_uuid'],
            ProgramEnrollmentCreateRequestSerializer,
            self.create_or_modify_program_enrollment,
            status.HTTP_200_OK,
        )

    def validate_enrollment_request(self, enrollment, seen_student_keys, serializer_class):
        """
        Validates the given enrollment record and checks that it isn't a duplicate
        """
        student_key = enrollment['student_key']
        if student_key in seen_student_keys:
            return CourseEnrollmentResponseStatuses.DUPLICATED
        seen_student_keys.add(student_key)
        enrollment_serializer = serializer_class(data=enrollment)
        try:
            enrollment_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            if enrollment_serializer.has_invalid_status():
                return CourseEnrollmentResponseStatuses.INVALID_STATUS
            else:
                raise e

    def create_or_modify_enrollments(self, request, program_uuid, serializer_class, operation, success_status):
        """
        Process a list of program course enrollment request objects
        and create or modify enrollments based on method
        """
        results = {}
        seen_student_keys = set()
        enrollments = []

        if not isinstance(request.data, list):
            return Response('invalid enrollment record', status.HTTP_422_UNPROCESSABLE_ENTITY)
        if len(request.data) > MAX_ENROLLMENT_RECORDS:
            return Response(
                'enrollment limit {}'.format(MAX_ENROLLMENT_RECORDS),
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        try:
            for enrollment_request in request.data:
                error_status = self.validate_enrollment_request(enrollment_request, seen_student_keys, serializer_class)
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
            if student_key in results and results[student_key] == ProgramEnrollmentResponseStatuses.DUPLICATED:
                continue
            try:
                program_enrollment = program_enrollments[student_key]
            except KeyError:
                program_enrollment = None
            results[student_key] = operation(enrollment, program_uuid, program_enrollment)

        return self._get_created_or_updated_response(results, success_status)

    def create_program_enrollment(self, request_data, program_uuid, program_enrollment):
        """
        Create new ProgramEnrollment, unless the learner is already enrolled in the program
        """
        if program_enrollment:
            return ProgramEnrollmentResponseStatuses.CONFLICT

        student_key = request_data.get('student_key')
        try:
            user = get_user_by_program_id(student_key, program_uuid)
        except ProviderDoesNotExistException:
            # IDP has not yet been set up, just create waiting enrollments
            user = None

        enrollment = ProgramEnrollment.objects.create(
            user=user,
            external_user_key=student_key,
            program_uuid=program_uuid,
            curriculum_uuid=request_data.get('curriculum_uuid'),
            status=request_data.get('status')
        )
        return enrollment.status

    # pylint: disable=unused-argument
    def modify_program_enrollment(self, request_data, program_uuid, program_enrollment):
        """
        Change the status of an existing program enrollment
        """
        if not program_enrollment:
            return ProgramEnrollmentResponseStatuses.NOT_IN_PROGRAM

        program_enrollment.status = request_data.get('status')
        program_enrollment.save()
        return program_enrollment.status

    def create_or_modify_program_enrollment(self, request_data, program_uuid, program_enrollment):
        if program_enrollment:
            return self.modify_program_enrollment(request_data, program_uuid, program_enrollment)
        else:
            return self.create_program_enrollment(request_data, program_uuid, program_enrollment)

    def get_existing_program_enrollments(self, program_uuid, student_data):
        """ Returns the existing program enrollments for the given students and program """
        student_keys = [data['student_key'] for data in student_data]
        return {
            e.external_user_key: e
            for e in ProgramEnrollment.bulk_read_by_student_key(program_uuid, student_keys)
        }

    def _get_created_or_updated_response(self, response_data, default_status=status.HTTP_201_CREATED):
        """
        Helper method to determine an appropirate HTTP response status code.
        """
        response_status = default_status
        good_count = len([
            v for v in response_data.values()
            if v not in CourseEnrollmentResponseStatuses.ERROR_STATUSES
        ])
        if not good_count:
            response_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif good_count != len(response_data):
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


# pylint: disable=line-too-long
class ProgramCourseEnrollmentsView(DeveloperErrorViewMixin, ProgramCourseRunSpecificViewMixin, PaginatedAPIView):
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

    @verify_program_exists
    @verify_course_exists_and_in_program
    def post(self, request, program_uuid=None, course_id=None):
        """
        Enroll a list of students in a course in a program
        """
        return self.create_or_modify_enrollments(
            request,
            program_uuid,
            self.enroll_learner_in_course
        )

    @verify_program_exists
    @verify_course_exists_and_in_program
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

    @verify_program_exists
    @verify_course_exists_and_in_program
    # pylint: disable=unused-argument
    def put(self, request, program_uuid=None, course_id=None):
        """
        Create or Update the program course enrollments of a list of learners
        """
        return self.create_or_modify_enrollments(
            request,
            program_uuid,
            self.create_or_update_learner_enrollment
        )

    def create_or_modify_enrollments(self, request, program_uuid, operation):
        """
        Process a list of program course enrollment request objects
        and create or modify enrollments based on method
        """
        results = {}
        seen_student_keys = set()
        enrollments = []

        if not isinstance(request.data, list):
            return Response('invalid enrollment record', status.HTTP_400_BAD_REQUEST)
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
            return Response('invalid enrollment record', status.HTTP_400_BAD_REQUEST)
        except TypeError:  # enrollment_request isn't a dict
            return Response('invalid enrollment record', status.HTTP_400_BAD_REQUEST)
        except ValidationError:  # there was some other error raised by the serializer
            return Response('invalid enrollment record', status.HTTP_400_BAD_REQUEST)

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

        return ProgramCourseEnrollment.create_program_course_enrollment(
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

    def create_or_update_learner_enrollment(self, enrollment_request, program_enrollment, program_course_enrollment):
        """
        Attempts to create or update the specified user's enrollment in the given course
        in the given program
        """
        if program_course_enrollment is None:
            # create the course enrollment
            return ProgramCourseEnrollment.create_program_course_enrollment(
                program_enrollment,
                self.course_key,
                enrollment_request['status']
            )
        else:
            # Update course enrollment
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
