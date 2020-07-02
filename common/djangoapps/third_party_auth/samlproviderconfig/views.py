"""
    Viewset for auth/saml/v0/samlproviderconfig
"""

from rest_framework import viewsets
from rest_framework.decorators import action

from .models import SAMLProviderConfig
from .serializers import SAMLProviderConfigSerializer


class SAMLProviderMixin(object):
    queryset = SAMLProviderConfig.objects.all()
    serializer_class = SAMLProviderConfigSerializer
    # TODO: Authorization work pending, right now open API
    # permission_classes = [IsAdminUser]


class SAMLProviderConfigViewSet(SAMLProviderMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerconfig/
    """
