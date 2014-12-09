from django.conf.urls import include, patterns, url
from rest_framework import routers

from notifier_api.views import NotifierUsersViewSet


notifier_api_router = routers.DefaultRouter()
notifier_api_router.register(r'users', NotifierUsersViewSet, base_name="notifier_users")
urlpatterns = patterns(
    '',
    url(r'^v1/', include(notifier_api_router.urls)),
)
