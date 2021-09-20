"""
Command to trigger sending reminder emails for learners to achieve their Course Goals
"""
from datetime import date, timedelta
import logging

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.api import get_certificate_for_user_id
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.course_goals.models import CourseGoal, CourseGoalReminderStatus, UserActivity
from lms.djangoapps.course_goals.toggles import COURSE_GOALS_NUMBER_OF_DAYS_GOALS
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.course_duration_limits.access import get_user_course_expiration_date

log = logging.getLogger(__name__)

MONDAY_WEEKDAY = 0
SUNDAY_WEEKDAY = 6


def ace_send():
    """Just here as a mock hook for tests - drop this once we fix AA-909"""


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms goal_reminder_email
    """
    help = 'Send emails to users that are in danger of missing their course goals for the week'

    def handle(self, *args, **options):
        """
        Docstring

        Helpful notes for the function:
            weekday() returns an int 0-6 with Monday being 0 and Sunday being 6
        """
        today = date.today()
        sunday_date = today + timedelta(days=SUNDAY_WEEKDAY - today.weekday())
        monday_date = today - timedelta(days=today.weekday())

        # Monday is the start of when we consider user's activity towards counting towards their weekly
        # goal. As such, we use Mondays to clear out the email reminders sent from the previous week.
        if today.weekday() == MONDAY_WEEKDAY:
            CourseGoalReminderStatus.objects.filter(email_reminder_sent=True).update(email_reminder_sent=False)
            log.info('Cleared all reminder statuses')
            return

        course_goals = CourseGoal.objects.filter(
            days_per_week__gt=0, subscribed_to_reminders=True,
        ).exclude(
            reminder_status__email_reminder_sent=True,
        )
        all_goal_course_keys = course_goals.values_list('course_key', flat=True).distinct()
        # Exclude all courses whose end dates are earlier than Sunday so we don't send an email about hitting
        # a course goal when it may not even be possible.
        courses_to_exclude = CourseOverview.objects.filter(
            id__in=all_goal_course_keys, end__date__lte=sunday_date
        ).values_list('id', flat=True)

        count = 0
        course_goals = course_goals.exclude(course_key__in=courses_to_exclude).select_related('user').order_by('user')
        with emulate_http_request(site=Site.objects.get_current()):  # emulate a request for waffle's benefit
            for goal in course_goals:
                if self.handle_goal(goal, today, sunday_date, monday_date):
                    count += 1

        log.info(f'Sent {count} emails')

    @staticmethod
    def handle_goal(goal, today, sunday_date, monday_date):
        """Sends an email reminder for a single CourseGoal, if it passes all our checks"""
        if not COURSE_GOALS_NUMBER_OF_DAYS_GOALS.is_enabled(goal.course_key):
            return False

        enrollment = CourseEnrollment.get_enrollment(goal.user, goal.course_key, select_related=['course'])
        # If you're not actively enrolled in the course or your enrollment was this week
        if not enrollment or not enrollment.is_active or enrollment.created.date() >= monday_date:
            return False

        audit_access_expiration_date = get_user_course_expiration_date(goal.user, enrollment.course_overview)
        # If an audit user's access expires this week, exclude them from the email since they may not
        # be able to hit their goal anyway
        if audit_access_expiration_date and audit_access_expiration_date.date() <= sunday_date:
            return False

        cert = get_certificate_for_user_id(goal.user, goal.course_key)
        # If a user has a downloadable certificate, we will consider them as having completed
        # the course and opt them out of receiving emails
        if cert and cert.status == CertificateStatuses.downloadable:
            return False

        # Check the number of days left to successfully hit their goal
        week_activity_count = UserActivity.objects.filter(
            user=goal.user, course_key=goal.course_key, date__gte=monday_date,
        ).count()
        required_days_left = goal.days_per_week - week_activity_count
        # The weekdays are 0 indexed, but we want this to be 1 to match required_days_left.
        # Essentially, if today is Sunday, days_left_in_week should be 1 since they have Sunday to hit their goal.
        days_left_in_week = SUNDAY_WEEKDAY - today.weekday() + 1
        if required_days_left == days_left_in_week:
            # TODO: hook up email AA-909
            # ace.send(msg)
            ace_send()  # temporary for tests, drop with AA-909 and just mock ace.send directly
            CourseGoalReminderStatus.objects.update_or_create(goal=goal, defaults={'email_reminder_sent': True})
            return True

        return False
