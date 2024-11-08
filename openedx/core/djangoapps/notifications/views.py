"""
Views for the notifications API.
"""
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.email.utils import update_user_preferences_from_patch
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    get_course_notification_preference_config_version
)
from openedx.core.djangoapps.notifications.permissions import allow_any_authenticated_user

from .base_notification import COURSE_NOTIFICATION_APPS
from .config.waffle import ENABLE_NOTIFICATIONS
from .events import (
    notification_preference_update_event,
    notification_preferences_viewed_event,
    notification_read_event,
    notification_tray_opened_event,
    notifications_app_all_read_event
)
from .models import Notification
from .serializers import (
    NotificationCourseEnrollmentSerializer,
    NotificationSerializer,
    UserCourseNotificationPreferenceSerializer,
    UserNotificationPreferenceUpdateSerializer,
)
from .utils import get_show_notifications_tray, get_is_new_notification_view_enabled


@allow_any_authenticated_user()
class CourseEnrollmentListView(generics.ListAPIView):
    """
    API endpoint to get active CourseEnrollments for requester.

    **Permissions**: User must be authenticated.
    **Response Format** (paginated):

        {
            "next": (str) url_to_next_page_of_courses,
            "previous": (str) url_to_previous_page_of_courses,
            "count": (int) total_number_of_courses,
            "num_pages": (int) total_number_of_pages,
            "current_page": (int) current_page_number,
            "start": (int) index_of_first_course_on_page,
            "results" : [
                {
                    "course": {
                        "id": (int) course_id,
                        "display_name": (str) course_display_name
                    },
                },
                ...
            ],
        }

    Response Error Codes:
    - 403: The requester cannot access resource.
    """
    serializer_class = NotificationCourseEnrollmentSerializer

    def get_paginated_response(self, data):
        """
        Return a response given serialized page data with show_preferences flag.
        """
        response = super().get_paginated_response(data)
        response.data["show_preferences"] = get_show_notifications_tray(self.request.user)
        return response

    def get_queryset(self):
        user = self.request.user
        return CourseEnrollment.objects.filter(user=user, is_active=True)

    def list(self, request, *args, **kwargs):
        """
        Returns the list of active course enrollments for which ENABLE_NOTIFICATIONS
        Waffle flag is enabled
        """
        queryset = self.filter_queryset(self.get_queryset())
        course_ids = queryset.values_list('course_id', flat=True)

        for course_id in course_ids:
            if not ENABLE_NOTIFICATIONS.is_enabled(course_id):
                queryset = queryset.exclude(course_id=course_id)

        queryset = queryset.select_related('course').order_by('-id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response({
            "show_preferences": get_show_notifications_tray(request.user),
            "results": self.get_serializer(queryset, many=True).data
        })


@allow_any_authenticated_user()
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
        user_preference = CourseNotificationPreference.get_updated_user_course_preferences(request.user, course_id)
        serializer_context = {
            'course_id': course_id,
            'user': request.user
        }
        serializer = UserCourseNotificationPreferenceSerializer(user_preference, context=serializer_context)
        notification_preferences_viewed_event(request, course_id)
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
                {'error': _('The notification preference config version is not up to date.')},
                status=status.HTTP_409_CONFLICT,
            )

        if request.data.get('notification_channel', '') == 'email_cadence':
            request.data['email_cadence'] = request.data['value']
            del request.data['value']

        preference_update = UserNotificationPreferenceUpdateSerializer(
            user_course_notification_preference, data=request.data, partial=True
        )
        preference_update.is_valid(raise_exception=True)
        updated_notification_preferences = preference_update.save()
        notification_preference_update_event(request.user, course_id, preference_update.validated_data)

        serializer_context = {
            'course_id': course_id,
            'user': request.user
        }
        serializer = UserCourseNotificationPreferenceSerializer(updated_notification_preferences,
                                                                context=serializer_context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@allow_any_authenticated_user()
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

    def get_queryset(self):
        """
        Override the get_queryset method to filter the queryset by app name, request.user and created
        """
        expiry_date = datetime.now(UTC) - timedelta(days=settings.NOTIFICATIONS_EXPIRY)
        app_name = self.request.query_params.get('app_name')

        if self.request.query_params.get('tray_opened'):
            unseen_count = Notification.objects.filter(user_id=self.request.user, last_seen__isnull=True).count()
            notification_tray_opened_event(self.request.user, unseen_count)
        params = {
            'user': self.request.user,
            'created__gte': expiry_date,
            'web': True
        }

        if app_name:
            params['app_name'] = app_name
        return Notification.objects.filter(**params).order_by('-created')


@allow_any_authenticated_user()
class NotificationCountView(APIView):
    """
    API view for getting the unseen notifications count and show_notification_tray flag for a user.
    """

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
            },
            "notification_expiry_days": 60
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
        show_notifications_tray = get_show_notifications_tray(self.request.user)
        is_new_notification_view_enabled = get_is_new_notification_view_enabled()
        count_by_app_name_dict = {
            app_name: 0
            for app_name in COURSE_NOTIFICATION_APPS
        }

        for item in count_by_app_name:
            app_name = item['app_name']
            count = item['count']
            count_total += count
            count_by_app_name_dict[app_name] = count

        return Response({
            "show_notifications_tray": show_notifications_tray,
            "count": count_total,
            "count_by_app_name": count_by_app_name_dict,
            "notification_expiry_days": settings.NOTIFICATIONS_EXPIRY,
            "is_new_notification_view_enabled": is_new_notification_view_enabled
        })


@allow_any_authenticated_user()
class MarkNotificationsSeenAPIView(UpdateAPIView):
    """
    API view for marking user's all notifications seen for a provided app_name.
    """

    def update(self, request, *args, **kwargs):
        """
        Marks all notifications for the given app name seen for the authenticated user.

        **Args:**
            app_name: The name of the app to mark notifications seen for.
        **Response Format:**
            A `Response` object with a 200 OK status code if the notifications were successfully marked seen.
        **Response Error Codes**:
        - 400: Bad Request status code if the app name is invalid.
        """
        app_name = self.kwargs.get('app_name')

        if not app_name:
            return Response({'error': _('Invalid app name.')}, status=400)

        notifications = Notification.objects.filter(
            user=request.user,
            app_name=app_name,
            last_seen__isnull=True,
        )

        notifications.update(last_seen=datetime.now())

        return Response({'message': _('Notifications marked as seen.')}, status=200)


@allow_any_authenticated_user()
class NotificationReadAPIView(APIView):
    """
    API view for marking user notifications as read, either all notifications or a single notification
    """

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
        - 400: Bad Request status code if the app name is invalid.
        - 403: Forbidden status code if the user is not authenticated.
        - 404: Not Found status code if the notification was not found.
        """
        notification_id = request.data.get('notification_id', None)
        read_at = datetime.now(UTC)

        if notification_id:
            notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
            first_time_read = notification.last_read is None
            notification.last_read = read_at
            notification.save()
            notification_read_event(request.user, notification, first_time_read)
            return Response({'message': _('Notification marked read.')}, status=status.HTTP_200_OK)

        app_name = request.data.get('app_name', '')

        if app_name in COURSE_NOTIFICATION_APPS:
            notifications = Notification.objects.filter(
                user=request.user,
                app_name=app_name,
                last_read__isnull=True,
            )
            notifications.update(last_read=read_at)
            notifications_app_all_read_event(request.user, app_name)
            return Response({'message': _('Notifications marked read.')}, status=status.HTTP_200_OK)

        return Response({'error': _('Invalid app_name or notification_id.')}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def preference_update_from_encrypted_username_view(request, username, patch):
    """
    View to update user preferences from encrypted username and patch.
    username and patch must be string
    """
    update_user_preferences_from_patch(username, patch)
    return Response({"result": "success"}, status=status.HTTP_200_OK)
