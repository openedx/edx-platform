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
    StudentBoosterBadgeView,
    StudentActiveProgramBadgesView,
)

app_name = 'genplus_badges_api_v1'

urlpatterns = [
    url(r'^program-badges/$', StudentProgramBadgeView.as_view(), name='student-program-badges'),
    url(r'^active/program-badges/$', StudentActiveProgramBadgesView.as_view(), name='student-active-program-badges'),
    url(r'^award-badges/$', AwardBoosterBadgesView.as_view(), name='assign-booster-badges'),
    url(r'^booster-badges/$', BoosterBadgeView.as_view(), name='booster-badges-view'),
    url(r'^booster-badges/student/$', StudentBoosterBadgeView.as_view(), name='student-booster-badges'),
]
