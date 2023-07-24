"""
Management command to send Schedule course due date reminders
"""

import datetime
import pytz
from textwrap import dedent  # lint-amnesty, pylint: disable=wrong-import-order

from django.contrib.sites.models import Site

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import COURSE_DUE_DATE_REMINDER_LOG_PREFIX, ScheduleCourseDueDateReminders


class Command(SendEmailBaseCommand):
    """
    Command to send due date reminders for subsections in Self paced courses.

    Note: this feature does not support reminders for INDIVIDUAL_DUE_DATES as the applicable schedule
    objects are fetched based on course relative due dates.

    Usage:
        ./manage.py lms send_course_due_date_reminders localhost:18000 --due 7 --date 2023-06-07

    Positional required args:
        - site: Django site domain name, for example: localhost:18000
    Keyword Required args
        - due-in: Remind subsections due in given days
    Optional args:
        - date: The date to compute weekly messages relative to, in YYYY-MM-DD format.
        - override-recipient-email: Send all emails to this address instead of the actual recipient
    """
    help = dedent(__doc__).strip()
    async_send_task = ScheduleCourseDueDateReminders
    log_prefix = COURSE_DUE_DATE_REMINDER_LOG_PREFIX

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--due-in',
            type=int,
            help='Remind subsections due in given days',
        )

    def handle(self, *args, **options):
        current_date = datetime.datetime(
            *[int(x) for x in options['date'].split('-')],
            tzinfo=pytz.UTC
        )

        site = Site.objects.get(domain__iexact=options['site_domain_name'])
        override_recipient_email = options.get('override_recipient_email')

        self.async_send_task.enqueue(site, current_date, options['due_in'], override_recipient_email)
