"""
URLs for genplus badges API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StudentProgramBadgeView
)

app_name = 'genplus_badges_api_v1'


urlpatterns = [
    url('^program-badges/$', StudentProgramBadgeView.as_view(), name='student-program-badges'),
]
