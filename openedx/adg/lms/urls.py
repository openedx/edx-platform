"""
Urls for adg apps
"""
from django.conf.urls import include, url
from django.urls import path

from openedx.adg.lms.applications.admin import adg_admin_site

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
    path('adg-admin/', adg_admin_site.urls)
]
