"""
URLs for the rss_proxy djangoapp.
"""

from .views import proxy
from django.urls import path

app_name = 'rss_proxy'
urlpatterns = [
    path('', proxy, name='proxy'),
]
