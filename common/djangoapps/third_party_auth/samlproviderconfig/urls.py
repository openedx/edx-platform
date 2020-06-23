"""
    Viewset for auth/saml/v0/providerconfig/
"""

from rest_framework import routers

from .views import SAMLProviderConfigViewSet

samlproviderconfig_router = routers.DefaultRouter()
samlproviderconfig_router.register(r'providerconfig', SAMLProviderConfigViewSet, basename="samlproviderconfig")
urlpatterns = samlproviderconfig_router.urls
