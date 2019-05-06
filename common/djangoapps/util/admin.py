"""Admin interface for the util app. """

from __future__ import absolute_import

from django.contrib import admin

from util.models import RateLimitConfiguration

admin.site.register(RateLimitConfiguration)
