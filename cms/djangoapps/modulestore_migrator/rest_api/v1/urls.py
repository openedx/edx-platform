"""
Course to Library Import API v1 URLs.
"""

from rest_framework.routers import SimpleRouter
from .views import MigrationViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'migrations', MigrationViewSet)

urlpatterns = ROUTER.urls
