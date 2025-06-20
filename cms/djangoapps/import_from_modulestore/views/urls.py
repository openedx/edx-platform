"""
Course to Library Import API URLs.
"""

from django.urls import include, path

from .v0 import urls as v0_urls

app_name = 'import_from_modulestore'

urlpatterns = [
    path('v0/', include(v0_urls)),
]
