"""
URL definitions for the course_modes API.
"""
from __future__ import absolute_import

from django.conf.urls import include, url

app_name = 'common.djangoapps.course_modes.api'

urlpatterns = [
    url(r'^v1/', include('openedx.core.djangoapps.course_modes.api.v1.urls', namespace='v1')),
]
