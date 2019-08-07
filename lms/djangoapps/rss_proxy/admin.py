"""
Admin module for the rss_proxy djangoapp.
"""
from __future__ import absolute_import

from django.contrib import admin

from rss_proxy.models import WhitelistedRssUrl

admin.site.register(WhitelistedRssUrl)
