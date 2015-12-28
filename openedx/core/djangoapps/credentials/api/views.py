"""
Credentials API views (v1).
"""
import logging

from rest_framework import status
from rest_framework import viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters


log = logging.getLogger(__name__)


class ProgramCredentialInfoView(APIView):
    """
    View to get credential info related to a program.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    # authentication_classes = (authentication.TokenAuthentication,)
    # permission_classes = (permissions.IsAdminUser,)

    def get(self, request, format=None):
        """
        Return credentials information related to a program.
        """
        credential_info = {
            'user': 'edxapp'
        }
        return Response(credential_info)
