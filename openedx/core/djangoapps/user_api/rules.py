"""
Django rules for accounts
"""


import rules
from django.conf import settings


@rules.predicate
def can_retire_user(user):
    """
    Returns whether the user can retire accounts
    """
    return (
        user.username == settings.RETIREMENT_SERVICE_WORKER_USERNAME or
        user.is_superuser
    )

rules.add_perm('accounts.can_retire_user', can_retire_user)
