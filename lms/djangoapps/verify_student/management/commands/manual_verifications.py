"""
Django admin commands related to verify_student
"""


import logging
import os
from pprint import pformat

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from lms.djangoapps.verify_student.models import ManualVerification
from lms.djangoapps.verify_student.utils import earliest_allowed_verification_date

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This method attempts to manually verify users.
    Example usage:
        $ ./manage.py lms manual_verifications --email-ids-file <absolute path of file with email ids (one per line)>
    """
    help = 'Manually verifies one or more users passed as an argument list.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email-ids-file',
            action='store',
            dest='email_ids_file',
            default=None,
            help='Path of the file to read email id from.',
            type=str,
            required=True
        )

    def handle(self, *args, **options):

        email_ids_file = options['email_ids_file']

        if email_ids_file:
            if not os.path.exists(email_ids_file):
                raise CommandError(u'Pass the correct absolute path to email ids file as --email-ids-file argument.')

        total_emails, failed_emails = self._generate_manual_verification_from_file(email_ids_file)

        if failed_emails:
            log.error(u'Completed manual verification. {} of {} failed.'.format(
                len(failed_emails),
                total_emails
            ))
            log.error(u'Failed emails:{}'.format(pformat(failed_emails)))
        else:
            log.info(u'Successfully generated manual verification for {} emails.'.format(total_emails))

    def _generate_manual_verification_from_file(self, email_ids_file):
        """
        Generate manual verification for the emails provided in the email ids file.

        Arguments:
            email_ids_file (str): path of the file containing email ids.

        Returns:
            (total_emails, failed_emails): a tuple containing count of emails processed and a list containing
             emails whose verifications could not be processed.
        """
        failed_emails = []

        with open(email_ids_file, 'r') as file_handler:
            email_ids = file_handler.readlines()
            total_emails = len(email_ids)
            log.info(u'Creating manual verification for {} emails.'.format(total_emails))
            for email_id in email_ids:
                try:
                    email_id = email_id.strip()
                    user = User.objects.get(email=email_id)
                    ManualVerification.objects.get_or_create(
                        user=user,
                        status='approved',
                        created_at__gte=earliest_allowed_verification_date(),
                        defaults={'name': user.profile.name},
                    )
                except User.DoesNotExist:
                    failed_emails.append(email_id)
                    err_msg = u'Tried to verify email {}, but user not found'
                    log.error(err_msg.format(email_id))
        return total_emails, failed_emails
