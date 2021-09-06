"""
"""
from django.urls import include, path
from rest_framework import routers

from openedx.core.djangoapps.appsembler.tpa_admin.api import (
    SAMLConfigurationViewSet,
    SAMLConfigurationSiteDetail,
    SAMLProviderConfigViewSet,
    SAMLProviderSiteDetail
)

router = routers.DefaultRouter()

# Register SAML service providers configuration endpoint
router.register(r'saml-configurations',
                SAMLConfigurationViewSet,
                basename='saml-configuration')

# Register SAML identity providers endpoint
router.register(r'saml-providers-config',
                SAMLProviderConfigViewSet,
                basename='saml-providers-config')

urlpatterns = [
    path('site-saml-configuration/<int:site_id>/',
         SAMLConfigurationSiteDetail.as_view(),
         name='site-saml-configuration'),
    path('site-saml-providers/<int:site_id>/',
         SAMLProviderSiteDetail.as_view(),
         name='site-saml-provider'),
    path('', include(router.urls, )),
]
