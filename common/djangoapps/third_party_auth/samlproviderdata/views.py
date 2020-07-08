"""
    Viewset for auth/saml/v0/samlproviderdata
"""

from rest_framework import viewsets

from edx_rbac.mixins import PermissionRequiredMixin

from ..models import SAMLProviderData
from .serializers import SAMLProviderDataSerializer


class SAMLProviderDataMixin(object):
    queryset = SAMLProviderData.objects.all()
    serializer_class = SAMLProviderDataSerializer
    # permission_classes = [IsAdminUser]


class SAMLProviderDataViewSet(PermissionRequiredMixin, SAMLProviderDataMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderData CRUD.
    Uses the edx-rbac mixin PermissionRequiredMixin to apply enterprise authorization

    Usage:
        [HttpVerb] /auth/saml/v0/providerdata/
    """
    permission_required = 'enterprise.can_access_admin_dashboard'
