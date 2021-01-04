import logging

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from social_django.models import UserSocialAuth

from common.djangoapps.student.models import AccountRecovery, Registration, get_retired_email_by_email
from openedx.core.djangolib.oauth2_retirement_utils import retire_dot_oauth2_models

from ...models import UserRetirementStatus


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Manually move a user into the retirement queue, so that they can be
    picked up by the user retirement pipeline. This should only be done in
    the case that a user has tried and is unable to delete their account
    via the UI.

    Most of this code has been lifted from openedx/core/djangoapps/user_api/accounts/views

    As this is a fairly sensitive operation, we want to make sure that human
    error is accounted for. In order to make sure that something like a typo
    during command invocation does not result in the retirement of a
    different user, you must supply both the username and email address linked
    to the user account.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            required=True,
            type=str,
            help='Username to be retired'
        )
        parser.add_argument(
            '--user_email',
            required=True,
            type=str,
            help='User email address.'
        )

    def handle(self, *args, **options):
        """
        Execute the command.
        """

        username = options['username']
        user_email = options['user_email']
        try:
            user = User.objects.get(username=username, email=user_email)
        except:
            error_message = (
                'Could not find a user with specified username and email '
                'address. Make sure you have everything correct before '
                'trying again'
            )
            logger.error(error_message)
            raise CommandError(error_message)

        user_model = get_user_model()

        try:
            with transaction.atomic():
                # Add user to retirement queue.
                UserRetirementStatus.create_retirement(user)
                # Unlink LMS social auth accounts
                UserSocialAuth.objects.filter(user_id=user.id).delete()
                # Change LMS password & email
                user.email = get_retired_email_by_email(user.email)
                user.set_unusable_password()
                user.save()

                # TODO: Unlink social accounts & change password on each IDA.
                # Remove the activation keys sent by email to the user for account activation.
                Registration.objects.filter(user=user).delete()

                # Delete OAuth tokens associated with the user.
                retire_dot_oauth2_models(user)
                AccountRecovery.retire_recovery_email(user.id)
        except KeyError:
            error_message = 'Username not specified {}'.format(user)
            logger.error(error_message)
            raise CommandError(error_message)
        except user_model.DoesNotExist:
            error_message = 'The user "{}" does not exist.'.format(user.username)
            logger.error(error_message)
            raise CommandError(error_message)
        except Exception as exc:  # pylint: disable=broad-except
            error_message = '500 error deactivating account {}'.format(exc)
            logger.error(error_message)
            raise CommandError(error_message)

        logger.info("User succesfully moved to the retirment pipeline")
