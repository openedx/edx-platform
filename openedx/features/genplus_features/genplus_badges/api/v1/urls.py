"""
URLs for genplus badges API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StudentProgramBadgeView,
    AwardBoosterBadgesView,
    BoosterBadgeView,
    ClassBoosterBadgeView,
)

app_name = 'genplus_badges_api_v1'

urlpatterns = [
    url(r'^program-badges/$', StudentProgramBadgeView.as_view(), name='student-program-badges'),
    url(r'^award-badges/$', AwardBoosterBadgesView.as_view(), name='assign-booster-badges'),
    url(r'^booster-badges/$', BoosterBadgeView.as_view(), name='booster-badges-view'),
    url(r'^booster-badges/student/(?P<username>\w+)/$', ClassBoosterBadgeView.as_view(), name='class-booster-badges'),
]
