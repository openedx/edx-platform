"""
Models for notifications
"""
import logging

from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

from openedx.core.djangoapps.notifications.base_notification import (
    get_notification_content,
    COURSE_NOTIFICATION_APPS,
    COURSE_NOTIFICATION_TYPES
)
from openedx.core.djangoapps.notifications.email_notifications import EmailCadence

User = get_user_model()
log = logging.getLogger(__name__)

NOTIFICATION_CHANNELS = ['web', 'push', 'email']

ADDITIONAL_NOTIFICATION_CHANNEL_SETTINGS = ['email_cadence']


def get_notification_channels():
    """
    Returns the notification channels.
    """
    return NOTIFICATION_CHANNELS


def get_additional_notification_channel_settings():
    """
    Returns the additional notification channel settings.
    """
    return ADDITIONAL_NOTIFICATION_CHANNEL_SETTINGS


def create_notification_preference(user_id: int, notification_type: str):
    """
    Create a single notification preference with appropriate defaults.
    Args:
        user_id: ID of the user
        notification_type: Type of notification
    Returns:
        NotificationPreference instance
    """
    notification_config = COURSE_NOTIFICATION_TYPES.get(notification_type, {})
    is_core = notification_config.get('is_core', False)
    app = notification_config['notification_app']

    kwargs = {
        "web": notification_config.get('web', True),
        "push": notification_config.get('push', False),
        "email": notification_config.get('email', False),
        "email_cadence": notification_config.get('email_cadence', EmailCadence.DAILY),
    }
    if is_core:
        app_config = COURSE_NOTIFICATION_APPS[app]
        kwargs = {
            "web": app_config.get("core_web", True),
            "push": app_config.get("core_push", False),
            "email": app_config.get("core_email", False),
            "email_cadence": app_config.get("core_email_cadence", EmailCadence.DAILY),
        }
    return NotificationPreference(
        user_id=user_id,
        type=notification_type,
        app=app,
        **kwargs,
    )


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
    web = models.BooleanField(default=True, null=False, blank=False)
    email = models.BooleanField(default=False, null=False, blank=False)
    push = models.BooleanField(default=False, null=False, blank=False)
    last_read = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    group_by_id = models.CharField(max_length=255, db_index=True, null=False, default="")

    def __str__(self):
        return f'{self.user.username} - {self.course_id} - {self.app_name} - {self.notification_type}'

    @property
    def content(self):
        """
        Returns the content for the notification.
        """
        return get_notification_content(self.notification_type, self.content_context)


class NotificationPreference(TimeStampedModel):
    """
    Model to store notification preferences for users at account level
    """

    class EmailCadenceChoices(models.TextChoices):
        DAILY = 'Daily'
        WEEKLY = 'Weekly'
        IMMEDIATELY = 'Immediately'

    class Meta:
        # Ensures user do not have duplicate preferences.
        unique_together = ('user', 'app', 'type',)

    user = models.ForeignKey(User, related_name="notification_preference", on_delete=models.CASCADE)
    type = models.CharField(max_length=128, db_index=True)
    app = models.CharField(max_length=128, null=False, blank=False, db_index=True)
    web = models.BooleanField(default=True, null=False, blank=False)
    push = models.BooleanField(default=False, null=False, blank=False)
    email = models.BooleanField(default=False, null=False, blank=False)
    email_cadence = models.CharField(max_length=64, choices=EmailCadenceChoices.choices, null=False, blank=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user_id} {self.type} (Web:{self.web}) (Push:{self.push})" \
               f"(Email:{self.email}, {self.email_cadence})"

    @classmethod
    def create_default_preferences_for_user(cls, user_id) -> list:
        """
        Creates all preferences for user
        Note: It creates preferences using bulk create, so primary key will be missing for newly created
        preference. Refetch if primary key is needed
        """
        preferences = list(NotificationPreference.objects.filter(user_id=user_id))
        user_preferences_map = {pref.type: pref for pref in preferences}
        diff = set(COURSE_NOTIFICATION_TYPES.keys()) - set(user_preferences_map.keys())

        if diff:
            missing_types = [
                create_notification_preference(user_id=user_id, notification_type=missing_type)
                for missing_type in diff
            ]
            new_preferences = NotificationPreference.objects.bulk_create(missing_types)
            preferences = preferences + list(new_preferences)
        return preferences

    def is_enabled_for_any_channel(self, *args, **kwargs) -> bool:
        """
        Returns True if the notification preference is enabled for any channel.
        """
        return self.web or self.push or self.email

    def get_channels_for_notification_type(self, *args, **kwargs) -> list:
        """
        Returns the channels for the given app name and notification type.
        Sample Response:
        ['web', 'push']
        """
        channels = []
        if self.web:
            channels.append('web')
        if self.push:
            channels.append('push')
        if self.email:
            channels.append('email')
        return channels

    def get_email_cadence_for_notification_type(self, *args, **kwargs) -> str:
        """
        Returns the email cadence for the notification type.
        """
        return self.email_cadence
