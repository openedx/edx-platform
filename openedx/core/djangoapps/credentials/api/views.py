"""
Credentials API views (v1).
"""
import logging
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.programs.utils import get_program_by_id


log = logging.getLogger(__name__)


class ProgramCredentialInfoView(APIView):
    """
    View to get credential info related to a program.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    # authentication_classes = (authentication.TokenAuthentication,)
    # permission_classes = (permissions.IsAdminUser,)

    def get(self, request, username, program_id):
        """
        Return credentials information related to a program.
        """
        try:
            user = User.objects.select_related('profile').get(username=username)
        except User.DoesNotExist:
            log.exception("User '{username}' doesn't exist.".format(username=username))
            return Response(status=status.HTTP_404_NOT_FOUND)

        program = get_program_by_id(user, program_id=int(program_id))
        if not program:
            return Response(status=status.HTTP_404_NOT_FOUND)

        credential_info_data = {
            "full_name": user.profile.name,
            "program_data": program,
            "platform_name": settings.PLATFORM_NAME
        }

        return Response(credential_info_data)
