"""
Python APIs exposed by the Entitlements app to other in-process apps.
"""

from .models import CourseEntitlement as _CourseEntitlement


def get_active_entitlement_list_for_user(user):
    """
    Arguments:
        user (User): The user we are looking at the entitlements of.

    Returns:
        List: Active entitlements for the provided User.
    """
    return _CourseEntitlement.get_active_entitlements_for_user(user)
