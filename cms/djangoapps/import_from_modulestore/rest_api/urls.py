"""
URLs for import_from_modulstore REST API
"""

from django.urls import include, path

from .v0 import urls as v0_urls

app_name = 'import_from_modulestore'

urlpatterns = [
    path('v0/', include(v0_urls)),
]
