"""
Urls for pakx cms apps
"""
from django.conf.urls import include, url

pakx_url_patterns = [

    # URL for custom_settings app
    url(r'', include('openedx.features.pakx.cms.custom_settings.urls')),

]
