"""
Management command to send reminder emails.
"""

import logging

from textwrap import dedent
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user

from lms.djangoapps.save_for_later.helper import send_email
from lms.djangoapps.save_for_later.models import SavedCourse
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.util.query import use_read_replica_if_available

logger = logging.getLogger(__name__)

USER_SEND_SAVE_FOR_LATER_REMINDER_EMAIL = 'user.send.save.for.later.reminder.email'


class Command(BaseCommand):
    """
    Command to send reminder emails to those users who
    saved course by email but not register within 15 days.


    Examples:

        ./manage.py lms send_course_reminder_emails --batch-size=100
    """
    help = dedent(__doc__)

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Maximum number of users to send reminder email in one chunk')

    def handle(self, *args, **options):
        """
        Handle the send save for later reminder emails.
        """

        reminder_email_threshold_date = datetime.now() - timedelta(
            days=settings.SAVE_FOR_LATER_REMINDER_EMAIL_THRESHOLD)
        saved_courses_ids = SavedCourse.objects.filter(
            reminder_email_sent=False, modified__lt=reminder_email_threshold_date
        ).values_list('id', flat=True)
        total = saved_courses_ids.count()
        batch_size = max(1, options.get('batch_size'))
        num_batches = ((total - 1) / batch_size + 1) if total > 0 else 0

        for batch_num in range(int(num_batches)):
            reminder_email_sent_ids = []
            start = batch_num * batch_size
            end = min(start + batch_size, total) - 1
            saved_courses_batch_ids = list(saved_courses_ids)[start:end + 1]

            query = SavedCourse.objects.filter(id__in=saved_courses_batch_ids).order_by('-modified')
            saved_courses = use_read_replica_if_available(query)
            for saved_course in saved_courses:
                user = User.objects.filter(email=saved_course.email).first()
                course_overview = CourseOverview.get_from_id(saved_course.course_id)
                course_data = {
                    'course': course_overview,
                    'send_to_self': None,
                    'user_id': saved_course.user_id,
                    'org_img_url': saved_course.org_img_url,
                    'marketing_url': saved_course.marketing_url,
                    'weeks_to_complete': saved_course.weeks_to_complete,
                    'min_effort': saved_course.min_effort,
                    'max_effort': saved_course.max_effort,
                    'type': 'course',
                    'reminder': True,
                    'braze_event': USER_SEND_SAVE_FOR_LATER_REMINDER_EMAIL,
                }
                if user:
                    enrollment = CourseEnrollment.get_enrollment(user, saved_course.course_id)
                    if enrollment:
                        continue
                email_sent = send_email(saved_course.email, course_data)
                if email_sent:
                    reminder_email_sent_ids.append(saved_course.id)
                else:
                    logging.info("Unable to send reminder email to {user} for {course} course"
                                 .format(user=str(saved_course.email), course=str(saved_course.course_id)))
            SavedCourse.objects.filter(id__in=reminder_email_sent_ids).update(reminder_email_sent=True)
