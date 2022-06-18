"""
URL definitions for version 1 of the CSRF API.
"""

from django.urls import re_path

from .views import CsrfTokenView


urlpatterns = [
    re_path(r'^token$', CsrfTokenView.as_view(), name='csrf_token'),
]
