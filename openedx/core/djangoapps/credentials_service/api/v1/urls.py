"""
URLs for the credentials service APIs.
"""
from django.conf.urls import patterns, url, include
from openedx.core.djangoapps.credentials_service.api.v1 import views
from openedx.core.djangoapps.credit import routers


router = routers.SimpleRouter()  # pylint: disable=invalid-name
router.register(r'users', views.UserCredentialViewSet,  base_name='users_credentials')

V1_URLS = router.urls

urlpatterns = patterns(
    '',
    url(r'^', include(V1_URLS)),
)
