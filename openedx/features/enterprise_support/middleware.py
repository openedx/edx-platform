"""
Middleware for the Enterprise feature.

The Enterprise feature must be turned on for this middleware to have any effect.
"""

from django.core.exceptions import MiddlewareNotUsed
from django.utils.deprecation import MiddlewareMixin

from openedx.features.enterprise_support import api


class EnterpriseMiddleware(MiddlewareMixin):
    """
    Middleware that adds Enterprise-related content to the request.
    """

    def __init__(self, *args, **kwargs):
        """
        We don't need to use this middleware if the Enterprise feature isn't enabled.
        """
        if not api.enterprise_enabled():
            raise MiddlewareNotUsed()
        super(EnterpriseMiddleware, self).__init__(*args, **kwargs)

    def process_request(self, request):
        """
        Fill the request with Enterprise-related content.
        """
        if 'enterprise_customer' not in request.session and request.user.is_authenticated:
            request.session['enterprise_customer'] = api.enterprise_customer_for_request(request)
