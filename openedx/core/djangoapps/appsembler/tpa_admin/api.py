"""

TODO: We should move the views here to the tpa_admin.views module to adhere to
standard practices
"""
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from openedx.core.djangoapps.appsembler.sites.permissions import AMCAdminPermission

from openedx.core.lib.api.authentication import (
    BearerAuthenticationAllowInactiveUser,
)
from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig
from openedx.core.djangoapps.appsembler.tpa_admin.serializers import (
    SAMLConfigurationSerializer,
    SAMLProviderConfigSerializer,
)
from openedx.core.djangoapps.appsembler.tpa_admin.filters import (
    SAMLConfigurationFilter,
    SAMLProviderConfigFilter,
)


class SAMLConfigurationViewSet(viewsets.ModelViewSet):
    model = SAMLConfiguration
    queryset = SAMLConfiguration.objects.current_set().order_by('id')
    serializer_class = SAMLConfigurationSerializer
    authentication_classes = (BearerAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)
    filterset_class = SAMLConfigurationFilter


class SAMLConfigurationSiteDetail(generics.RetrieveAPIView):
    """
    We may not need this view as SAMLConfigurationViewSet provides filtering
    by site id with following endpoint and query param

    ```
    saml-configurations/?site_id=<site_id>
    ```
    """
    serializer_class = SAMLConfigurationSerializer
    lookup_field = 'site_id'

    def get_queryset(self):
        site_id = self.kwargs['site_id']
        return SAMLConfiguration.objects.current_set().filter(site_id=site_id)


class SAMLProviderConfigViewSet(viewsets.ModelViewSet):
    queryset = SAMLProviderConfig.objects.current_set().order_by('id')
    serializer_class = SAMLProviderConfigSerializer
    authentication_classes = (BearerAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)
    filterset_class = SAMLProviderConfigFilter


class SAMLProviderSiteDetail(generics.ListAPIView):
    """
    We may not need this view as SAMLProviderConfigViewSet provides filtering
    by site id with following endpoint and query param

    ```
    saml-provider-config/?site_id=<site_id>
    ```
    """
    serializer_class = SAMLProviderConfigSerializer
    lookup_field = 'site_id'

    def get_queryset(self):
        site_id = self.kwargs['site_id']
        return SAMLProviderConfig.objects.current_set().filter(
            site__id=site_id).order_by('-enabled')
