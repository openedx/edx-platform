"""
Credentials API views (v1).
"""
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response

from openedx.core.djangoapps.credentials.api.v1 import serializers


class GenerateProgramsCredentialView(APIView):
    serializer_class = serializers.GenerateProgramsCredentialSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):
        serializer = serializers.GenerateProgramsCredentialSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        credential_data = serializer.validated_data
        usernames = credential_data['usernames'].split(',')

        data_for_credentials_service = [
            self._get_user_context_for_program(username=username, program_id=credential_data['program_id'],
                                               whitelist=credential_data['is_whitelist'],
                                               whitelist_reason=credential_data['whitelist_reason']) for username in
            usernames if User.objects.filter(username=username).exists()
        ]

        # TODO call credential service for generating credentials

        # sample response data which will be received from credentials service
        response = {
            "credential_type": "program-certificate",
            "credential_id": 123,
            "username": "edxapp",
            "program_id": 1,
            "status": "(awarded|revoked)",
            "uuid": "abc123",
            "attributes": [
                {"namespace": "whitelist", "name": "Whitelist", "value": "Reason"}
            ]
        }

        return Response(response)

    def _get_user_context_for_program(self, username, program_id, whitelist, whitelist_reason=None):
        """ Helper method that will return dict of credential info on the basis of user input.

        Arguments:
            username (string): username for which credential need to be created
            program_id (int): unique id for X-series program
            whitelist (boolean): True if credentials are created for a whitelist user
            whitelist_reason (string): reason for white listing

        Returns:
            Returns dict that contains required input for credential
        """
        credential_info = {
            "username": username,
            "program_id": program_id,
            }

        if whitelist:
            credential_info.update({
                "attributes": {
                "namespace": "whitelist", "name": "program_whitelist", "value": whitelist_reason
            }
        })
        return credential_info
