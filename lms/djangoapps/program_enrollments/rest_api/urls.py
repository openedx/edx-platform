"""
Program Enrollment API URLs.
"""

from __future__ import absolute_import

from django.conf.urls import include, url

from .v1 import urls as v1_urls

app_name = 'lms.djangoapps.program_enrollments'

urlpatterns = [
    url(r'^v1/', include(v1_urls))
]
