from django.conf.urls import include, patterns, url
from rest_framework import routers
from user_api import views as user_api_views


user_api_router = routers.DefaultRouter()
user_api_router.register(r'users', user_api_views.UserViewSet)
user_api_router.register(r'user_prefs', user_api_views.UserPreferenceViewSet)
urlpatterns = patterns(
    '',
    url(r'^v1/', include(user_api_router.urls)),
)
