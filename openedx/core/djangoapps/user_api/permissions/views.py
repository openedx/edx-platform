from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.parsers import MergePatchParser
from ..errors import UserNotFound, UserNotAuthorized


class PermissionsView(APIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    parser_classes = (MergePatchParser,)

    def get(self, request):
        """
        GET /api/user/v1/
        """
        try:
            is_staff = request.user.is_staff
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(is_staff)
