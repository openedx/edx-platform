"""
Urls for adg apps
"""
from django.conf.urls import include, url

adg_url_patterns = [

    # ADG Applications app
    url(
        r'^application/',
        include('openedx.adg.lms.applications.urls'),
    ),
    url(
        r'^api/applications/',
        include('openedx.adg.lms.applications.api_urls', namespace='applications_api')
    ),
]
