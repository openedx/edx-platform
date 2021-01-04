"""Admin interface for the util app. """


from django.contrib import admin

from util.models import RateLimitConfiguration

admin.site.register(RateLimitConfiguration)
