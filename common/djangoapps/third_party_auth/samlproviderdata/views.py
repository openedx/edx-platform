"""
    Viewset for auth/saml/v0/samlproviderdata
"""

from rest_framework import viewsets

from .models import SAMLProviderData
from .serializers import SAMLProviderDataSerializer


class SAMLProviderDataMixin(object):
    queryset = SAMLProviderData.objects.all()
    serializer_class = SAMLProviderDataSerializer
    # permission_classes = [IsAdminUser]


class SAMLProviderDataViewSet(SAMLProviderDataMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderData CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerdata/
    """
