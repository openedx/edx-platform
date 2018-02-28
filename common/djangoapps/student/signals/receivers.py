"""
Signal receivers for the "student" application.
"""
from __future__ import absolute_import

from django.utils import timezone

from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, waffle


def update_last_login(sender, user, **kwargs):  # pylint: disable=unused-argument
    """
    Replacement for Django's ``user_logged_in`` signal handler that knows not
    to attempt updating the ``last_login`` field when we're trying to avoid
    writes to the ``auth_user`` table while running a migration.
    """
    if not waffle().is_enabled(PREVENT_AUTH_USER_WRITES):
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
