"""
Admin module for the rss_proxy djangoapp.
"""
from django.contrib import admin
from rss_proxy.models import WhitelistedRssUrl

admin.site.register(WhitelistedRssUrl)
