"""
Course Metadata API URI specification.

Patterns here are further-directed to version-specific patterns, where applicable
"""
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v0/', include('course_metadata_api.v0.urls', namespace='v0'))
)
