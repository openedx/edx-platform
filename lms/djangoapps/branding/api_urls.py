"""
Branding API endpoint urls.
"""

from __future__ import absolute_import

from django.conf.urls import url

from branding.views import footer

urlpatterns = [
    url(r"^footer$", footer, name="branding_footer"),
]
