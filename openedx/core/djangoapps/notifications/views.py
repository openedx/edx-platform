"""
Views for the notifications API.
"""
from rest_framework import generics, permissions

from common.djangoapps.student.models import CourseEnrollment

from .serializers import NotificationCourseEnrollmentSerializer


class CourseEnrollmentListView(generics.ListAPIView):
    """
    API endpoint to get active CourseEnrollments for requester.

    **Permissions**: User must be authenticated.

    **Response Format**:
        [
            {
                "course": {
                    "id": (int) course_id,
                    "display_name": (str) course_display_name
                },
                "is_active": (bool) is_enrollment_active,
                "mode": (str) enrollment_mode
            },
            ...
        ]
    **Response Error Codes**:
            - 403: The requester cannot access resource.
    """
    serializer_class = NotificationCourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return CourseEnrollment.objects.filter(user=user, is_active=True)
