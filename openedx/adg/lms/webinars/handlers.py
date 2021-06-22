"""
handler functions for webinars
"""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .helpers import cancel_all_reminders
from .models import WebinarRegistration


@receiver(post_delete, sender=WebinarRegistration)
def cancel_reminder_emails(instance, **kwargs):  # pylint: disable=unused-argument
    """
    Cancel the reminder emails of a registered user or a webinar team member
    when deleting webinar registration
    """
    if instance.is_registered or instance.is_team_member_registration:
        cancel_all_reminders([instance])
