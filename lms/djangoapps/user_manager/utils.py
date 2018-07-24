"""
Utilities for User Manager Application.
"""
from .models import UserManagerRole


def create_user_manager_role(user, manager_user=None, manager_email=None):
    """
    Crates a new ``UserManagerRole`` given a ``user`` and a ``manager_user``
    or ``manager_email``.
    """
    if manager_email is not None:
        obj, _ = UserManagerRole.objects.get_or_create(
            unregistered_manager_email=manager_email,
            user=user,
        )
    else:
        obj, _ = UserManagerRole.objects.get_or_create(
            manager_user=manager_user,
            user=user
        )
    return obj
