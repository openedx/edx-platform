import logging
from datetime import datetime, timedelta, date
from pytz import utc
from openedx.core.djangoapps.timed_notification.core import send_course_notification_email, get_course_link, get_course_first_chapter_link
from lms.djangoapps.branding import get_visible_courses
from common.lib.mandrill_client.client import MandrillClient


log = logging.getLogger('edx.celery.task')


def task_course_notifications():
    log.info('Getting courses')
    courses = get_visible_courses()

    while courses:
        log.info('Pop first course')
        course = courses[-1]

        # we're interested only in dates
        log.info('Getting course start date')
        course_start_date = course.start.date()
        log.info('Today date')
        date_now = datetime.now(utc).date()

        log.info('Setting up email context')
        context = {
            'course_name': course.display_name,
            'course_url': get_course_link(course_id=course.id)
        }

        # send email when 7 days left to course start
        if course_start_date - timedelta(days=7) == date_now:
            send_course_notification_email(course=course,
                                           template_name=MandrillClient.COURSE_EARLY_WELCOME_TEMPLATE,
                                           context=context)
        # send email when 2 days left to course start
        elif course_start_date - timedelta(days=2) == date_now:
            send_course_notification_email(course=course,
                                           template_name=MandrillClient.COURSE_START_REMINDER_TEMPLATE,
                                           context=context)

        # send email the day the course starts
        elif course_start_date == date_now:
            send_course_notification_email(course=course,
                                           template_name=MandrillClient.COURSE_WELCOME_TEMPLATE,
                                           context={'course_name': course.display_name,
                                                    'course_url': get_course_first_chapter_link(course)
                                                    }
                                           )

        log.info('CELERY-TASK: date_now: %s, course_start_date: %s',
            date_now,
            course_start_date,
            )

        if course.end:
            log.info('CELERY-TASK: course_end_date: %s', course.end.date())

        log.info("Finishing celery task")

        courses.pop()
