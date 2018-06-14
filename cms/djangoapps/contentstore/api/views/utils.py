"""
Common utilities for Contentstore APIs.
"""
from rest_framework import status

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.util.forms import to_bool
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from student.auth import has_course_author_access


def get_bool_param(request, param_name, default):
    param_value = request.query_params.get(param_name, None)
    bool_value = to_bool(param_value)
    if bool_value is None:
        return default
    else:
        return bool_value


def course_author_access_required(view):
    """
    Ensure the user making the API request has course author access to the given course.

    This decorator parses the course_id parameter, checks course access, and passes
    the parsed course_key to the view as a parameter. It will raise a
    403 error if the user does not have author access.

    Usage::
        @course_author_access_required
        def my_view(request, course_key):
            # Some functionality ...
    """
    def _wrapper_view(self, request, course_id, *args, **kwargs):
        """
        Checks for course author access for the given course by the requesting user.
        Calls the view function if has access, otherwise raises a 403.
        """
        course_key = CourseKey.from_string(course_id)
        if not has_course_author_access(request.user, course_key):
            raise DeveloperErrorViewMixin.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The requesting user does not have course author permissions.',
                error_code='user_permissions',
            )
        return view(self, request, course_key, *args, **kwargs)
    return _wrapper_view
