"""Tahoe API main URL patterns

Use this URL handler module to manage versioned Tahoe APIs
"""

from django.conf.urls import include, url

from openedx.core.djangoapps.appsembler.api.v1 import urls as v1_urls
from openedx.core.djangoapps.appsembler.api.v2 import urls as v2_urls


urlpatterns = [
    url(r'^v1/', include((v1_urls, 'v1'), namespace='v1')),
    url(r'^v2/', include((v2_urls, 'v2'), namespace='v2'))
]
