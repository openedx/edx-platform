"""
URLs for the Studio API app
"""

from __future__ import absolute_import

from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('cms.djangoapps.api.v1.urls', namespace='v1')),
]
