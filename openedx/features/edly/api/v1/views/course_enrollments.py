"""
Views for course enrollments API
"""
from figures.views import CourseEnrollmentViewSet
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission


class EdlyCourseEnrollmentViewSet(CourseEnrollmentViewSet):
    """
    **Use Case**

        Get information about the course enrollments about a specific course.

    **Example Request**

        GET /api/v1/courses/course_enrollment/

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK" response.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
        )
    permission_classes = (ApiKeyHeaderPermission,)
