"""
Signal receivers for the "student" application.
"""
from __future__ import absolute_import

from django.conf import settings
from django.utils import timezone

from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, waffle
from student.helpers import (
    AccountValidationError,
    USERNAME_EXISTS_MSG_FMT
)
from student.models import (
    is_email_retired,
    is_username_retired,
)


def update_last_login(sender, user, **kwargs):  # pylint: disable=unused-argument
    """
    Replacement for Django's ``user_logged_in`` signal handler that knows not
    to attempt updating the ``last_login`` field when we're trying to avoid
    writes to the ``auth_user`` table while running a migration.
    """
    if not waffle().is_enabled(PREVENT_AUTH_USER_WRITES):
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])


def on_user_updated(sender, instance, **kwargs):  # pylint: disable=unused-argument
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
        if is_email_retired(instance.email):
            raise AccountValidationError(
                EMAIL_EXISTS_MSG_FMT.format(username=instance.email),
                field="email"
            )
