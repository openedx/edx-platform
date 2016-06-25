""" API v0 views. """
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lms.djangoapps.certificates.api import get_certificate_for_user
from openedx.core.lib.api import (
    authentication,
    permissions,
)


log = logging.getLogger(__name__)


class CertificatesDetailView(GenericAPIView):
    """
        **Use Case**

            * Get the details of a certificate for a specific user in a course.

        **Example Request**

            GET /api/certificates/v0/certificates/{username}/courses/{course_id}

        **GET Parameters**

            A GET request must include the following parameters.

            * username: A string representation of an user's username.
            * course_id: A string representation of a Course ID.

        **GET Response Values**

            If the request for information about the Certificate is successful, an HTTP 200 "OK" response
            is returned.

            The HTTP 200 response has the following values.

            * username: A string representation of an user's username passed in the request.

            * course_id: A string representation of a Course ID.

            * certificate_type: A string representation of the certificate type.
                Can be honor|verified|professional

            * status: A string representation of the certificate status.

            * download_url: A string representation of the certificate url.

            * grade: A string representation of a float for the user's course grade.

        **Example GET Response**

            {
                "username": "bob",
                "course_id": "edX/DemoX/Demo_Course",
                "certificate_type": "verified",
                "status": "downloadable",
                "download_url": "http://www.example.com/cert.pdf",
                "grade": "0.98"
            }
    """

    authentication_classes = (
        authentication.OAuth2AuthenticationAllowInactiveUser,
        authentication.SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (
        IsAuthenticated,
        permissions.IsUserInUrlOrStaff
    )

    def get(self, request, username, course_id):
        """
        Gets a certificate information.

        Args:
            request (Request): Django request object.
            username (string): URI element specifying the user's username.
            course_id (string): URI element specifying the course location.

        Return:
            A JSON serialized representation of the certificate.
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.warning('Course ID string "%s" is not valid', course_id)
            return Response(
                status=404,
                data={'error_code': 'course_id_not_valid'}
            )

        user_cert = get_certificate_for_user(username=username, course_key=course_key)
        if user_cert is None:
            return Response(
                status=404,
                data={'error_code': 'no_certificate_for_user'}
            )
        return Response(
            {
                "username": user_cert.get('username'),
                "course_id": unicode(user_cert.get('course_key')),
                "certificate_type": user_cert.get('type'),
                "status": user_cert.get('status'),
                "download_url": user_cert.get('download_url'),
                "grade": user_cert.get('grade')
            }
        )
