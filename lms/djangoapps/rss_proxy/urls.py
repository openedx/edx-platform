"""
URLs for the rss_proxy djangoapp.
"""
from django.conf.urls import url


urlpatterns = [
    url(r"^$", "rss_proxy.views.proxy", name="proxy"),
]
