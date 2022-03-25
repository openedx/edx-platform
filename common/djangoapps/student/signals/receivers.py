"""
Signal receivers for the "student" application.
"""


from django.conf import settings

from openedx.core.djangoapps.appsembler.sites.utils import get_current_organization

from student.helpers import USERNAME_EXISTS_MSG_FMT, AccountValidationError
from student.helpers import EMAIL_EXISTS_MSG_FMT
from student.models import is_email_retired, is_username_retired


def on_user_updated(sender, instance, **kwargs):
    """
    Check for retired usernames.
    """
    # Check only at User creation time and when not raw.
    if not instance.id and not kwargs['raw']:
        prefix_to_check = getattr(settings, 'RETIRED_USERNAME_PREFIX', None)
        if prefix_to_check:
            # Check for username that's too close to retired username format.
            if instance.username.startswith(prefix_to_check):
                raise AccountValidationError(
                    USERNAME_EXISTS_MSG_FMT.format(username=instance.username),
                    field="username"
                )

        # Check for a retired username.
        if is_username_retired(instance.username):
            raise AccountValidationError(
                USERNAME_EXISTS_MSG_FMT.format(username=instance.username),
                field="username"
            )

        # Check for a retired email.
        if not settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
            # Note: Doing a loose check for retirement within organization in case
            #       of non-request contexts such as management commands or Django shell which is not a
            #       common use-case at all, except that it shows up in tests when we don't do full mocking.
            #
            #       This is a best-effort trade-off to allow compatibility with upstream while enabling
            #       the unique constraints on all learner-initiated contexts.
            #
            #        There are limitations to this such as limited or non-existent checks for superuser
            #        operations via the admin panel.
            #
            #        For more information about the AccountValidationError below please checkout the
            #        upstream conversations at:
            #               - https://github.com/edx/edx-platform/pull/18136
            #               - https://openedx.atlassian.net/browse/PLAT-2117
            organization = get_current_organization(failure_return_none=True)
            if is_email_retired(
                    email=instance.email,
                    # Avoid a chicken-and-egg problem in which that we don't have an active request to get the
                    # organization from.
                    #
                    # This specifically solves the issue with `student.signals..on_user_updated` for new users
                    # calls `is_email_retired` in non-request contexts.
                    #
                    # Chicken-and-egg:
                    #   It's impossible to get the organization for a user that we didn't save yet
                    #   to the database because we don't have a link between the user and the organization yet.
                    #   We cannot have that link until we save the user,
                    #   therefore it's not possible to get the organization from the user.
                    check_within_organization=bool(organization),
                    organization=organization,
            ):
                raise AccountValidationError(
                    EMAIL_EXISTS_MSG_FMT.format(username=instance.email),
                    field="email"
                )
