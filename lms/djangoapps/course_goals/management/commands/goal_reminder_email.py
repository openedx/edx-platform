"""
Command to trigger sending reminder emails for learners to achieve their Course Goals
"""
from datetime import date, datetime, timedelta
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.api import get_certificate_for_user_id
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.courseware.context_processor import get_user_timezone_or_last_seen_timezone_or_utc
from lms.djangoapps.course_goals.models import CourseGoal, CourseGoalReminderStatus, UserActivity
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.course_duration_limits.access import get_user_course_expiration_date
from openedx.features.course_experience import ENABLE_COURSE_GOALS, ENABLE_SES_FOR_GOALREMINDER
from openedx.features.course_experience.url_helpers import get_learning_mfe_home_url

log = logging.getLogger(__name__)

MONDAY_WEEKDAY = 0
SUNDAY_WEEKDAY = 6


def send_ace_message(goal):
    """
    Send an email reminding users to stay on track for their learning goal in this course

    Arguments:
        goal (CourseGoal): Goal object

    Returns true if sent, false if it absorbed an exception and did not send
    """
    user = goal.user
    try:
        course = CourseOverview.get_from_id(goal.course_key)
    except CourseOverview.DoesNotExist:
        log.error(f"Goal Reminder course {goal.course_key} not found.")
        return False

    course_name = course.display_name

    site = Site.objects.get_current()
    message_context = get_base_template_context(site)

    course_home_url = get_learning_mfe_home_url(course_key=goal.course_key, url_fragment='home')

    goals_unsubscribe_url = f'{settings.LEARNING_MICROFRONTEND_URL}/goal-unsubscribe/{goal.unsubscribe_token}'

    language = get_user_preference(user, LANGUAGE_KEY)

    # Code to allow displaying different banner images for different languages
    # However, we'll likely want to develop a better way to do this within edx-ace
    image_url = settings.STATIC_URL
    if image_url:
        # If the image url is a relative url prepend the LMS ROOT
        if 'http' not in image_url:
            image_url = settings.LMS_ROOT_URL + settings.STATIC_URL
        image_url += 'images/'

        if language and language in ['es', 'es-419']:
            image_url += 'spanish-'

    message_context.update({
        'email': user.email,
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'course_name': course_name,
        'course_id': str(goal.course_key),
        'days_per_week': goal.days_per_week,
        'course_url': course_home_url,
        'goals_unsubscribe_url': goals_unsubscribe_url,
        'image_url': image_url,
        'unsubscribe_url': None,  # We don't want to include the default unsubscribe link
        'omit_unsubscribe_link': True,
        'courses_url': getattr(settings, 'ACE_EMAIL_COURSES_URL', None),
        'programs_url': getattr(settings, 'ACE_EMAIL_PROGRAMS_URL', None),
    })

    options = {'transactional': True}

    is_ses_enabled = ENABLE_SES_FOR_GOALREMINDER.is_enabled(goal.course_key)

    if is_ses_enabled:
        options = {
            'transactional': True,
            'from_address': settings.LMS_COMM_DEFAULT_FROM_EMAIL,
            'override_default_channel': 'django_email',
        }

    msg = Message(
        name="goalreminder",
        app_label="course_goals",
        recipient=Recipient(user.id, user.email),
        language=language,
        context=message_context,
        options=options,
    )

    with emulate_http_request(site, user):
        try:
            ace.send(msg)
        except Exception as exc:  # pylint: disable=broad-except
            log.error(f"Goal Reminder for {user.id} for course {goal.course_key} could not send: {exc}")
            return False
    return True


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms goal_reminder_email
    """
    help = 'Send emails to users that are in danger of missing their course goals for the week'

    def handle(self, *args, **options):
        """
        Handle goal emails across all courses.

        This outer layer calls the inner and reports on any exception that
        occurred.
        """

        try:
            self._handle_all_goals()
        except BaseException:  # pylint: disable=broad-except
            log.exception("Error while sending course goals emails: ")
            for h in log.handlers:
                h.flush()
            raise

    def _handle_all_goals(self):
        """
        Handle goal emails across all courses

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
        log.info(f"Processing course goals across {len(all_goal_course_keys)} courses "
                 + f"excluding {len(courses_to_exclude)} ended courses")

        sent_count = 0
        filtered_count = 0
        course_goals = course_goals.exclude(course_key__in=courses_to_exclude).select_related('user').order_by('user')
        total_goals = len(course_goals)
        log.info(f'Processing course goals, total goal count {total_goals}')
        for goal in course_goals:
            # emulate a request for waffle's benefit
            with emulate_http_request(site=Site.objects.get_current(), user=goal.user):
                if self.handle_goal(goal, today, sunday_date, monday_date):
                    sent_count += 1
                else:
                    filtered_count += 1
            if (sent_count + filtered_count) % 10000 == 0:
                log.info(f'Processing course goals: sent {sent_count} filtered {filtered_count} out of {total_goals}')

        log.info(f'Processing course goals complete: sent {sent_count} emails, filtered out {filtered_count} emails')

    @staticmethod
    def handle_goal(goal, today, sunday_date, monday_date):
        """Sends an email reminder for a single CourseGoal, if it passes all our checks"""
        if not ENABLE_COURSE_GOALS.is_enabled(goal.course_key):
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

        # We want to email users during the day of their timezone
        user_timezone = get_user_timezone_or_last_seen_timezone_or_utc(goal.user)
        now_in_users_timezone = datetime.now(user_timezone)
        if not 8 <= now_in_users_timezone.hour < 18:
            return False

        if required_days_left == days_left_in_week:
            sent = send_ace_message(goal)
            if sent:
                CourseGoalReminderStatus.objects.update_or_create(goal=goal, defaults={'email_reminder_sent': True})
                return True

        return False
