"""
URL definitions for Nexblock API endpoints.
"""

from django.conf.urls import include, url

from .v0 import urls as v0_urls

app_name = "openedx.core.djangoapps.nexblocks"
urlpatterns = [
    url(r"^v0/", include(v0_urls)),
]
