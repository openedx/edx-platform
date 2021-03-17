"""
Contentstore API URLs.
"""

from django.urls import include, re_path

from .v1 import urls as v1_urls

app_name = 'cms.djangoapps.contentstore'

urlpatterns = [
    re_path(r'^v1/', include(v1_urls))
]
