import re

from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from enrollment import api
from enrollment.errors import (
    CourseEnrollmentError,
    CourseModeNotFoundError,
    CourseEnrollmentExistsError
)
from student.auth import user_has_role
from student.roles import CourseStaffRole, GlobalStaff
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey

from enrollment.views import EnrollmentListView


class AppsemblerEnrollmentListView(EnrollmentListView):

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """Gets a list of all course enrollments for a user.

        Returns a list for the currently logged in user, or for the user named by the 'user' GET
        parameter. If the username does not match that of the currently logged in user, only
        courses for which the currently logged in user has the Staff or Admin role are listed.
        As a result, a course team member can find out which of his or her own courses a particular
        learner is enrolled in.

        Only the Staff or Admin role (granted on the Django administrative console as the staff
        or instructor permission) in individual courses gives the requesting user access to
        enrollment data. Permissions granted at the organizational level do not give a user
        access to enrollment data for all of that organization's courses.

        Users who have the global staff permission can access all enrollment data for all
        courses.

        Appsembler specific changes: We're inheriting the View and the GET method
        to tweak the JSON response and override the course org, in the course key, if the
        advanced setting is_microsoft_course is True.
        """
        username = request.GET.get('user', request.user.username)
        try:
            enrollment_data = api.get_enrollments(username)
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving enrollments for user '{username}'"
                    ).format(username=username)
                }
            )
        if username == request.user.username or GlobalStaff().has_user(
                request.user) or \
                self.has_api_key_permissions(request):
            for enrollment in enrollment_data:
                course_id = CourseKey.from_string(
                    enrollment['course_details']['course_id'])
                course_obj = modulestore().get_course(course_id, depth=0)
                if course_obj.is_microsoft_course:
                    enrollment['course_details']['course_id'] = re.sub('\:.*?\+', ':Microsoft+', enrollment['course_details']['course_id'])
            return Response(enrollment_data)
        filtered_data = []
        for enrollment in enrollment_data:
            course_key = CourseKey.from_string(
                enrollment["course_details"]["course_id"])
            if user_has_role(request.user, CourseStaffRole(course_key)):
                enrollment['course_details']['course_id'] = re.sub('\:.*?\+', ':Microsoft+', enrollment['course_details']['course_id'])
                filtered_data.append(enrollment)
        return Response(filtered_data)
