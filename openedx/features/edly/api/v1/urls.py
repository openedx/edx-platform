from rest_framework import routers

from openedx.features.edly.api.v1.views.user_sites import UserSitesViewSet

router = routers.SimpleRouter()
router.register(r'user_sites', UserSitesViewSet, base_name='user_sites')

urlpatterns = router.urls
