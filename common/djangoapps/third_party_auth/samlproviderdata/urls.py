from django.conf.urls import include, url
from rest_framework import routers

from .views import SAMLProviderDataViewSet

router = routers.DefaultRouter()
router.register(r'auth/saml/v0/providerdata', SAMLProviderDataViewSet, basename="samlproviderdata")
urlpatterns = router.urls
