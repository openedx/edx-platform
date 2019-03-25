from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from openedx.core.djangoapps.appsembler.sites.permissions import AMCAdminPermission

from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig
from openedx.core.djangoapps.appsembler.tpa_admin.serializers import (
    SAMLConfigurationSerializer,
    SAMLProviderConfigSerializer,
)


class SAMLConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SAMLConfiguration.objects.current_set()
    serializer_class = SAMLConfigurationSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)


class SAMLConfigurationSiteDetail(generics.RetrieveAPIView):
    serializer_class = SAMLConfigurationSerializer
    lookup_field = 'site_id'

    def get_queryset(self):
        site_id = self.kwargs['site_id']
        return SAMLConfiguration.objects.current_set().filter(site__id=site_id)


class SAMLProviderConfigViewSet(viewsets.ModelViewSet):
    queryset = SAMLProviderConfig.objects.current_set()
    serializer_class = SAMLProviderConfigSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)


class SAMLProviderSiteDetail(generics.ListAPIView):
    serializer_class = SAMLProviderConfigSerializer
    lookup_field = 'site_id'

    def get_queryset(self):
        site_id = self.kwargs['site_id']
        return SAMLProviderConfig.objects.current_set().filter(site__id=site_id).order_by('-enabled')
