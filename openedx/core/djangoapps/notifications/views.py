"""
Views for the notifications API.
"""
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Count
from opaque_keys.edx.keys import CourseKey
from rest_framework import generics, permissions, status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.models import NotificationPreference

from .models import Notification
from .serializers import (
    NotificationCourseEnrollmentSerializer,
    NotificationSerializer,
    UserNotificationPreferenceSerializer
)

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

    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Override the get_queryset method to filter the queryset by app name and request.user.
        """
        app_name = self.request.query_params.get('app_name')
        if app_name:
            return Notification.objects.filter(user=self.request.user, app_name=app_name)
        else:
            return Notification.objects.filter(user=self.request.user)


class NotificationCountView(APIView):
    """
    API view for getting the unseen notifications count for a user.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get the unseen notifications count for a user.

        **Permissions**: User must be authenticated.
        **Response Format**:
        ```json
        {
            "count": (int) total_number_of_unseen_notifications,
            "count_by_app_name": {
                (str) app_name: (int) number_of_unseen_notifications,
                ...
            }
        }
        ```
        **Response Error Codes**:
        - 403: The requester cannot access resource.
        """
        # Get the unseen notifications count for each app name.
        count_by_app_name = (
            Notification.objects
            .filter(user_id=request.user, last_seen__isnull=True)
            .values('app_name')
            .annotate(count=Count('*'))
        )
        count_total = 0
        count_by_app_name_dict = {}

        for item in count_by_app_name:
            app_name = item['app_name']
            count = item['count']

            count_total += count
            count_by_app_name_dict[app_name] = count
        # Return the unseen notifications count for the user and the unseen notifications count for each app name.

        return Response({
            "count": count_total,
            "count_by_app_name": count_by_app_name_dict,
        })


class MarkNotificationsUnseenAPIView(UpdateAPIView):
    """
    API view for marking user's all notifications unseen for a provided app_name.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        """
        Marks all notifications for the given app name unseen for the authenticated user.

        **Args:**
            app_name: The name of the app to mark notifications unseen for.
        **Response Format:**
            A `Response` object with a 200 OK status code if the notifications were successfully marked unseen.
        **Response Error Codes**:
        - 400: Bad Request status code if the app name is invalid.
        """
        app_name = self.kwargs.get('app_name')

        if not app_name:
            return Response({'message': 'Invalid app name.'}, status=400)

        notifications = Notification.objects.filter(
            user=request.user,
            app_name=app_name,
            last_seen__isnull=True,
        )

        notifications.update(last_seen=datetime.now())

        return Response({'message': 'Notifications marked unseen.'}, status=200)
