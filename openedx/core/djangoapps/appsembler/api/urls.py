"""Tahoe API main URL patterns

Use this URL handler module to manage versioned Tahoe APIs
"""

from django.conf.urls import include, url

from openedx.core.djangoapps.appsembler.api.v1 import urls as v1_urls


urlpatterns = [
    url(r'^v1/', include((v1_urls, 'v1'), namespace='v1')),
]
