"""
Use this mgmt command when a user requests retirement mistakenly, then requests
for the retirement request to be cancelled. The command can't cancel a retirement
that has already commenced - only pending retirements.
"""


import logging

from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangoapps.user_authn.utils import generate_password

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Implementation of the cancel_user_retirement_request command.
    """
    help = 'Cancels the retirement of a user who has requested retirement - but has not yet been retired.'

    def add_arguments(self, parser):
        parser.add_argument('email_address',
                            help='Email address of user whose retirement request will be cancelled.')

    def handle(self, *args, **options):
        """
        Execute the command.
        """
        email_address = options['email_address'].lower()

        try:
            # Load the user retirement status.
            retirement_status = UserRetirementStatus.objects.select_related('current_state').select_related('user').get(
                original_email=email_address
            )
        except UserRetirementStatus.DoesNotExist:
            raise CommandError(u"No retirement request with email address '{}' exists.".format(email_address))

        # Check if the user has started the retirement process -or- not.
        if retirement_status.current_state.state_name != 'PENDING':
            raise CommandError(
                u"Retirement requests can only be cancelled for users in the PENDING state."
                u" Current request state for '{}': {}".format(
                    email_address,
                    retirement_status.current_state.state_name
                )
            )

        # Load the user record using the retired email address -and- change the email address back.
        retirement_status.user.email = email_address
        retirement_status.user.set_password(generate_password(length=25))
        retirement_status.user.save()

        # Delete the user retirement status record.
        # No need to delete the accompanying "permanent" retirement request record - it gets done via Django signal.
        retirement_status.delete()

        print(u"Successfully cancelled retirement request for user with email address '{}'.".format(email_address))
