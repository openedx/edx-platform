"""
Labster API URI specification.

Patterns here should simply point to version-specific patterns.
"""
from django.conf.urls import patterns, url
from django.conf import settings
from labster_enroll.views import ccx_invite


urlpatterns = patterns(
    '',
    url(
        r'^course/{}/enroll/?$'.format(settings.COURSE_ID_PATTERN), ccx_invite, name='labster_ccx_invite'
    )
)
