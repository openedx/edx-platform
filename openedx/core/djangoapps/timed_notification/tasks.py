import logging
from datetime import datetime, timedelta, date
from pytz import utc
from openedx.core.djangoapps.timed_notification.core import \
    send_course_notification_email, \
    get_course_link, \
    get_course_first_chapter_link
from lms.djangoapps.branding import get_visible_courses
from common.lib.hubspot_client.client import HubSpotClient
from openedx.features.course_card.helpers import get_course_open_date
from nodebb.helpers import get_community_url
from django.conf import settings


log = logging.getLogger('edx.celery.task')


def task_course_notifications():
    log.info('Getting courses')
    courses = get_visible_courses()

    for course in courses:
        log.info("checking course {} for email".format(course.id))

        # we're interested only in dates
        course_open_date = get_course_open_date(course)
        course_start_date = course_open_date.date()

        log.info('Course start date %s', course_start_date)

        date_now = datetime.now(utc).date()
        log.info('Today date %s', date_now)

        context = {}
        template = None
        course_name = course.display_name
        course_discussion_url = "{}/category/{}".format(settings.NODEBB_ENDPOINT, get_community_url(course.id))
        course_url = get_course_link(course_id=course.id)

        # create context when 7 days left to course start
        if course_start_date - timedelta(days=7) == date_now:
            template = HubSpotClient.COURSE_WEEK_BEFORE_REMINDER
            context = {
                'course_name': course_name,
                'course_discussion_URL': course_discussion_url,
                'course_url': course_url
            }

        # create context when when 2 days left to course start
        elif course_start_date - timedelta(days=2) == date_now:
            template = HubSpotClient.COURSE_TWO_DAYS_BEFORE_REMINDER
            context = {
                'course_name': course_name,
                'course_discussion_URL': course_discussion_url,
                'course_url': course_url
            }

        # create context on the day the course starts
        elif course_start_date == date_now:
            template = HubSpotClient.COURSE_WELCOME_EMAIL_NOTIFICATION
            context = {
                'course_name': course_name,
                'course_url': get_course_first_chapter_link(course)
            }

        log.info('Setting up email context')

        # if context is set then send email
        if context and template:
            send_course_notification_email(
                course=course,
                template_id=template,
                context=context
            )

            log.info('CELERY-TASK: date_now: %s, course_start_date: %s', date_now, course_start_date)

            if course.end:
                log.info('CELERY-TASK: course_end_date: %s', course.end.date())

            log.info("Finishing celery task")

    log.info("Emailing Task Completed")
