"""
Models for notifications
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

# When notification preferences are updated, we need to update the CONFIG_VERSION.
NOTIFICATION_PREFERENCE_CONFIG = {
    "discussion": {
        "new_post": {
            "web": False,
            "push": False,
            "email": False,
        },
    },
}
# Update this version when NOTIFICATION_PREFERENCE_CONFIG is updated.
CONFIG_VERSION = 1


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
    content_context = models.JSONField(default={})
    content_url = models.URLField(null=True, blank=True)
    last_read = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.app_name} - {self.notification_type} - {self.content}'

    def get_content(self):
        return self.content

    def get_content_url(self):
        return self.content_url

    def get_notification_type(self):
        return self.notification_type

    def get_app_name(self):
        return self.app_name

    def get_content_context(self):
        return self.content_context

    def get_user(self):
        return self.user


class NotificationPreference(TimeStampedModel):
    """
    Model to store notification preferences for users

    .. no_pii:
    """
    user = models.ForeignKey(User, related_name="notification_preferences", on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, blank=True, default=None)
    notification_preference_config = models.JSONField(default=NOTIFICATION_PREFERENCE_CONFIG)
    # This version indicates the current version of this notification preference.
    config_version = models.IntegerField(blank=True, default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} - {self.course_id} - {self.notification_preference_config}'

    def get_user(self):
        return self.user

    def get_course_id(self):
        return self.course_id

    def get_notification_preference_config(self):
        return self.notification_preference_config

    def get_config_version(self):
        return self.config_version

    def get_is_active(self):
        return self.is_active
