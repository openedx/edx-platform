from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from third_party_auth.models import SAMLProviderData
from third_party_auth.samlproviderdata.serializers import SAMLProviderDataSerializer


class SAMLProviderDataViewSet(viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderData CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerdata/
    """
    queryset = SAMLProviderData.objects.all()
    serializer_class = SAMLProviderDataSerializer
    # permission_classes = [IsAdminUser]
