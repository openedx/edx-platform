""" Utilities for views in the course home api"""
from rest_framework.exceptions import PermissionDenied

from lms.djangoapps.courseware.courses import get_course_with_access as base_get_course_with_access
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect


def get_course_or_403(*args, **kwargs):
    """
    When we make requests to the various Learner Home API endpoints, we do not want to return the actual redirects,
    Instead we should return an error code. The redirect info is returned from the course metadata endpoint and the
    URL can be followed by whatever client is calling.

    Raises:
     - 404 if course is not found
     - 403 if the requesting user does not have access to the course
    """
    try:
        return base_get_course_with_access(*args, **kwargs)
    except CourseAccessRedirect as e:
        raise PermissionDenied(
            detail=e.access_error.user_message,
            code=e.access_error.error_code
        ) from e
