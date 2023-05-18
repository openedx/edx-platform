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
