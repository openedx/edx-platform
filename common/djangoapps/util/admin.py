"""Admin interface for the util app. """

from ratelimitbackend import admin
from util.models import RateLimitConfiguration


admin.site.register(RateLimitConfiguration)
