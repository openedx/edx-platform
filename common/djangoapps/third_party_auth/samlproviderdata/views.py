"""
    Viewset for auth/saml/v0/samlproviderdata
"""

from rest_framework import viewsets

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
