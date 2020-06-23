from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from third_party_auth.models import SAMLProviderConfig
from third_party_auth.samlproviderconfig.serializers import SAMLProviderConfigSerializer

class SAMLProviderConfigView(generics.ListCreateAPIView):
    """
    A View to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/samlproviderconfig/
    """
    queryset = SAMLProviderConfig.objects.all()
    serializer_class = SAMLProviderConfigSerializer
    permission_classes = [IsAdminUser]
