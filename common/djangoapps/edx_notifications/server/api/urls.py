"""
All URL mappings for HTTP-based APIs
"""
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from edx_notifications.server.api import consumer as consumer_views

from .url_regex import (
    CONSUMER_NOTIFICATIONS_COUNT_REGEX,
    CONSUMER_NOTIFICATION_DETAIL_REGEX,
    CONSUMER_NOTIFICATIONS_MARK_NOTIFICATIONS_REGEX,
    CONSUMER_NOTIFICATIONS_REGEX,
    CONSUMER_RENDERERS_TEMPLATES_REGEX,
    CONSUMER_NOTIFICATION_DETAIL_NO_PARAM_REGEX,
    CONSUMER_USER_PREFERENCES_DETAIL_REGEX,
    CONSUMER_NOTIFICATIONS_PREFERENCES_REGEX,
    CONSUMER_USER_PREFERENCES_REGEX,
    CONSUMER_USER_PREFERENCES_DETAIL_NO_PARAM_REGEX)


urlpatterns = patterns(  # pylint: disable=invalid-name
    '',
    url(
        CONSUMER_NOTIFICATIONS_COUNT_REGEX,
        consumer_views.NotificationCount.as_view(),
        name='edx_notifications.consumer.notifications.count'
    ),
    url(
        CONSUMER_NOTIFICATION_DETAIL_REGEX,
        consumer_views.NotificationDetail.as_view(),
        name='edx_notifications.consumer.notifications.detail'
    ),
    url(
        CONSUMER_NOTIFICATION_DETAIL_NO_PARAM_REGEX,
        consumer_views.NotificationDetail.as_view(),
        name='edx_notifications.consumer.notifications.detail.no_param'
    ),
    url(
        CONSUMER_NOTIFICATIONS_MARK_NOTIFICATIONS_REGEX,
        consumer_views.MarkNotificationsAsRead.as_view(),
        name='edx_notifications.consumer.notifications.mark_notifications_as_read'
    ),
    url(
        CONSUMER_NOTIFICATIONS_REGEX,
        consumer_views.NotificationsList.as_view(),
        name='edx_notifications.consumer.notifications'
    ),
    url(
        CONSUMER_RENDERERS_TEMPLATES_REGEX,
        consumer_views.RendererTemplatesList.as_view(),
        name='edx_notifications.consumer.renderers.templates'
    ),
    url(
        CONSUMER_NOTIFICATIONS_PREFERENCES_REGEX,
        consumer_views.NotificationPreferenceList.as_view(),
        name='edx_notifications.consumer.notification_preferences'
    ),
    url(
        CONSUMER_USER_PREFERENCES_REGEX,
        consumer_views.UserPreferenceList.as_view(),
        name='edx_notifications.consumer.user_preferences'
    ),
    url(
        CONSUMER_USER_PREFERENCES_DETAIL_REGEX,
        consumer_views.UserPreferenceDetail.as_view(),
        name='edx_notifications.consumer.user_preferences.detail'
    ),
    url(
        CONSUMER_USER_PREFERENCES_DETAIL_NO_PARAM_REGEX,
        consumer_views.UserPreferenceDetail.as_view(),
        name='edx_notifications.consumer.user_preferences.detail.no_param'
    ),
)

urlpatterns = format_suffix_patterns(urlpatterns)  # pylint: disable=invalid-name
