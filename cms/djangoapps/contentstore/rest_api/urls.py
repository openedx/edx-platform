"""
Contentstore API URLs.
"""

from django.urls import include, re_path

from .v0 import urls as v0_urls
from .v1 import urls as v1_urls

app_name = 'cms.djangoapps.contentstore'

urlpatterns = [
    re_path(r'^v0/', include(v0_urls)),
    re_path(r'^v1/', include(v1_urls)),
]
