"""
Utility functions for third_party_auth
"""

from django.contrib.auth.models import User


def user_exists(details):
    """
    Return True if user with given details exist in the system.

    Arguments:
        details (dict): dictionary containing user infor like email, username etc.

    Returns:
        (bool): True if user with given details exists, `False` otherwise.
    """
    user_queryset_filter = {}
    email = details.get('email')
    username = details.get('username')
    if email:
        user_queryset_filter['email'] = email
    elif username:
        user_queryset_filter['username'] = username

    if user_queryset_filter:
        return User.objects.filter(**user_queryset_filter).exists()

    return False
