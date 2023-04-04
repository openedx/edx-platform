"""
Models for notifications
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db import models
from model_utils.models import TimeStampedModel


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
    app_name = models.CharField(max_length=64, choices=NotificationApplication.choices)
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
