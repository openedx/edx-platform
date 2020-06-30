"""
    Viewset for auth/saml/v0/providerconfig/
"""

from rest_framework import routers

from .views import SAMLProviderConfigViewSet

router = routers.DefaultRouter()
router.register(r'auth/saml/v0/providerconfig', SAMLProviderConfigViewSet, basename="samlproviderconfig")
urlpatterns = router.urls
