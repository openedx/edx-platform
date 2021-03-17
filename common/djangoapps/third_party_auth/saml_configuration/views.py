"""
Viewset for auth/saml/v0/saml_configuration
"""

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication

from ..models import SAMLConfiguration
from .serializers import SAMLConfigurationSerializer


class SAMLConfigurationMixin(object):
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SAMLConfigurationSerializer


class SAMLConfigurationViewSet(SAMLConfigurationMixin, viewsets.ModelViewSet):
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
