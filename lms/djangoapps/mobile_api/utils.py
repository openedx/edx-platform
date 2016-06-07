"""
Common utility methods and decorators for Mobile APIs.
"""
from openedx.core.lib.api.view_utils import view_course_access, view_auth_classes


def mobile_course_access(depth=0):
    """
    Method decorator for a mobile API endpoint that verifies the user has access to the course in a mobile context.
    """
    return view_course_access(depth=depth, access_action='load_mobile', check_for_milestones=True)


def mobile_view(is_user=False):
    """
    Function and class decorator that abstracts the authentication and permission checks for mobile api views.
    """
    return view_auth_classes(is_user)


def parsed_version(version):
    """ Converts string X.X.X.Y to int tuple (X, X, X) """
    return tuple(map(int, (version.split(".")[:3])))
