"""
Tasks for webinars
"""
from datetime import timedelta

from celery.task import task
from django.utils.timezone import now

from openedx.adg.lms.webinars.helpers import reschedule_webinar_reminders
from openedx.adg.lms.webinars.models import Webinar, WebinarRegistration


@task()
def task_reschedule_webinar_reminders(webinar_id):
    """
    Reschedules all the webinar reminders.

    Args:
        webinar_id (int): Webinar Id for which reminders will be rescheduled.
    """
    webinar = Webinar.objects.get(id=webinar_id)

    week_before_start_time = webinar.start_time - timedelta(days=7)
    two_hours_before_start_time = webinar.start_time - timedelta(hours=2)

    registrations = WebinarRegistration.objects.filter(webinar=webinar)

    if week_before_start_time > now():
        reschedule_webinar_reminders(registrations, week_before_start_time, 'week_before_mandrill_reminder_id')

    if two_hours_before_start_time > now():
        reschedule_webinar_reminders(registrations, two_hours_before_start_time, 'starting_soon_mandrill_reminder_id')
