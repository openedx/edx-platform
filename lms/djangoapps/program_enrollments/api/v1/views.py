# -*- coding: utf-8 -*-
"""
ProgramEnrollment Views
"""
from __future__ import unicode_literals
from django.http import Http404
from django.http import HttpResponse
from course_modes.models import CourseMode
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_207_MULTI_STATUS,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from lms.djangoapps.program_enrollments.api.v1.constants import CourseEnrollmentResponseStatuses
from lms.djangoapps.program_enrollments.models import ProgramEnrollment, ProgramCourseEnrollment
from lms.djangoapps.program_enrollments.serializers import ProgramCourseEnrollmentRequestSerializer


class ProgramEnrollmentsView(APIView):
    """
    POST view for ProgramEnrollments
    """

    def get(self, request, *args, **kwargs):
        return HttpResponse('result')


class ProgramSpecificViewMixin(object):
    """
    A mixin for views that operate on or within a specific program.
    """
    def __init__(self, *args, **kwargs):
        super(ProgramSpecificViewMixin, self).__init__(*args, **kwargs)
        self._program = None

    @property
    def program(self):
        """
        The program specified by the `program_uuid` URL parameter.
        """
        if self._program is None:
            program = get_programs(uuid=self.kwargs['program_uuid'])
            if program is None:
                raise Http404()
            self._program = program
        return self._program


class ProgramCourseRunSpecificViewMixin(ProgramSpecificViewMixin):
    """
    A mixin for views that operate on or within a specific course run in a program
    """
    def __init__(self, *args, **kwargs):
        super(ProgramCourseRunSpecificViewMixin, self).__init__(*args, **kwargs)
        self._course_run = None
        self._course_key = None

    def check_existence_and_membership(self):
        """
        Attempting to look up the course and program will trigger 404 responses if:
        - The program does not exist
        - The course run (course_key) does not exist
        - The course run is not part of the program
        """
        self._parse_run_and_key()

    @property
    def course_run(self):
        """
        The course run specified by the `course_id` URL parameter.
        """
        if self._course_run is None:
            self._parse_run_and_key()
        return self._course_run

    @property
    def course_key(self):
        """
        The course key for the course run specified by the `course_id` URL parameter.
        """
        if self._course_key is None:
            self._parse_run_and_key()
        return self._course_key

    def _parse_run_and_key(self):
        """
        Parse the course_run and course_key fields from the course_id url parameter

        Raises Http404 if the program or course_run does not exist or if the course_run
        is not in the program
        """
        try:
            course_key = CourseKey.from_string(self.kwargs['course_id'])
            course = CourseOverview.get_from_id(course_key)
        except CourseOverview.DoesNotExist:
            raise Http404()
        for course in self.program["courses"]:
            for course_run in course["course_runs"]:
                if course_key == CourseKey.from_string(course_run["key"]):
                    self._course_run = course_run
                    self._course_key = course_key
                    return
        raise Http404()


class ProgramCourseEnrollmentsView(ProgramCourseRunSpecificViewMixin, APIView):
    """
    A view for enrolling students in a course through a program,
    modifying program course enrollments, and listing program course
    enrollments

    Path: /api/v1/programs/{program_uuid}/courses/{course_id}/enrollments

    Accepts: [POST]

    ------------------------------------------------------------------------------------
    POST
    ------------------------------------------------------------------------------------

    Returns:
     * 200: Returns a map of students and their enrollment status.
     * 207: Not all students enrolled. Returns resulting enrollment status.
     * 401: User is not authenticated
     * 403: User lacks read access organization of specified program.
     * 404: Program does not exist, or course does not exist in program
     * 422: Invalid request, unable to enroll students.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        Enroll a list of students in a course in a program
        """
        self.check_existence_and_membership()
        results = {}
        seen_student_keys = set()
        enrollments = []

        if not isinstance(request.data, list):
            raise ValidationError("invalid enrollment record")
        if len(request.data) > 25:
            return Response(
                'enrollment limit 25', HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        try:
            for enrollment_request in request.data:
                error_status = self.check_enrollment_request(enrollment_request, seen_student_keys)
                if error_status:
                    results[enrollment_request["student_key"]] = error_status
                else:
                    enrollments.append(enrollment_request)
        except (KeyError, ValidationError, TypeError):
            return Response('invalid enrollment record', HTTP_422_UNPROCESSABLE_ENTITY)

        program_enrollments = self.get_existing_program_enrollments(enrollments)
        for enrollment in enrollments:
            student_key = enrollment["student_key"]
            if student_key in results and results[student_key] == CourseEnrollmentResponseStatuses.DUPLICATED:
                continue
            results[student_key] = self.enroll_learner_in_course(enrollment, program_enrollments)

        good_count = sum([1 for _, v in results.items() if v not in CourseEnrollmentResponseStatuses.ERROR_STATUSES])
        if not good_count:
            return Response(results, HTTP_422_UNPROCESSABLE_ENTITY)
        if good_count != len(results):
            return Response(results, HTTP_207_MULTI_STATUS)
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

    def get_existing_program_enrollments(self, enrollments):
        """
        Parameters:
            - enrollments: A list of enrollment requests
        Returns:
            - Dictionary mapping all student keys in the enrollment requests
              to that user's existing program enrollment <self.program>
        """
        external_user_keys = [e["student_key"] for e in enrollments]
        existing_enrollments = ProgramEnrollment.objects.filter(
            external_user_key__in=external_user_keys
        )
        existing_enrollments = existing_enrollments.prefetch_related('program_course_enrollments')
        return {enrollment.external_user_key: enrollment for enrollment in existing_enrollments}

    def enroll_learner_in_course(self, enrollment_request, program_enrollments):
        """
        Attempts to enroll the specified user into the course as a part of the
         given program enrollment with the given status

        Returns the actual status
        """
        student_key = enrollment_request['student_key']
        try:
            program_enrollment = program_enrollments[student_key]
        except KeyError:
            return CourseEnrollmentResponseStatuses.NOT_IN_PROGRAM
        if program_enrollment.get_program_course_enrollment(self.course_key):
            return CourseEnrollmentResponseStatuses.CONFLICT

        status = enrollment_request['status']
        course_enrollment = None
        if program_enrollment.user:  # This user has an account, enroll them in the course
            course_enrollment = CourseEnrollment.enroll(
                program_enrollment.user,
                self.course_key,
                mode=CourseMode.MASTERS,
                check_access=True,
            )
            if status == CourseEnrollmentResponseStatuses.INACTIVE:
                course_enrollment.deactivate()

        ProgramCourseEnrollment.objects.create(
            program_enrollment=program_enrollment,
            course_enrollment=course_enrollment,
            course_key=self.course_key,
            status=status,
        )
        return status
