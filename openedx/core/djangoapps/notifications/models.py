"""
Models for notifications
"""
from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField


User = get_user_model()

NOTIFICATION_CHANNELS = ['web', 'push', 'email']

# When notification preferences are updated, we need to update the CONFIG_VERSION.
NOTIFICATION_PREFERENCE_CONFIG = {
    'discussion': {
        'enabled': False,
        'notification_types': {
            'new_post': {
                'info': '',
                'web': False,
                'push': False,
                'email': False,
            },
            'core': {
                'info': '',
                'web': False,
                'push': False,
                'email': False,
            },
        },
        # This is a list of notification channels for notification type that are not editable by the user.
        # e.g. 'new_post' web notification is not editable by user i.e. 'not_editable': {'new_post': ['web']}
        'not_editable': {},
    },
}
# Update this version when NOTIFICATION_PREFERENCE_CONFIG is updated.
NOTIFICATION_CONFIG_VERSION = 1


def get_notification_preference_config():
    """
    Returns the notification preference config.
    """
    return NOTIFICATION_PREFERENCE_CONFIG


def get_notification_preference_config_version():
    """
    Returns the notification preference config version.
    """
    return NOTIFICATION_CONFIG_VERSION


def get_notification_channels():
    """
    Returns the notification channels.
    """
    return NOTIFICATION_CHANNELS


class NotificationApplication(models.TextChoices):
    """
    Application choices where notifications are generated from
    """
    DISCUSSION = 'DISCUSSION'


class NotificationType(models.TextChoices):
    """
    Notification type choices
    """
    NEW_CONTRIBUTION = 'NEW_CONTRIBUTION'


class NotificationTypeContent:
    """
    Notification type content
    """
    NEW_CONTRIBUTION_NOTIFICATION_CONTENT = 'There is a new contribution. {new_contribution}'


class Notification(TimeStampedModel):
    """
    Model to store notifications for users

    .. no_pii:
    """
    user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    app_name = models.CharField(max_length=64, choices=NotificationApplication.choices, db_index=True)
    notification_type = models.CharField(max_length=64, choices=NotificationType.choices)
    content = models.CharField(max_length=1024)
    content_context = models.JSONField(default=dict)
    content_url = models.URLField(null=True, blank=True)
    last_read = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.app_name} - {self.notification_type} - {self.content}'


class NotificationPreference(TimeStampedModel):
    """
    Model to store notification preferences for users

    .. no_pii:
    """
    user = models.ForeignKey(User, related_name="notification_preferences", on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, blank=True, default=None)
    notification_preference_config = models.JSONField(default=get_notification_preference_config)
    # This version indicates the current version of this notification preference.
    config_version = models.IntegerField(blank=True, default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} - {self.course_id} - {self.notification_preference_config}'
