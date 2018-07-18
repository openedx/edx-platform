"""Admin interface for the util app. """

from django.contrib import admin

from common_utils.models import RateLimitConfiguration

admin.site.register(RateLimitConfiguration)
