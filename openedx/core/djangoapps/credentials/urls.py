"""
URLs for the credentials support in LMS and Studio.
"""

from django.conf.urls import patterns, url
from openedx.core.djangoapps.credentials.api.v1.views import generate_program_credential

urlpatterns = patterns('',
    url(r'^v1/user-credentials/$', generate_program_credential),
)
