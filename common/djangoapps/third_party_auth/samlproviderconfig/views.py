"""
    Viewset for auth/saml/v0/samlproviderconfig
"""

from rest_framework import viewsets

from third_party_auth.models import SAMLProviderConfig
from third_party_auth.samlproviderconfig.serializers import SAMLProviderConfigSerializer


class SAMLProviderConfigViewSet(viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerconfig/
    """
    queryset = SAMLProviderConfig.objects.all()
    serializer_class = SAMLProviderConfigSerializer
    # permission_classes = [IsAdminUser]
