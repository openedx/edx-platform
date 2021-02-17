"""
Urls for pakx lms apps
"""
from django.conf.urls import include, url

pakx_url_patterns = [

    # URL for overrides app
    url(r'', include('openedx.features.pakx.lms.overrides.urls')),

]
