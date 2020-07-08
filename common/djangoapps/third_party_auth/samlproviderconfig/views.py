"""
    Viewset for auth/saml/v0/samlproviderconfig
"""

from rest_framework import viewsets

from edx_rbac.mixins import PermissionRequiredMixin

from ..models import SAMLProviderConfig
from .serializers import SAMLProviderConfigSerializer


class SAMLProviderMixin(object):
    queryset = SAMLProviderConfig.objects.all()
    serializer_class = SAMLProviderConfigSerializer


class SAMLProviderConfigViewSet(PermissionRequiredMixin, SAMLProviderMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerconfig/
    """
    permission_required = 'enterprise.can_access_admin_dashboard'
