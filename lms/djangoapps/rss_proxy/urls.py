"""
URLs for the rss_proxy djangoapp.
"""
from django.conf.urls import url

from rss_proxy.views import proxy

urlpatterns = [
    url(r'^$', proxy, name='proxy'),
]
