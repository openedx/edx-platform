from django.conf.urls import include, url
from rest_framework import routers

from third_party_auth.samlproviderconfig.views import SAMLProviderConfigViewSet

samlprovider_router = routers.SimpleRouter()
samlprovider_router.register(r'^auth/samlproviderconfig', SAMLProviderConfigViewSet, basename='samlproviderconfig')

urlpatterns = samlprovider_router.urls
