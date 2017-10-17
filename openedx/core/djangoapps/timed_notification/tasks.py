import logging

from datetime import datetime, timedelta, date
from pytz import utc

from core import send_course_notification_email, get_course_link
from lms.djangoapps.branding import get_visible_courses

from celery.task import periodic_task
from celery.schedules import crontab

log = logging.getLogger('edx.celery.task')


@periodic_task(run_every=crontab(minute=1, hour=0))
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
        # Email-template context
        context = {
            'course_name': course.display_name,
            'course_link': get_course_link(course_id=course.id),
        }

        # if course end-date is missing then we can't guess the course week
        if course.end:
            log.info('Getting course end date')
            course_end_date = course.end.date()
            # check if course is already started or just started today and not ended yet
            if (date_now >= course_start_date) and (date_now <= course_end_date):
                if date.today().weekday() == 0:
                    log.info('Calculating course week')
                    course_week = (abs((date_now - course_start_date).days) / 7) + 1
                    log.info('Adding week in the context')
                    context['course_week'] = course_week
                    log.info('Sending weekly notification email')
                    send_course_notification_email(course=course,
                                                   mako_template_path='timed_notification/weekly_notification.txt',
                                                   context=context)
        else:
            log.info("Course: %s, weekly notification-email sending failed, course end-date missing.", course)

        # send email when 7 days left to course start
        if course_start_date - timedelta(days=7) == date_now:
            send_course_notification_email(course=course,
                                           mako_template_path='timed_notification/course_early_welcome.txt',
                                           context=context)
        # send email when 2 days left to course start
        elif course_start_date - timedelta(days=2) == date_now:
            send_course_notification_email(course=course,
                                           mako_template_path='timed_notification/course_start_reminder.txt',
                                           context=context)
        # send email the day the course starts
        elif course_start_date == date_now:
            send_course_notification_email(course=course,
                                           mako_template_path='timed_notification/course_welcome.txt',
                                           context=context)

        log.info('CELERY-TASK: date_now: %s, course_start_date: %s',
                 date_now,
                 course_start_date,
                 )

        if course.end:
            log.info('CELERY-TASK: course_end_date: %s', course.end.date())

        log.info("Finishing celery task")

        courses.pop()
