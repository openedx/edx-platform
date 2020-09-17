"""
URLs for the tiers app to be included in the LMS.
"""

from django.conf.urls import url

from cms.djangoapps.appsembler_tiers.views import (
    SiteUnavailableRedirectView,
)

urlpatterns = [
    url(r'^site-unavailable/$', SiteUnavailableRedirectView.as_view(), name='site_unavailable'),
]
