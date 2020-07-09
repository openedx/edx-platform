"""
    Viewset for auth/saml/v0/samlproviderdata
"""

from edx_rbac.mixins import PermissionRequiredMixin
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from enterprise.models import EnterpriseCustomerIdentityProvider
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication

from third_party_auth.samlutils.utils import fetch_enterprise_customer_by_id

from ..models import SAMLProviderConfig, SAMLProviderData
from .serializers import SAMLProviderDataSerializer


class SAMLProviderDataMixin(object):
    authentication_classes = [JwtAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SAMLProviderDataSerializer


class SAMLProviderDataViewSet(PermissionRequiredMixin, SAMLProviderDataMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderData CRUD.
    Uses the edx-rbac mixin PermissionRequiredMixin to apply enterprise authorization

    Usage:
        [HttpVerb] /auth/saml/v0/providerdata/
    """
    permission_required = 'enterprise.can_access_admin_dashboard'

    def get_queryset(self):
        """
        Find and return the matching providerid for the given enterprise uuid
        Note: There is no direct association between samlproviderdata and enterprisecustomer.
        So we make that association in code via samlproviderdata > samlproviderconfig ( via entity_id )
        then, we fetch enterprisecustomer via samlproviderconfig > enterprisecustomer ( via association table )
        """
        enterprise_customer_idp = EnterpriseCustomerIdentityProvider.objects.get(
            enterprise_customer__uuid=self.requested_enterprise_uuid
        )
        saml_provider = SAMLProviderConfig.objects.get(pk=enterprise_customer_idp.provider_id)
        return SAMLProviderData.objects.filter(entity_id=saml_provider.entity_id)

    @property
    def requested_enterprise_uuid(self):
        return self.request.query_params.get('enterprise_customer_uuid')

    def get_permission_object(self):
        """
        Retrive an EnterpriseCustomer to do auth against
        """
        return fetch_enterprise_customer_by_id(self.requested_enterprise_uuid)
