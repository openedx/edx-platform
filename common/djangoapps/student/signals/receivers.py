"""
Signal receivers for the "student" application.
"""


from django.conf import settings

from student.helpers import USERNAME_EXISTS_MSG_FMT, AccountValidationError
from student.models import is_email_retired, username_exists_or_retired


def on_user_updated(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Check for retired usernames.
    """
    # Check only when not raw and only at User creation time (since validation
    # for the update path is done elsewhere in user_api).
    if not instance.id and not kwargs['raw']:
        prefix_to_check = getattr(settings, 'RETIRED_USERNAME_PREFIX', None)
        if prefix_to_check:
            # Check for username that's too close to retired username format.
            if instance.username.startswith(prefix_to_check):
                raise AccountValidationError(
                    USERNAME_EXISTS_MSG_FMT.format(username=instance.username),
                    field="username"
                )

        # Check for conflict in username
        if username_exists_or_retired(instance.username):
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
