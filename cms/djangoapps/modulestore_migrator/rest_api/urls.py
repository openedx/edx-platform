"""
Course to Library Import API URLs.
"""

from django.urls import include, path

from .v0 import urls as v0_urls

app_name = 'modulestore_migrator'

urlpatterns = [
    path('v0/', include(v0_urls)),
]
