"""
URLs for social API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import AppSecret

urlpatterns = patterns(
    'mobile_api.social.views',
    url(
        r'^app-secret/(?P<app_id>[\d]*)/$',
        AppSecret.as_view(),
        name='app-secret'
    ),
)
