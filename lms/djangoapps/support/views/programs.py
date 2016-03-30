# pylint: disable=missing-docstring
import logging

from rest_framework import permissions, status, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework_oauth.authentication import OAuth2Authentication

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tasks.v1.tasks import award_program_certificates


log = logging.getLogger(__name__)


class IssueProgramCertificatesView(views.APIView):
    """
    **Use Cases**

        Trigger the task responsible for awarding program certificates on behalf
        of the user with the provided username.

    **Example Requests**

        POST /support/programs/certify/
        {
            'username': 'foo'
        }

    **Returns**

        * 200 on success.
        * 400 if program certification is disabled or a username is not provided.
        * 401 if the request is not authenticated.
        * 403 if the authenticated user does not have staff permissions.
    """
    authentication_classes = (SessionAuthentication, OAuth2Authentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser,)

    def post(self, request):
        if not ProgramsApiConfig.current().is_certification_enabled:
            return Response(
                {'error': 'Program certification is disabled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = request.data.get('username')
        if username:
            log.info('Enqueuing program certification task for user [%s]', username)
            award_program_certificates.delay(username)

            return Response()
        else:
            return Response(
                {'error': 'A username is required in order to issue program certificates.'},
                status=status.HTTP_400_BAD_REQUEST
            )
