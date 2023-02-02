"""
Additional utilities for Learner Home
"""

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from rest_framework.exceptions import PermissionDenied, NotFound

from common.djangoapps.student.models import (
    get_user_by_username_or_email,
)

log = logging.getLogger(__name__)
User = get_user_model()


def get_masquerade_user(request):
    """
    Determine if the user is masquerading

    Returns:
    - masquerade_user if allowed and masquerade user found
    - None if not masquerading

    Raises:
    - PermissionDenied if user is not staff
    - NotFound if masquerade user does not exist
    """
    if request.GET.get("user"):
        if not request.user.is_staff:
            log.info(
                f"[Learner Home] {request.user.username} attempted to masquerade but is not staff"
            )
            raise PermissionDenied()

        masquerade_identifier = request.GET.get("user")
        try:
            masquerade_user = get_user_by_username_or_email(masquerade_identifier)
        except User.DoesNotExist:
            raise NotFound()  # pylint: disable=raise-missing-from
        except MultipleObjectsReturned:
            msg = (
                f"[Learner Home] {masquerade_identifier} could refer to multiple learners. "
                " Defaulting to username."
            )
            log.info(msg)
            masquerade_user = User.objects.get(username=masquerade_identifier)

        success_msg = (
            f"[Learner Home] {request.user.username} masquerades as "
            f"{masquerade_user.username} - {masquerade_user.email}"
        )
        log.info(success_msg)
        return masquerade_user
