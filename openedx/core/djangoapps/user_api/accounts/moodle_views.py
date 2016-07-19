from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.parsers import MergePatchParser

from certificates.models import MdlCertificateIssued
from student.models import MdlToEdx
from django.contrib.auth.models import User
from .moodle_serializers import MoodleCertificateSerializer


class MoodleCertificateView(APIView):

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MergePatchParser,)

    def get(self, request, username):
        """
        GET /api/user/v1/certificates/moodle/{username}/
        """
        try:
            user = User.objects.get(username=username) # handle user exception also
            mdl_id =MdlToEdx.objects.get(user_id=user.id).mdl_user_id
            certificates = MdlCertificateIssued.objects.filter(mdl_userid=mdl_id)
            serializer = MoodleCertificateSerializer(certificates, many=True)
            return Response(serializer.data)
        except MdlToEdx.DoesNotExist:
            serializer = MoodleCertificateSerializer([], many=True)
            return Response(serializer.data)
