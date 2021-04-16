"""
Handlers for Webinars app
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from openedx.adg.lms.webinars.models import Webinar
from openedx.adg.lms.webinars.tasks import task_reschedule_webinar_reminders


@receiver(pre_save, sender=Webinar)
def rescheduled_reminder_emails(instance, **kwargs):  # pylint: disable=unused-argument
    """
    Reschedules reminder emails for webinar if start_time is updated.
    """
    if instance.start_time != Webinar.objects.get(id=instance.id).start_time:
        task_reschedule_webinar_reminders.delay(instance.id)
