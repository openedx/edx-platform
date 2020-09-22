"""
URLs for the rss_proxy djangoapp.
"""


from django.conf.urls import url

from .views import proxy

app_name = 'rss_proxy'
urlpatterns = [
    url(r'^$', proxy, name='proxy'),
]
