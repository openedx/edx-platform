"""
Calendar Sync Email Management
"""


from django.utils.translation import ugettext_lazy as _

from edx_ace.recipient import Recipient
from student.models import CourseEnrollment, CourseOverview
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.features.calendar_sync.message_types import CalendarSync
from openedx.features.calendar_sync.tasks import send_calendar_sync_email


def compose_calendar_sync_email(user, course: CourseOverview, is_update=False):
    """
    Construct all the required params for the calendar
    sync email through celery task
    """

    course_name = course.display_name
    if is_update:
        calendar_sync_subject = _('Updates for Your {course} Schedule').format(course=course_name)
        calendar_sync_headline = _('Update Your Calendar')
        calendar_sync_body = _('Your assignment due dates for {course} were recently adjusted. Update your calendar'
                               'with your new schedule to ensure that you stay on track!').format(course=course_name)
    else:
        calendar_sync_subject = _('Stay on Track')
        calendar_sync_headline = _('Mark Your Calendar')
        calendar_sync_body = _('Sticking to a schedule is the best way to ensure that you successfully complete your '
                               'self-paced course. This schedule of assignment due dates for {course} will help you '
                               'stay on track!').format(course=course_name)
    email_context = {
        'calendar_sync_subject': calendar_sync_subject,
        'calendar_sync_headline': calendar_sync_headline,
        'calendar_sync_body': calendar_sync_body,
    }

    msg = CalendarSync().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=email_context,
    )

    return msg


def compose_and_send_calendar_sync_email(user, course: CourseOverview, is_update=False):
    """
    Construct all the required params and send the activation email
    through celery task

    Arguments:
        user: current logged-in user
        course: course overview object
        is_update: if this should be an 'update' email
    """
    if not CourseEnrollment.objects.filter(user=user, course=course).exists():
        return

    msg = compose_calendar_sync_email(user, course, is_update)

    send_calendar_sync_email.delay(str(msg))
