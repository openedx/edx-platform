"""
Contain the middleware logic needed during pact verification
"""
from django.contrib import auth
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

User = auth.get_user_model()


class PactBypassAuthMiddleware(MiddlewareMixin):
    """
    Middleware to add default authentication into the requests for pact verification.

    This middleware is required to add a default authenticated user and bypass CSRF validation
    into the requests during the pact verification workflow. Without the authentication, the pact verification
    process will not work as the apis.
    See https://docs.pact.io/faq#how-do-i-test-oauth-or-other-security-headers
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        if not getattr(settings, 'PACT_BYPASS_AUTHENTICATION', None):
            raise MiddlewareNotUsed
        self.auth_user = User.objects.get_or_create(username='pact_staff', is_staff=True)[0]
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Add a default authenticated user and remove CSRF checks for a request
        in a subset of views.
        """
        if request.user.is_anonymous and 'Pact-Authentication' in request.headers:
            request.user = self.auth_user
            request._dont_enforce_csrf_checks = True  # pylint: disable=protected-access
