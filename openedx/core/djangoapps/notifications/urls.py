"""
URLs for the notifications API.
"""
from django.conf import settings
from django.urls import path, re_path
from rest_framework import routers

from .views import (
    CourseEnrollmentListView,
    MarkNotificationsSeenAPIView,
    NotificationCountView,
    NotificationListAPIView,
    NotificationReadAPIView,
    UpdateAllNotificationPreferencesView,
    UserNotificationPreferenceView,
    preference_update_from_encrypted_username_view, AggregatedNotificationPreferences
)

router = routers.DefaultRouter()

urlpatterns = [
    path('enrollments/', CourseEnrollmentListView.as_view(), name='enrollment-list'),
    re_path(
        fr'^configurations/{settings.COURSE_KEY_PATTERN}$',
        UserNotificationPreferenceView.as_view(),
        name='notification-preferences'
    ),
    path(
        'configurations/',
        AggregatedNotificationPreferences.as_view(),
        name='notification-preferences-aggregated'
    ),
    path('', NotificationListAPIView.as_view(), name='notifications-list'),
    path('count/', NotificationCountView.as_view(), name='notifications-count'),
    path(
        'mark-seen/<app_name>/',
        MarkNotificationsSeenAPIView.as_view(),
        name='mark-notifications-seen'
    ),
    path('read/', NotificationReadAPIView.as_view(), name='notifications-read'),
    path('preferences/update/<str:username>/<str:patch>/', preference_update_from_encrypted_username_view,
         name='preference_update_from_encrypted_username_view'),
    path(
        'preferences/update-all/',
        UpdateAllNotificationPreferencesView.as_view(),
        name='update-all-notification-preferences'
    ),
]

urlpatterns += router.urls
