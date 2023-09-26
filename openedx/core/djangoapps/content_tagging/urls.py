"""
Content Tagging URLs
"""
from django.urls import path, include

from .rest_api import urls

urlpatterns = [
    path('', include(urls)),
]
