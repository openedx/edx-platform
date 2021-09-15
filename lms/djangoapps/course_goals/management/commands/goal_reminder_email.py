"""
Command to trigger sending reminder emails for learners to achieve their Course Goals
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.api import get_certificate_for_user_id
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.course_goals.models import CourseGoal, UserActivity
from lms.djangoapps.course_goals.toggles import COURSE_GOALS_NUMBER_OF_DAYS_GOALS
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_duration_limits.access import get_user_course_expiration_date

MONDAY_WEEKDAY = 0
SUNDAY_WEEKDAY = 6


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms goal_reminder_email
    """
    help = ''

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
            CourseGoal.objects.filter(email_reminder_sent=True).update(email_reminder_sent=False)
            return

        course_goals = CourseGoal.objects.filter(days_per_week__gt=0, subscribed_to_reminders=True, email_reminder_sent=False)
        all_goal_course_keys = course_goals.values_list('course_key', flat=True).distinct()
        # Exclude all courses whose end dates are earlier than Sunday so we don't send an email about hitting
        # a course goal when it may not even be possible.
        # NOTE TO MT: Should we maybe also use this list and set all of the course goals in this to be unsubscribed?
        courses_to_exclude = CourseOverview.objects.filter(
            id__in=all_goal_course_keys, end__date__lt=sunday_date
        ).values_list('id', flat=True)

        course_goals = course_goals.exclude(course_key__in=courses_to_exclude).select_related('user').order_by('user')
        for goal in course_goals:
            if not COURSE_GOALS_NUMBER_OF_DAYS_GOALS.is_enabled(goal.course_key):
                continue

            enrollment = CourseEnrollment.objects.prefetch_related('course_overview').get(user=goal.user, course__id=goal.course_key)
            # If you're not actively enrolled in the course or your enrollment was this week
            if not enrollment.is_active or enrollment.created.date() >= monday_date:
                continue

            audit_access_expiration_date = get_user_course_expiration_date(user, enrollment.course_overview)
            # If an audit user's access expires this week, exclude them from the email since they may not
            # be able to hit their goal anyway
            if audit_access_expiration_date and audit_access_expiration_date.date() < sunday_date:
                # NOTE TO MT: Is this overkill? If they upgrade, I think they'd need to reselect it, but if they
                # don't, then we at least stop doing this for them for the rest of time.
                goal.update(subscribed_to_reminders=False)
                continue

            # NOTE TO MT: I had a thread with Aperture Eng (Justin Hynes) about which function to use here. This was the recommended one
            cert = get_certificate_for_user_id(goal.user, goal.course_key)
            # If a user has a downloadable certificate, we will consider them as having completed
            # the course and opt them out of receiving emails
            if cert and cert.status == CertificateStatuses.downloadable:
                # NOTE TO MT: Is this overkill? If their cert status changes, they would remain unsubscribed.
                # Also just not sure if it's bad for us to unsubscribe them anyway. Could be a weird thing to
                # come back to. I leave to your discretion.
                goal.update(subscribed_to_reminders=False)
                continue

            # Check the number of days left to successfully hit their goal
            week_activity_count = UserActivity.objects.filter(user=goal.user, course_key=goal.course_key, date__gte=monday_date).count()
            required_days_left = goal.days_per_week - week_activity_count
            # The weekdays are 0 indexed, but we want this to be 1 to match required_days_left.
            # Essentially, if today is Sunday, days_left_in_week should be 1 since they have Sunday to hit their goal.
            days_left_in_week = SUNDAY_WEEKDAY - today.weekday() + 1
            if required_days_left == days_left_in_week:
                # TODO: hook up email https://openedx.atlassian.net/browse/AA-909
                # ace.send(msg)
                goal.update(email_reminder_sent=True)
