"""
user manager API URLs
"""
from django.conf.urls import include, url

from .v1 import urls

urlpatterns = [
    url(r'^v1/', include(urls, namespace='v1')),
]
