"""
URLs for social API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import Social 

urlpatterns = patterns(
    'mobile_api.social.views',
    url(
        r'^{}/app-secret',
        Social.as_view(),
        name='app-secret'
    ),
)
