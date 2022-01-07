"""
URLs for the rss_proxy djangoapp.
"""


from django.urls import path

from .views import proxy

app_name = 'rss_proxy'
urlpatterns = [
    path('', proxy, name='proxy'),
]
