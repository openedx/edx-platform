"""
CCX API URLs.
"""
from __future__ import absolute_import

from django.conf.urls import include, url

app_name = 'ccx_api'
urlpatterns = [
    url(r'^v0/', include('lms.djangoapps.ccx.api.v0.urls')),
]
