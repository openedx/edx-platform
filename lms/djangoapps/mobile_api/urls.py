"""
URLs for mobile API
"""
from django.conf import settings
from django.conf.urls import patterns, url, include

from .users.views import my_user_info

urlpatterns = patterns(
    '',
    url(r'^users/', include('mobile_api.users.urls')),
    url(r'^my_user_info', my_user_info),
    url(r'^video_outlines/', include('mobile_api.video_outlines.urls')),
    url(r'^course_info/', include('mobile_api.course_info.urls')),
)

if settings.FEATURES["ENABLE_MOBILE_SOCIAL_FACEBOOK_FEATURES"]:
    urlpatterns += (
        url(r'^social/facebook/', include('mobile_api.social_facebook.urls')),
        url(r'^settings/', include('mobile_api.social_facebook.preferences.urls')),
    )
