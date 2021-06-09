from django.conf.urls import url
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserProfileViewSet

router = DefaultRouter()

router.register('users', UserProfileViewSet, basename='users')


urlpatterns = [
    path('adminpanel/', include(router.urls)),
    url('adminpanel/users/activate/', UserProfileViewSet.as_view({"post": "activate_users"})),
    url('adminpanel/users/deactivate/', UserProfileViewSet.as_view({"post": "deactivate_users"})),
]
