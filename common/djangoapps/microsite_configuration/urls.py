from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from .api import MicrositeViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'microsites', MicrositeViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
]
