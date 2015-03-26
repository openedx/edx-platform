"""
A utility class which wraps the RateLimitMixin 3rd party class to do bad request counting
which can be used for rate limiting
"""
from ratelimitbackend.backends import RateLimitMixin


class BadRequestRateLimiter(RateLimitMixin):
    """
    Use the 3rd party RateLimitMixin to help do rate limiting on the Password Reset flows
    """

    def is_rate_limit_exceeded(self, request):
        """
        Returns if the client has been rated limited
        """
        counts = self.get_counters(request)
        return sum(counts.values()) >= self.requests

    def tick_bad_request_counter(self, request):
        """
        Ticks any counters used to compute when rate limt has been reached
        """
        self.cache_incr(self.get_cache_key(request))
