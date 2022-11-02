"""API utils"""

import logging
import requests
from time import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from rest_framework.exceptions import PermissionDenied, NotFound

from common.djangoapps.student.models import (
    get_user_by_username_or_email,
)

log = logging.getLogger(__name__)
User = get_user_model()


def exec_time_logged(func):
    """Wrap the function and return result and execution time"""

    def wrap_func(*args, **kwargs):
        # Time the function operation
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()

        # Display lists / sets as their lengths instead of actual items
        debug_args = []
        for arg in args:
            if isinstance(arg, (list, set)):
                debug_args.append(f"<list: (len {len(arg)})>")
            else:
                debug_args.append(arg)

        # Log the output
        log.info(f"{func.__name__!r} args:{debug_args} completed in {(t2-t1):.4f}s")

        return result

    return wrap_func


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


def get_personalized_course_recommendations(user_id):
    """Get personalize recommendations from Amplitude."""
    headers = {
        "Authorization": f"Api-Key {settings.AMPLITUDE_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "user_id": user_id,
        "get_recs": True,
        "rec_id": settings.REC_ID,
    }
    try:
        response = requests.get(settings.AMPLITUDE_URL, params=params, headers=headers)
        if response.status_code == 200:
            response = response.json()
            recommendations = response.get("userData", {}).get("recommendations", [])
            if recommendations:
                is_control = recommendations[0].get("is_control")
                recommended_course_keys = recommendations[0].get("items")
                return is_control, recommended_course_keys
    except Exception as ex:  # pylint: disable=broad-except
        log.warning(f"Cannot get recommendations from Amplitude: {ex}")

    return True, []
