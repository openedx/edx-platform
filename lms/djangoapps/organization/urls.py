"""
URLS for organizations end points.
"""
# pylint: disable=invalid-name
from rest_framework import routers

from .views import PlatformOrganizationsViewSet

router = routers.SimpleRouter()
router.register(r'v0/organizations', PlatformOrganizationsViewSet)

urlpatterns = router.urls
