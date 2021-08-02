"""
Custom user-related utility code.
"""

from django.contrib.auth.models import AnonymousUser


class SystemUser(AnonymousUser):
    """
    A User that can act on behalf of system actions, when a user object is
    needed, but no real user exists.

    Like the AnonymousUser, this User is not represented in the database, and
    has no primary key.
    """

    # pylint: disable=abstract-method
    def __str__(self):
        return 'SystemUser'
