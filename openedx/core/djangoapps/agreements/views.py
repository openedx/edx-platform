"""Views served by the agreements app. """

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseStaffRole

from .api import get_integrity_signature
from .toggles import is_integrity_signature_enabled


def is_user_course_or_global_staff(user, course_id):
    """
    Return whether a user is course staff for a given course, described by the course_id,
    or is global staff.
    """

    return user.is_staff or auth.user_has_role(user, CourseStaffRole(CourseKey.from_string(course_id)))


class AuthenticatedAPIView(APIView):
    """
        Authenticated API View.
    """
    authentication_classes = (SessionAuthentication, JwtAuthentication)
    permission_classes = (IsAuthenticated,)


class IntegritySignatureView(AuthenticatedAPIView):
    """
    Endpoint for an Integrity Signature
    /integrity_signature/{course_id}

    Supports:
        HTTP GET: Returns an existing signed integrity agreement (by course id and user)

    HTTP GET
        ** Scenarios **
        ?username=xyz
        returns an existing signed integrity agreement for the given user and course
    """

    def get(self, request, course_id):
        """
        In order to check whether the user has signed the integrity agreement for a given course.

        Should return the following:
            username (str)
            course_id (str)
            created_at (str)

        If a username is not given, it should default to the requesting user (or masqueraded user).
        Only staff should be able to access this endpoint for other users.
        """
        # check that waffle flag is enabled
        if not is_integrity_signature_enabled():
            return Response(
                status=status.HTTP_404_NOT_FOUND,
            )

        # check that user can make request
        user = request.user.username
        requested_user = request.GET.get('username')
        is_staff = is_user_course_or_global_staff(request.user, course_id)

        if not is_staff and requested_user and (user != requested_user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": "User does not have permission to view integrity agreement."
                }
            )

        username = requested_user if requested_user else user
        signature = get_integrity_signature(username, course_id)

        if signature is None:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
            )

        created_at = str(signature.created)

        data = {
            'username': username,
            'course_id': course_id,
            'created_at': created_at,
        }

        return Response(data)
