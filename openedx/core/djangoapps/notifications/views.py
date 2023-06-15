"""
Views for the notifications API.
"""
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Count
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import generics, permissions, status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    get_course_notification_preference_config_version
)

from .base_notification import COURSE_NOTIFICATION_APPS
from .config.waffle import ENABLE_NOTIFICATIONS, SHOW_NOTIFICATIONS_TRAY
from .models import Notification
from .serializers import (
    NotificationCourseEnrollmentSerializer,
    NotificationSerializer,
    UserCourseNotificationPreferenceSerializer,
    UserNotificationPreferenceUpdateSerializer
)


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

    def list(self, request, *args, **kwargs):
        """
        Returns the list of active course enrollments for which ENABLE_NOTIFICATIONS
        Waffle flag is enabled
        """
        enrollment_queryset = self.get_queryset().select_related('course')
        enrollments = [
            enrollment
            for enrollment in enrollment_queryset
            if ENABLE_NOTIFICATIONS.is_enabled(enrollment.course.id)
        ]
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)


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
                'enabled': False,
                'core': {
                    'info': '',
                    'web': False,
                    'push': False,
                    'email': False,
                },
                'notification_types': {
                    'new_post': {
                        'info': '',
                        'web': False,
                        'push': False,
                        'email': False,
                    },
                },
                'not_editable': {},
            },
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
                        'enabled': False,
                        'core': {
                            'info': '',
                            'web': False,
                            'push': False,
                            'email': False,
                        },
                        'notification_types': {
                            'new_post': {
                                'info': '',
                                'web': False,
                                'push': False,
                                'email': False,
                            },
                        },
                        'not_editable': {},
                    },
                }
            }
         """
        course_id = CourseKey.from_string(course_key_string)
        user_notification_preference, _ = CourseNotificationPreference.objects.get_or_create(
            user=request.user,
            course_id=course_id,
            is_active=True,
        )
        serializer = UserCourseNotificationPreferenceSerializer(user_notification_preference)
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
        user_course_notification_preference = CourseNotificationPreference.objects.get(
            user=request.user,
            course_id=course_id,
            is_active=True,
        )
        if user_course_notification_preference.config_version != get_course_notification_preference_config_version():
            return Response(
                {'error': 'The notification preference config version is not up to date.'},
                status=status.HTTP_409_CONFLICT,
            )

        preference_update_serializer = UserNotificationPreferenceUpdateSerializer(
            user_course_notification_preference, data=request.data, partial=True
        )
        preference_update_serializer.is_valid(raise_exception=True)
        updated_notification_preferences = preference_update_serializer.save()
        serializer = UserCourseNotificationPreferenceSerializer(updated_notification_preferences)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        Override the get_queryset method to filter the queryset by app name, request.user and created
        """
        expiry_date = datetime.now(UTC) - timedelta(days=settings.NOTIFICATIONS_EXPIRY)
        app_name = self.request.query_params.get('app_name')

        if app_name:
            return Notification.objects.filter(
                user=self.request.user,
                app_name=app_name,
                created__gte=expiry_date,
            ).order_by('-id')
        else:
            return Notification.objects.filter(
                user=self.request.user,
                created__gte=expiry_date,
            ).order_by('-id')


class NotificationCountView(APIView):
    """
    API view for getting the unseen notifications count and show_notification_tray flag for a user.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get the unseen notifications count and show_notification_tray flag for a user.

        **Permissions**: User must be authenticated.
        **Response Format**:
        ```json
        {
            "show_notifications_tray": (bool) show_notifications_tray,
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
        show_notifications_tray_enabled = False

        for item in count_by_app_name:
            app_name = item['app_name']
            count = item['count']
            count_total += count
            count_by_app_name_dict[app_name] = count

        learner_enrollments_course_ids = CourseEnrollment.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('course_id', flat=True)

        for course_id in learner_enrollments_course_ids:
            if SHOW_NOTIFICATIONS_TRAY.is_enabled(course_id):
                show_notifications_tray_enabled = True
                break

        return Response({
            "show_notifications_tray": show_notifications_tray_enabled,
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


class NotificationReadAPIView(APIView):
    """
    API view for marking user notifications as read, either all notifications or a single notification
    """

    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        """
        Marks all notifications or single notification read for the given
        app name or notification id for the authenticated user.

        Requests:
        PATCH /api/notifications/read/

        Parameters:
            request (Request): The request object containing the app name or notification id.
                {
                    "app_name": (str) app_name,
                    "notification_id": (int) notification_id
                }

        Returns:
        - 200: OK status code if the notification or notifications were successfully marked read.
        - 400: Bad Request status code if the app name or notification id is invalid.
        - 403: Forbidden status code if the user is not authenticated.
        - 404: Not Found status code if the notification or notifications were not found.
        """
        app_name = request.data.get('app_name')
        notification_id = request.data.get('notification_id')

        if not app_name and not notification_id:
            return Response({'message': 'Invalid app name or notification id.'}, status=status.HTTP_400_BAD_REQUEST)

        if app_name and app_name not in COURSE_NOTIFICATION_APPS:
            return Response({'message': 'Invalid app name.'}, status=status.HTTP_400_BAD_REQUEST)

        query_params = {
            'user': request.user,
            'last_read__isnull': True,
        }

        if app_name:
            query_params['app_name'] = app_name

        if notification_id:
            query_params['id'] = notification_id

        notifications = Notification.objects.filter(**query_params)

        if notification_id and not notifications.exists():
            return Response({'message': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        notifications.update(last_read=datetime.now())

        return Response({'message': 'Notifications marked read.'}, status=status.HTTP_200_OK)
