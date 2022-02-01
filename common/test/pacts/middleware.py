"""
Contains the middleware logic needed during pact verification
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from common.djangoapps.student.tests.factories import UserFactory


class AuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to add default authentication into the requests for pact verification.

    This middleware is required to add a default authenticated user and bypass CSRF validation
    into the requests during the pact verification workflow. Without the authentication, the pact verification
    process will not work as the apis.
    See https://docs.pact.io/faq#how-do-i-test-oauth-or-other-security-headers
    """
    def __init__(self, get_response):
        super().__init__()

        username = getattr(settings, 'MOCK_USERNAME', 'Mock User')
        self.auth_user = UserFactory.create(username=username)
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Add a default authenticated user and remove CSRF checks for a pact request
        """
        if request.user.is_anonymous and 'Pact-Authentication' in request.headers:
            request.user = self.auth_user
            request._dont_enforce_csrf_checks = True  # pylint: disable=protected-access
