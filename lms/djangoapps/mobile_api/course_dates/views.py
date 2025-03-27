"""
API views for course dates.
"""

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.shortcuts import get_object_or_404
from rest_framework import views
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_home_api.utils import get_course_or_403
from lms.djangoapps.courseware.courses import get_course_date_blocks
from lms.djangoapps.courseware.date_summary import TodaysDate

from ..decorators import mobile_view
from .serializers import AllCourseDatesSerializer


class AllCourseDatesPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@mobile_view()
class AllCourseDatesAPIView(views.APIView):
    """
    API for retrieving all course dates for a specific user.
    This view provides a list of course dates for a user, including due dates for
    assignments and other course content.
    **Example Request**
        GET /api/mobile/{api_version}/course_dates/<user_name>/
    **Example Response**
        ```json
        {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
            {
                "course_id": "course-v1:1+1+1",
                "assignment_block_id": "block-v1:1+1+1+type@sequential+block@bafd854414124f6db42fee42ca8acc14",
                "due_date": "2030-01-01T00:00:00+0000",
                "assignment_title": "Subsection name",
                "learner_has_access": true,
                "course_name": "Course name",
                "relative": false
            },
            {
                "course_id": "course-v1:1+1+1",
                "assignment_block_id": "block-v1:1+1+1+type@sequential+block@bf9f2d55cf4f49eaa71e7157ea67ba32",
                "due_date": "2030-01-01T00:00:00+0000",
                "assignment_title": "Subsection name",
                "learner_has_access": true,
                "course_name": "Course name",
                "relative": true
            },
        }
        ```
    """

    pagination_class = AllCourseDatesPagination

    def get(self, request, *args, **kwargs) -> Response:
        user = get_object_or_404(User, username=kwargs.get("username"))
        user_enrollments = CourseEnrollment.enrollments_for_user(user).select_related("course")

        all_date_blocks = []

        for enrollment in user_enrollments:
            course = get_course_or_403(
                request.user, "load", enrollment.course_id, check_if_enrolled=False, is_mobile=True
            )
            blocks = get_course_date_blocks(course, user, request, include_access=True, include_past_dates=True)
            all_date_blocks.extend(
                [
                    block
                    for block in blocks
                    if not isinstance(block, TodaysDate) and (block.is_relative or not block.deadline_has_passed())
                ]
            )

        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(all_date_blocks, request)
        serializer = AllCourseDatesSerializer(paginated_data, many=True)
        return paginator.get_paginated_response(serializer.data)
