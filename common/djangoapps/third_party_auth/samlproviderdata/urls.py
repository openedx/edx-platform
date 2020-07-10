"""
    url mappings for auth/saml/v0/providerdata/
"""

from rest_framework import routers

from .views import SAMLProviderDataViewSet

samlproviderdata_router = routers.DefaultRouter()
samlproviderdata_router.register(r'providerdata', SAMLProviderDataViewSet, basename="samlproviderdata")
urlpatterns = samlproviderdata_router.urls
