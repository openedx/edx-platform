"""
Models for notifications
"""
from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

from openedx.core.djangoapps.notifications.base_notification import NotificationAppManager

User = get_user_model()

NOTIFICATION_CHANNELS = ['web', 'push', 'email']

# Update this version when there is a change to any course specific notification type or app.
COURSE_NOTIFICATION_CONFIG_VERSION = 1


def get_course_notification_preference_config():
    """
    Returns the course specific notification preference config.

    Sample Response:
    {
        'discussion': {
            'enabled': True,
            'not_editable': {
                'new_comment_on_post': ['push'],
                'new_response_on_post': ['web'],
                'new_response_on_comment': ['web', 'push']
            },
            'notification_types': {
                'new_comment_on_post': {
                    'email': True,
                    'push': True,
                    'web': True,
                    'info': 'Comment on post'
                },
                'new_response_on_comment': {
                    'email': True,
                    'push': True,
                    'web': True,
                    'info': 'Response on comment'
                },
                'new_response_on_post': {
                    'email': True,
                    'push': True,
                    'web': True,
                    'info': 'New Response on Post'
                },
                'core': {
                    'email': True,
                    'push': True,
                    'web': True,
                    'info': 'comment on post and response on comment'
                }
            },
            'core_notification_types': []
        }
    }
    """
    return NotificationAppManager().get_notification_app_preferences()


def get_course_notification_preference_config_version():
    """
    Returns the notification preference config version.
    """
    return COURSE_NOTIFICATION_CONFIG_VERSION


def get_notification_channels():
    """
    Returns the notification channels.
    """
    return NOTIFICATION_CHANNELS


class Notification(TimeStampedModel):
    """
    Model to store notifications for users

    .. no_pii:
    """
    user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, null=True, blank=True)
    app_name = models.CharField(max_length=64, db_index=True)
    notification_type = models.CharField(max_length=64)
    content_context = models.JSONField(default=dict)
    content_url = models.URLField(null=True, blank=True)
    last_read = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.course_id} - {self.app_name} - {self.notification_type}'


class CourseNotificationPreference(TimeStampedModel):
    """
    Model to store notification preferences for users

    .. no_pii:
    """
    user = models.ForeignKey(User, related_name="notification_preferences", on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, null=False, blank=False)
    notification_preference_config = models.JSONField(default=get_course_notification_preference_config)
    # This version indicates the current version of this notification preference.
    config_version = models.IntegerField(default=get_course_notification_preference_config_version)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'course_id')

    def __str__(self):
        return f'{self.user.username} - {self.course_id} - {self.notification_preference_config}'
