"""
Views for the download courses API.
"""

from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.shortcuts import get_object_or_404
from rest_framework import views
from rest_framework.response import Response
from urllib.parse import urljoin

from common.djangoapps.student.models import CourseEnrollment, User  # lint-amnesty, pylint: disable=reimported
from lms.djangoapps.courseware.access import is_mobile_available_for_user
from openedx.features.offline_mode.models import OfflineCourseSize

from ..decorators import mobile_view


@mobile_view(is_user=True)
class DownloadCoursesAPIView(views.APIView):
    """
    **Use Case**

        Get information for downloading courses for the user.

        USER_ENROLLMENTS_LIMIT - adds users enrollments query limit to
        safe API from possible DDOS attacks.

    **Example Request**

        GET /api/mobile/{api_version}/download_courses/<user_name>/

     **Response Values**

        The HTTP 200 response has the following values.

        * course_id (str): The course id associated with the user's enrollment.
        * course_name (str): The course name associated with the user's enrollment.
        * course_image (str): Full url to the course image.
        * total_size (int): Total size in bytes of the course offline content.

        The HTTP 200 response contains a list of dictionaries that contain info
        about each user's enrollment.

    **Example Response**

        ```json
        [
            {
                "course_id": "course-v1:a+a+a",
                "course_name": "a",
                "course_image": "/asset-v1:a+a+a+type@asset+block@images_course_image.jpg
                "total_size": 123456
            },
            {
                "course_id": "course-v1:b+b+b",
                "course_name": "b",
                "course_image": "/asset-v1:b+b+b+type@asset+block@images_course_image.jpg
                "total_size": 123456
            },
        ]
        ```
    """

    USER_ENROLLMENTS_LIMIT = 500

    def get(self, request, *args, **kwargs) -> Response:
        user = get_object_or_404(User, username=kwargs.get("username"))
        user_enrollments = CourseEnrollment.enrollments_for_user(user).select_related("course")[
            : self.USER_ENROLLMENTS_LIMIT
        ]
        mobile_available = [
            enrollment
            for enrollment in user_enrollments
            if is_mobile_available_for_user(user, enrollment.course_overview)
        ]
        response_data = []

        for user_enrollment in mobile_available:
            course_id = user_enrollment.course_overview.id
            offline_course_size = OfflineCourseSize.objects.filter(course_id=course_id).first()
            response_data.append(
                {
                    "course_id": str(course_id),
                    "course_name": user_enrollment.course_overview.display_name,
                    "course_image": user_enrollment.course_overview.course_image_url,
                    "total_size": getattr(offline_course_size, "size", 0),
                }
            )

        return Response(response_data)
