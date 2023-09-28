"""
Admin module for the rss_proxy djangoapp.
"""


from django.contrib import admin

from lms.djangoapps.rss_proxy.models import WhitelistedRssUrl

admin.site.register(WhitelistedRssUrl)
