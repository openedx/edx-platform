"""
Course to Library Import API v0 URLs.
"""

from rest_framework.routers import SimpleRouter
# from .views import ImportViewSet  # @@TODO - re-anble this once API is fixed

ROUTER = SimpleRouter()
# ROUTER.register(r'imports', ImportViewSet)

urlpatterns = ROUTER.urls
