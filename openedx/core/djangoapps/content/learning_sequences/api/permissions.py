"""
This is a dummy placeholder for now, as access to this endpoint is currently
limited to global staff.
"""


def can_see_all_content(requesting_user, _course_key):
    return requesting_user.is_staff
