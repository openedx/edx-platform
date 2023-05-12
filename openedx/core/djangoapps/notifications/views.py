"""
Views for the notifications API.
"""
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.models import NotificationPreference

from .serializers import NotificationCourseEnrollmentSerializer, UserNotificationPreferenceSerializer

User = get_user_model()
from .models import Notification
from .serializers import NotificationCourseEnrollmentSerializer, NotificationSerializer


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


class UserNotificationPreferenceView(APIView):
    """
    Supports retrieving and patching the UserNotificationPreference
    model.

    **Example Requests**
        GET /api/notifications/configurations/{course_id}
        PATCH /api/notifications/configurations/{course_id}

    **Example Response**:
    {
        'id': 1,
        'course_name': 'testcourse',
        'course_id': 'course-v1:testorg+testcourse+testrun',
        'notification_preference_config': {
            'discussion': {
                'new_post': {
                    'web': False,
                    'push': False,
                    'email': False,
                }
            }
        }
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_key_string):
        """
        Returns notification preference for user for a course.

         Parameters:
             request (Request): The request object.
             course_key_string (int): The ID of the course to retrieve notification preference.

         Returns:
             {
                'id': 1,
                'course_name': 'testcourse',
                'course_id': 'course-v1:testorg+testcourse+testrun',
                'notification_preference_config': {
                    'discussion': {
                        'new_post': {
                            'web': False,
                            'push': False,
                            'email': False,
                        }
                    }
                }
            }
         """
        course_id = CourseKey.from_string(course_key_string)
        user_notification_preference, _ = NotificationPreference.objects.get_or_create(
            user=request.user,
            course_id=course_id,
            is_active=True,
        )
        serializer = UserNotificationPreferenceSerializer(user_notification_preference)
        return Response(serializer.data)

    def patch(self, request, course_key_string):
        """
        Update an existing user notification preference with the data in the request body.

        Parameters:
            request (Request): The request object
            course_key_string (int): The ID of the course of the notification preference to be updated.

        Returns:
            200: The updated preference, serialized using the UserNotificationPreferenceSerializer
            404: If the preference does not exist
            403: If the user does not have permission to update the preference
            400: Validation error
        """
        course_id = CourseKey.from_string(course_key_string)
        user_notification_preference = NotificationPreference.objects.get(
            user=request.user,
            course_id=course_id,
            is_active=True,
        )
        serializer = UserNotificationPreferenceSerializer(user_notification_preference, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationListAPIView(generics.ListAPIView):
    """
    API view for listing notifications for a user.

    **Permissions**: User must be authenticated.
    **Response Format** (paginated):

        {
            "results" : [
                {
                    "id": (int) notification_id,
                    "app_name": (str) app_name,
                    "notification_type": (str) notification_type,
                    "content": (str) content,
                    "content_context": (dict) content_context,
                    "content_url": (str) content_url,
                    "last_read": (datetime) last_read,
                    "last_seen": (datetime) last_seen
                },
                ...
            ],
            "count": (int) total_number_of_notifications,
            "next": (str) url_to_next_page_of_notifications,
            "previous": (str) url_to_previous_page_of_notifications,
            "page_size": (int) number_of_notifications_per_page,

        }

    Response Error Codes:
        - 403: The requester cannot access resource.
    """

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Override the get_queryset method to filter the queryset by app name and request.user.
        """
        queryset = super().get_queryset()
        app_name = self.request.query_params.get('app_name')
        if app_name:
            queryset = queryset.filter(app_name=app_name, user=self.request.user)
        return queryset
