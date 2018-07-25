"""
One-off script to rehash all retired emails.

Background: We discovered that all prior retired emails were generated based on
the exact capitalization of the original email address, despite the fact that
emails are considered case insensitive in practice.  This led to the
possibility of users registering accounts with effectively retired emails just
by changing the capitalization of the email, because the different
capitalization would hash to a different digest.

Solution: Rehash all email addresses using the normalized-case (lowercase)
original emails rather than the possibly mixed-case ones.  This management
command likely cannot be re-used in the future because eventually we will need
to clean out the UserRetirementStatus table.
"""

from __future__ import print_function

from django.conf import settings
from django.db import transaction
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from user_util import user_util


class Command(BaseCommand):
    """
    Implementation of the bulk_rehash_retired_emails command.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Print proposed changes, but take no action.'
        )

    def handle(self, *args, **options):
        """
        Execute the command.
        """

        dry_run = options['dry_run']

        retirements = UserRetirementStatus.objects.all().select_related('user')
        for retirement in retirements:
            original_email = retirement.original_email
            old_retired_email = retirement.retired_email
            new_retired_email = user_util.get_retired_email(
                original_email,
                settings.RETIRED_USER_SALTS,
                settings.RETIRED_EMAIL_FMT
            )

            # Sanity check:
            if retirement.user.email != old_retired_email:
                print(
                    'WARNING: Skipping UserRetirementStatus ID {} / User ID {} because the user does not appear to '
                    'have a retired email address: {}.'.format(
                        retirement.id,
                        retirement.user.id,
                        retirement.user.email,
                    )
                )
            # If the original email address was already normalized (or all lowercase), the old and new hashes would
            # match:
            elif old_retired_email == new_retired_email:
                print(
                    'Skipping UserRetirementStatus ID {} / User ID {} because the email hash would not change.'.format(
                        retirement.id,
                        retirement.user.id,
                    )
                )
            # Found an email to update:
            else:
                print('Updating UserRetirementStatus ID {} / User ID {} to rehash their retired email: {} -> {}'.format(
                    retirement.id,
                    retirement.user.id,
                    old_retired_email,
                    new_retired_email,
                ))
                if not dry_run:
                    # Update and save both the user table and retirement queue table:
                    with transaction.atomic():
                        retirement.user.email = new_retired_email
                        retirement.user.save()
                        retirement.retired_email = new_retired_email
                        retirement.save()
                    # The only other place to update is in sailthru, so make sure to save the logging from this
                    # management command to make it possible to update sailthru later.
