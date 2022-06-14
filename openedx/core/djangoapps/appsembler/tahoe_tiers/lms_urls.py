"""
URLs for the tiers app (LMS part).

CMS part is in `cms/djangoapps/appsembler_tiers/`.
"""

from django.conf.urls import url

from .lms_views import (
    LMSSiteUnavailableView,
)

urlpatterns = [
    url(r'^site-unavailable/$', LMSSiteUnavailableView.as_view(), name='lms_site_unavailable'),
]
