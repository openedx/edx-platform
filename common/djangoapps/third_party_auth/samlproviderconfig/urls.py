from django.conf.urls import include, url
from rest_framework import routers

from .views import SAMLProviderConfigViewSet

router = routers.DefaultRouter()
router.register(r'auth/saml/v0/providerconfig', SAMLProviderConfigViewSet, basename="samlproviderconfig")
urlpatterns = router.urls
