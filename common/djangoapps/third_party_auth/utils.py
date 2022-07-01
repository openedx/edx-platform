"""
Utility functions for third_party_auth
"""

import logging

from django.conf import settings
from django.contrib.auth.models import User
from tahoe_sites.api import is_exist_organization_user_by_email

from openedx.core.djangoapps.appsembler.sites.utils import get_current_organization

logger = logging.getLogger(__name__)


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
        user_queryset_filter['username__iexact'] = username

    if user_queryset_filter:
        if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
            current_org = get_current_organization()

            if email:
                return is_exist_organization_user_by_email(email=email, organization=current_org)
            elif username:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return False
                else:
                    return True

        else:
            return User.objects.filter(**user_queryset_filter).exists()

    return False
