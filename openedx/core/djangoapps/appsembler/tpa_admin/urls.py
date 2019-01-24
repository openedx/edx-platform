from django.conf.urls import url

from openedx.core.djangoapps.appsembler.tpa_admin.api import (
    SAMLConfigurationViewSet,
    SAMLConfigurationSiteDetail,
    SAMLProviderConfigViewSet,
    SAMLProviderSiteDetail
)

saml_configuration_list = SAMLConfigurationViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

saml_configuration_detail = SAMLConfigurationViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

saml_providers_config_list = SAMLProviderConfigViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

saml_providers_config_detail = SAMLProviderConfigViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

urlpatterns = [
    # SAML Service Provider configuration
    url(r'^saml-configurations/$', saml_configuration_list, name='saml-configuration-list'),
    url(r'^saml-configurations/(?P<pk>[0-9]+)/$', saml_configuration_detail, name='saml-configuration-detail'),
    url(r'^site-saml-configuration/(?P<site_id>.+)/$', SAMLConfigurationSiteDetail.as_view()),

    # SAML Identity Providers
    url(r'^saml-providers-config/$', saml_providers_config_list, name='saml-providers-config-list'),
    url(r'^saml-providers-config/(?P<pk>[0-9]+)/$', saml_providers_config_detail, name='saml-providers-config-list'),
    url(r'^site-saml-providers/(?P<site_id>.+)/$', SAMLProviderSiteDetail.as_view()),
]
