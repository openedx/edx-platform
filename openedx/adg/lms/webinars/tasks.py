"""
Tasks for webinars
"""
from celery.task import task

from openedx.adg.lms.webinars.helpers import cancel_all_reminders, schedule_webinar_reminders
from openedx.adg.lms.webinars.models import Webinar


@task()
def task_reschedule_webinar_reminders(webinar_data):
    """
    Reschedules all the webinar reminders.

    Args:
        webinar_data (dict): Dict containing webinar data.

    Returns:
        None
    """
    webinar = Webinar.objects.get(id=webinar_data['webinar_id'])
    registrations = webinar.registrations.webinar_team_and_active_user_registrations()

    cancel_all_reminders(registrations, is_rescheduling=True)
    schedule_webinar_reminders(list(registrations.values_list('user__email', flat=True)), webinar_data)
