"""
All URL mappings for the API's which do not get mapped to Django REST Frameworks view handlers
This is useful for when we need a UI tier to do a reverse on URL's where we don't need to import
all of the backend
"""
from django.conf.urls import patterns, url
from django.http import HttpResponseBadRequest

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
    CONSUMER_USER_PREFERENCES_DETAIL_NO_PARAM_REGEX,
)


def mock_handler(request):  # pylint: disable=unused-argument
    """
    Simply return a 400
    """
    return HttpResponseBadRequest()


urlpatterns = patterns(  # pylint: disable=invalid-name
    '',
    url(
        CONSUMER_NOTIFICATIONS_COUNT_REGEX,
        mock_handler,
        name='edx_notifications.consumer.notifications.count'
    ),
    url(
        CONSUMER_NOTIFICATION_DETAIL_REGEX,
        mock_handler,
        name='edx_notifications.consumer.notifications.detail'
    ),
    url(
        CONSUMER_NOTIFICATION_DETAIL_NO_PARAM_REGEX,
        mock_handler,
        name='edx_notifications.consumer.notifications.detail.no_param'
    ),
    url(
        CONSUMER_NOTIFICATIONS_MARK_NOTIFICATIONS_REGEX,
        mock_handler,
        name='edx_notifications.consumer.notifications.mark_notifications_as_read'
    ),
    url(
        CONSUMER_NOTIFICATIONS_REGEX,
        mock_handler,
        name='edx_notifications.consumer.notifications'
    ),
    url(
        CONSUMER_RENDERERS_TEMPLATES_REGEX,
        mock_handler,
        name='edx_notifications.consumer.renderers.templates'
    ),
    url(
        CONSUMER_NOTIFICATIONS_PREFERENCES_REGEX,
        mock_handler,
        name='edx_notifications.consumer.notification_preferences'
    ),
    url(
        CONSUMER_USER_PREFERENCES_REGEX,
        mock_handler,
        name='edx_notifications.consumer.user_preferences'
    ),
    url(
        CONSUMER_USER_PREFERENCES_DETAIL_REGEX,
        mock_handler,
        name='edx_notifications.consumer.user_preferences.detail'
    ),
    url(
        CONSUMER_USER_PREFERENCES_DETAIL_NO_PARAM_REGEX,
        mock_handler,
        name='edx_notifications.consumer.user_preferences.detail.no_param'
    ),
)
