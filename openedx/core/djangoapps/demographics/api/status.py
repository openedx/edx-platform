"""
Python API for Demographics Status
"""

from openedx.core.djangoapps.programs.api import is_user_enrolled_in_program_type
from openedx.features.enterprise_support.utils import is_enterprise_learner


def show_user_demographics(user, enrollments=None, entitlements=None):
    """
    Check if the user should be shown demographics collection fields. Currently limited
    to MicroBachlors Programs' learners who aren't part of an enterprise.
    """
    is_user_in_microbachelors_program = is_user_enrolled_in_program_type(
        user, "microbachelors", enrollments=enrollments, entitlements=entitlements
    )
    return is_user_in_microbachelors_program and not is_enterprise_learner(user)


def show_call_to_action_for_user(user):
    """
    Utility method to determine if a user should be shown the Demographics call to
    action.
    """
    return False
