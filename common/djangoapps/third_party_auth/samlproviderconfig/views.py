"""
    Viewset for auth/saml/v0/samlproviderconfig
"""

from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication

from edx_rbac.mixins import PermissionRequiredMixin
from edx_rest_framework_extensions.auth.jwt.authentication import (
    JwtAuthentication,
)
from ..models import SAMLProviderConfig
from .serializers import SAMLProviderConfigSerializer
from enterprise.models import EnterpriseCustomerIdentityProvider
from third_party_auth.samlutils.utils import fetch_enterprise_customer_by_id


class SAMLProviderMixin(object):
    authentication_classes = [JwtAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SAMLProviderConfigSerializer


class SAMLProviderConfigViewSet(PermissionRequiredMixin, SAMLProviderMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerconfig/?enterprise-id=uuid
    """

    """
    This string refers to the rule name defined in edx-rbac
    That rule will allow rbac to check if the EnterpriseCustomer
    returned by the get_permission_object method here, can be
    accessed by the user making this request (request.user)
    Access is only allowed if the user has the system role
    of 'ENTERPRISE_ADMIN' which is defined in enterprise.constants
    """
    permission_required = 'enterprise.can_access_admin_dashboard'

    def get_queryset(self):
        """
        Find and return the matching providerid for the given enterprise uuid
        """
        enterprise_customer_idp = EnterpriseCustomerIdentityProvider.objects.get(
            enterprise_customer__uuid=self.requested_enterprise_uuid
        )
        return SAMLProviderConfig.objects.filter(pk=enterprise_customer_idp.provider_id)

    @property
    def requested_enterprise_uuid(self):
        return self.request.query_params.get('enterprise_customer_uuid')

    def get_permission_object(self):
        """
        Retrive an EnterpriseCustomer to do auth against
        """
        return fetch_enterprise_customer_by_id(self.requested_enterprise_uuid)
