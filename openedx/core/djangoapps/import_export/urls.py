"""
URLs for the public API
"""
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    # Import/Export API
    url(
        r'^courses/',
        include('openedx.core.djangoapps.import_export.courses.urls')
    ),
)
