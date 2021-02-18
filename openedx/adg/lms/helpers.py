"""
ADG LMS Helpers
"""


def get_user_first_name(user):
    """
    Get First name of the user, Checks if first name is available otherwise
    splits full name to get the first name.
    Args:
        user: Auth User instance
    Returns:
        (str) first name of the user

    """
    return user.first_name or user.profile.full_name.split()[0]
