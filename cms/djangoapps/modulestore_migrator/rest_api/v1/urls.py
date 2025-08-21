"""
Course to Library Import API v1 URLs.
"""

from rest_framework.routers import SimpleRouter
from .views import ImportViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'migrations', ImportViewSet)

urlpatterns = ROUTER.urls
