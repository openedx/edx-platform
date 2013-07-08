"""
Methods for interacting programmatically with the user creator table.
"""
from course_creators.models import CourseCreator
from django.core.exceptions import PermissionDenied

from auth.authz import add_user_to_creator_group


def add_user_with_status_unrequested(caller, user):
    """
    Adds a user to the course creator table with status 'unrequested'.

    Caller must have staff permissions.
    """
    _add_user(caller, user, 'u')


def add_user_with_status_granted(caller, user):
    """
    Adds a user to the course creator table with status 'granted'.

    Caller must have staff permissions. This method also adds the user
    to the course creator group maintained by authz.py.
    """
    _add_user(caller, user, 'g')
    add_user_to_creator_group(caller, user)


def get_course_creator_status(user):
    """
    Returns the status for a particular user.

    Possible return values are:
        'g' = 'granted'
        'u' = 'unrequested'
        'p' = 'pending'
        'd' = 'denied'
    """
    user = CourseCreator.objects.filter(username=user.username)
    assert user.count() == 1, "The user does not exist in the table."
    return user[0].state


def _add_user(caller, user, state):
    """
    Adds a user to the course creator table with the specified state.
    """
    if not caller.is_active or not caller.is_authenticated or not caller.is_staff:
        raise PermissionDenied

    if CourseCreator.objects.filter(username=user.username).count() == 0:
        entry = CourseCreator(username=user.username, email=user.email, state=state)
        entry.save()
