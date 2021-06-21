"""
URLs patterns for PakX admin app
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnalyticsStats, LearnerListAPI, UserProfileViewSet

router = DefaultRouter()

router.register('users', UserProfileViewSet, basename='users')


urlpatterns = [
    path('adminpanel/', include(router.urls)),
    url('adminpanel/users/activate/', UserProfileViewSet.as_view({"post": "activate_users"})),
    url('adminpanel/users/deactivate/', UserProfileViewSet.as_view({"post": "deactivate_users"})),
    url('adminpanel/analytics/stats/', AnalyticsStats.as_view()),
    url('adminpanel/analytics/learners/', LearnerListAPI.as_view()),
]
