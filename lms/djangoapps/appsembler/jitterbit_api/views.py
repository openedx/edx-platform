import logging
from dateutil import parser

from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from openedx.core.djangoapps.user_api.accounts.api import check_account_exists, get_account_settings
from openedx.core.djangoapps.user_api.errors import UserNotFound


from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsStaffOrOwner

from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey


log = logging.getLogger(__name__)

class GetBatchUserDataView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser,
    permission_classes = IsStaffOrOwner,

    def get(self, request):
        """
            /api/jitterbit/v1/accounts/batch[?time-parameter]

            time-parameter is an optional query parameter of: 
                ?updated_min=yyyy-mm-ddThh:mm:ss
                ?updated_max=yyyy-mm-ddThh:mm:ss
                ?updated_min=yyyy-mm-ddThh:mm:ss&updated_max=yyyy-mm-ddThh:mm:ss

        """
        updated_min = request.GET.get('updated_min','')
        updated_max = request.GET.get('updated_max','')

        users = User.objects.all()
        if updated_min:
            min_date = parser.parse(updated_min)
            users = users.filter(date_joined__gt=min_date)

        if updated_max:
            max_date = parser.parse(updated_max)
            users = users.filter(date_joined__lt=max_date)

        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'date_joined': user.date_joined
            }
            user_list.append(user_data)

        return Response(user_list, status=200)

class GetBatchEnrollmentDataView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser,
    permission_classes = IsStaffOrOwner,

    def get(self, request):
        """
        /api/jitterbit/v1/enrollment/batch[?course_id=course_slug&time-parameter]

        course_slug an optional query parameter; if specified will only show enrollments 
            for that particular course. The course_id need to be URL encoded, so:
                course_id=course-v1:edX+DemoX+Demo_Course
            would be encoded as: 
                course_id=course-v1%3AedX%2BDemoX%2BDemo_Course
        time-parameter is an optional query parameter of: 
                ?updated_min=yyyy-mm-ddThh:mm:ss
                ?updated_max=yyyy-mm-ddThh:mm:ss
                ?updated_min=yyyy-mm-ddThh:mm:ss&updated_max=yyyy-mm-ddThh:mm:ss
        """

        updated_min = request.GET.get('updated_min','')
        updated_max = request.GET.get('updated_max','')
        course_id = request.GET.get('course_id')
        print course_id
        # users = User.objects.all()
        enrollments = CourseEnrollment.objects.all()

        if course_id:
            course_key = CourseKey.from_string(course_id)
            enrollments = enrollments.filter(course_id=course_key)

        if updated_min:
            min_date = parser.parse(updated_min)
            enrollments = enrollments.filter(created__gt=min_date)

        if updated_max:
            max_date = parser.parse(updated_max)
            enrollments = enrollments.filter(created__lt=max_date)

        enrollment_list = []
        for enrollment in enrollments:
            enrollment_data = {
                'enrollment_id': enrollment.id,
                'user_id': enrollment.user.id,
                'username': enrollment.user.username,
                'course_id': str(enrollment.course_id),
                'date_enrolled': enrollment.created,
            }
            

            enrollment_list.append(enrollment_data)

        return Response(enrollment_list, status=200)



