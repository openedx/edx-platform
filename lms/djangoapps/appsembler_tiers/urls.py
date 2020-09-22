"""
URLs for the tiers app (LMS part).
"""

from django.conf.urls import url

from lms.djangoapps.appsembler_tiers.views import (
    SiteUnavailableView,
)

urlpatterns = [
    url(r'^site-unavailable/$', SiteUnavailableView.as_view(), name='site_unavailable'),
]
