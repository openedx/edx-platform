"""
Viewset for auth/saml/v0/saml_configuration
"""

from rest_framework import permissions, viewsets

from ..models import SAMLConfiguration
from .serializers import SAMLConfigurationSerializer


class SAMLConfigurationMixin:
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SAMLConfigurationSerializer


class SAMLConfigurationViewSet(SAMLConfigurationMixin, viewsets.ReadOnlyModelViewSet):
    """
    A View to handle SAMLConfiguration GETs

    Usage:
        GET /auth/saml/v0/saml_configuration/
    """

    def get_queryset(self):
        """
        Find and return all saml configurations that are listed as public.
        """
        return SAMLConfiguration.objects.current_set().filter(is_public=True)
