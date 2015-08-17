"""
URLs for users sharing preferences
"""
from django.conf.urls import patterns, url
from .views import UserSharing

urlpatterns = patterns(
    'mobile_api.social_facebook.preferences.views',
    url(
        r'^preferences/$',
        UserSharing.as_view(),
        name='preferences'
    ),
)
