"""
A command to notify non active users
"""
from datetime import datetime, timedelta
from logging import getLogger

from django.core.management.base import BaseCommand
from pytz import utc

from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email
from courseware.models import StudentModule
from lms.djangoapps.branding import get_visible_courses
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
from openedx.features.course_card.helpers import get_course_open_date
from student.models import CourseEnrollment

log = getLogger(__name__)

DAYS_TO_SEND_EMAIL = 7


class Command(BaseCommand):
    """
    A command to notify non active users
    """

    help = """
    Send Notifications prompts to users who have not entered into course after Course Open Date.
    Orientation module will not be considered because that module will be accessible to user
    before course actually starts. We are managing this by introducing our own date "Course Open Date"
    in custom setting.
    Note: As we know in some cases enrollment process may continues after Course Open Date so if any student
    enroll to some course after 7 days of course open date, those users will not be notified.
    """

    def handle(self, *args, **options):
        courses = get_visible_courses()

        for course in courses:

            today = datetime.now(utc).date()
            log.info('Today date %s', today)

            course_start_date = get_course_open_date(course).date()
            log.info('Course start date %s', course_start_date)

            delta_date = today - course_start_date
            log.info('Days passed since course started %s', delta_date.days)

            if delta_date.days == DAYS_TO_SEND_EMAIL:

                log.info('Getting all enrollments for %s course', course.display_name)
                all_enrollments = CourseEnrollment.objects.filter(course_id=course.id)

                active_users = []
                enrolled_users = []

                for enrollment in all_enrollments:
                    enrolled_users.append(enrollment.user)

                modules = StudentModule.objects.filter(course_id=course.id)

                for mod_entry in modules:
                    # Verifying if mod_entry is between Course Open Date and 7 days after course open date
                    if course_start_date < mod_entry.created.date() \
                            <= (course_start_date + timedelta(days=DAYS_TO_SEND_EMAIL)):
                        active_users.append(mod_entry.student)

                # Getting unique users as Student module may contains multiple entries for same course of same user
                unique_users = set([k for k in dict.fromkeys(active_users)])
                # Getting list of those users who haven't entered in course.
                non_actives = [user for user in enrolled_users if user not in unique_users]

                for non_active_user in non_actives:
                    first_name = non_active_user.first_name
                    course_name = course.display_name
                    course_url = get_course_first_chapter_link(course=course)

                    context = {
                        'emailId': HubSpotClient.COURSE_ACTIVATION_REMINDER_NON_ACTIVE_USERS,
                        'message': {
                            'to': non_active_user.email
                        },
                        'customProperties': {
                            'first_name': first_name,
                            'course_name': course_name,
                            'course_url': course_url
                        }
                    }

                    task_send_hubspot_email.delay(context)
                    log.info("Emailing to %s Task Completed", non_active_user.email)
