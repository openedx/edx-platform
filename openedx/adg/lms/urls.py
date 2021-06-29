"""
URLs for ADG LMS
"""
from django.conf.urls import include
from django.urls import path

from openedx.adg.lms.applications.admin import adg_admin_site

adg_url_patterns = [

    # ADG Applications app
    path('application/', include('openedx.adg.lms.applications.urls')),
    path('api/applications/', include('openedx.adg.lms.applications.api.urls', namespace='applications_api')),

    # ADG our_team app
    path('our_team/', include('openedx.adg.lms.our_team.urls')),

    # ADG webinars app
    path('webinars/', include('openedx.adg.lms.webinars.urls')),
    path('api/webinars/', include('openedx.adg.lms.webinars.api.urls', namespace='webinars_api')),
    path('adg-admin/', adg_admin_site.urls)
]
