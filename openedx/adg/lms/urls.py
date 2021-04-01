"""
URLs for ADG LMS
"""
from django.conf.urls import include
from django.urls import path

from openedx.adg.lms.applications.admin import adg_admin_site
from openedx.adg.lms.utils.env_utils import is_testing_environment

adg_url_patterns = [

    # ADG Applications app
    path('application/', include('openedx.adg.lms.applications.urls')),
    path('api/applications/', include('openedx.adg.lms.applications.api_urls', namespace='applications_api')),
    # ADG webinars app
    path('webinars/', include('openedx.adg.lms.webinars.urls')),
    path('adg-admin/', adg_admin_site.urls)
]

if not is_testing_environment():
    adg_url_patterns.extend(
        [
            path('msp/', include('msp_assessment.msp_dashboard.urls')),
        ]
    )
