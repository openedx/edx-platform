"""
Throttle classes for the entitlements API.
"""

from django.conf import settings
from rest_framework.throttling import UserRateThrottle


class ServiceUserThrottle(UserRateThrottle):
    """A throttle allowing service users to override rate limiting"""

    def allow_request(self, request, view):
        """Returns True if the request is coming from one of the service users
        and defaults to UserRateThrottle's configured setting otherwise.
        """
        service_users = [
            settings.SUBSCRIPTIONS_SERVICE_WORKER_USERNAME
        ]
        if request.user.username in service_users:
            return True
        return super().allow_request(request, view)
