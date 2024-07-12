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
        user.is_superuser or
        (user.is_staff and user.has_perm('user_api.add_userretirementrequest'))
    )

rules.add_perm('accounts.can_retire_user', can_retire_user)
