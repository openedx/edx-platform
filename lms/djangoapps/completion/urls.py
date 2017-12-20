"""
URL configuration for the completion API
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('lms.djangoapps.completion.api.v1.urls', namespace='completion_api_v1')),
]
