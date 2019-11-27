"""
A utility class which wraps the RateLimitMixin 3rd party class to do bad request counting
which can be used for rate limiting
"""
from __future__ import absolute_import

from django.conf import settings
from ratelimitbackend.backends import RateLimitMixin


class RequestRateLimiter(RateLimitMixin):
    """
    Use the 3rd party RateLimitMixin to help do rate limiting.
    """
    def is_rate_limit_exceeded(self, request):
        """
        Returns if the client has been rated limited
        """
        counts = self.get_counters(request)
        return sum(counts.values()) >= self.requests

    def tick_request_counter(self, request):
        """
        Ticks any counters used to compute when rate limt has been reached
        """
        self.cache_incr(self.get_cache_key(request))


class BadRequestRateLimiter(RequestRateLimiter):
    """
    Default rate limit is 30 requests for every 5 minutes.
    """
    pass


class PasswordResetEmailRateLimiter(RequestRateLimiter):
    """
    Rate limiting requests to send password reset emails.
    """
    email_rate_limit = getattr(settings, 'PASSWORD_RESET_EMAIL_RATE_LIMIT', {})
    requests = email_rate_limit.get('no_of_emails', 1)
    cache_timeout_seconds = email_rate_limit.get('per_seconds', 60)
    reset_email_cache_prefix = 'resetemail'

    def key(self, request, dt):
        """
        Returns cache key.
        """
        return '%s-%s-%s' % (
            self.reset_email_cache_prefix,
            self.get_ip(request),
            dt.strftime('%Y%m%d%H%M'),
        )

    def expire_after(self):
        """
        Returns timeout for cache keys.
        """
        return self.cache_timeout_seconds
