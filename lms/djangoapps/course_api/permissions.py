"""
Course API Authorization functions
"""

from student.roles import GlobalStaff


def can_view_courses_for_username(requesting_user, target_username):
    """
    Determine whether `requesting_user` has permission to view courses available
    to the user identified by `target_username`.

    Arguments:
        requesting_user (User): The user requesting permission to view another
        target_username (string):
            The name of the user `requesting_user` would like
            to access.

    Return value:
        Boolean:
            `True` if `requesting_user` is authorized to view courses as
            `target_username`.  Otherwise, `False`
    Raises:
        TypeError if target_username is empty or None.
    """

    # AnonymousUser has no username, so we test for requesting_user's own
    # username before prohibiting an empty target_username.
    if requesting_user.username == target_username:
        return True
    elif not target_username:
        raise TypeError("target_username must be specified")
    else:
        staff = GlobalStaff()
        return staff.has_user(requesting_user)
