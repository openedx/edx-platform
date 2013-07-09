"""
Methods for interacting programmatically with the user creator table.
"""
from course_creators.models import CourseCreator
from django.core.exceptions import PermissionDenied

from auth.authz import add_user_to_creator_group, remove_user_from_creator_group


def add_user_with_status_unrequested(caller, user):
    """
    Adds a user to the course creator table with status 'unrequested'.

    If the user is already in the table, this method is a no-op
    (state will not be changed). Caller must have staff permissions.
    """
    _add_user(caller, user, CourseCreator.UNREQUESTED)


def add_user_with_status_granted(caller, user):
    """
    Adds a user to the course creator table with status 'granted'.

    If the user is already in the table, this method is a no-op
    (state will not be changed). Caller must have staff permissions.

    This method also adds the user to the course creator group maintained by authz.py.
    """
    _add_user(caller, user, CourseCreator.GRANTED)
    update_course_creator_group(caller, user, True)


def update_course_creator_group(caller, user, add):
    """
    Method for adding and removing users from the creator group.

    Caller must have staff permissions.
    """
    if add:
        add_user_to_creator_group(caller, user)
    else:
        remove_user_from_creator_group(caller, user)


def get_course_creator_status(user):
    """
    Returns the status for a particular user, or None if user is not in the table.

    Possible return values are:
        'unrequested' = user has not requested course creation rights
        'pending' = user has requested course creation rights
        'granted' = user has been granted course creation rights
        'denied' = user has been denied course creation rights
        None = user does not exist in the table
    """
    user = CourseCreator.objects.filter(user=user)
    if user.count() == 0:
        return None
    else:
        # User is defined to be unique, can assume a single entry.
        return user[0].state


def _add_user(caller, user, state):
    """
    Adds a user to the course creator table with the specified state.

    If the user is already in the table, this method is a no-op
    (state will not be changed).
    """
    if not caller.is_active or not caller.is_authenticated or not caller.is_staff:
        raise PermissionDenied

    if CourseCreator.objects.filter(user=user).count() == 0:
        entry = CourseCreator(user=user, state=state)
        entry.save()
