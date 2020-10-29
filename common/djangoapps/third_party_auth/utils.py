"""
Utility functions for third_party_auth
"""
from __future__ import absolute_import

import logging

from django.conf import settings
from django.contrib.auth.models import User

from openedx.core.djangoapps.appsembler.sites.utils import (
    get_current_organization,
    get_single_user_organization
)
from openedx.core.djangoapps.appsembler.multi_tenant_emails.exceptions import (
    SAMLUnusableUsernameDueToMTE
)

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
                return current_org.userorganizationmapping_set.filter(user__email=email).exists()
            elif username:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return False

                if get_single_user_organization(user) == current_org:
                    return True
                else:
                    logger.info(
                        'SAMLUnusableUsernameDueToMTE: Cannot use username '
                        '(%s) in (%s) because it is already taken in a '
                        'different organization (%s)',
                        username,
                        current_org.short_name,
                        get_single_user_organization(user)
                    )
                    raise SAMLUnusableUsernameDueToMTE(
                        'The username is already taken in a different organization'
                    )

        else:
            return User.objects.filter(**user_queryset_filter).exists()

    return False
