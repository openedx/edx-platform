"""
Management command to send program reminder emails.
"""

import logging

from textwrap import dedent
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user

from lms.djangoapps.save_for_later.helper import send_email
from lms.djangoapps.save_for_later.models import SavedProgram
from lms.djangoapps.program_enrollments.api import get_program_enrollment
from openedx.core.djangoapps.catalog.utils import get_programs
from common.djangoapps.util.query import use_read_replica_if_available

LOGGER = logging.getLogger(__name__)

USER_SEND_SAVE_FOR_LATER_REMINDER_EMAIL = 'user.send.save.for.later.reminder.email'


class Command(BaseCommand):
    """
    Command to send reminder emails to those users who saved
    program by email but not enroll program within 15 days.


    Examples:

        ./manage.py lms send_program_reminder_emails --batch-size=100
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
        saved_program_ids = SavedProgram.objects.filter(
            reminder_email_sent=False, modified__lt=reminder_email_threshold_date
        ).values_list('id', flat=True)
        total = saved_program_ids.count()
        batch_size = max(1, options.get('batch_size'))
        num_batches = ((total - 1) / batch_size + 1) if total > 0 else 0

        for batch_num in range(int(num_batches)):
            reminder_email_sent_ids = []
            start = batch_num * batch_size
            end = min(start + batch_size, total) - 1
            saved_program_batch_ids = list(saved_program_ids)[start:end + 1]

            query = SavedProgram.objects.filter(id__in=saved_program_batch_ids).order_by('-modified')
            saved_programs = use_read_replica_if_available(query)
            for saved_program in saved_programs:
                user = User.objects.filter(email=saved_program.email).first()
                program = get_programs(uuid=saved_program.program_uuid)
                if program:
                    program_data = {
                        'program': program,
                        'send_to_self': None,
                        'user_id': saved_program.user_id,
                        'type': 'program',
                        'reminder': True,
                        'braze_event': USER_SEND_SAVE_FOR_LATER_REMINDER_EMAIL,
                    }
                    try:
                        if user and get_program_enrollment(program_uuid=saved_program.program_uuid, user=user):
                            continue
                    except ObjectDoesNotExist:
                        pass
                    email_sent = send_email(saved_program.email, program_data)
                    if email_sent:
                        reminder_email_sent_ids.append(saved_program.id)
                    else:
                        logging.info("Unable to send reminder email to {user} for {program} program"
                                     .format(user=str(saved_program.email), program=str(saved_program.program_uuid)))
            SavedProgram.objects.filter(id__in=reminder_email_sent_ids).update(reminder_email_sent=True)
