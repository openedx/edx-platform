"""
URLs for the credentials support in LMS and Studio.
"""
from django.conf.urls import patterns, url, include


urlpatterns = patterns(
    '',
    url(r'^v1/', include('openedx.core.djangoapps.credentials.api.urls')),
)
