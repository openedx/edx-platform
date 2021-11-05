"""
Middleware for User Authentication
"""


from django.conf import settings
from django.http import QueryDict
from django.shortcuts import redirect


class RedirectUnauthenticatedToLoginMiddleware:
    """
    Middleware that redirects unauthenticated users to login page.

    Any GET request comming from an unauthenticated user will be responded with
    a redirect to the login url. The middleware ignores requests to login and
    register pages.

    If redirects, passes the requested url to login as 'next' query string
    parameter.

    To enable the middleware, ENABLE_REDIRECT_UNAUTHENTICATED_USERS_TO_LOGIN
    setting has to be set to True.

    Assumed that the requests passed to the middleware have user attribute set.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect(request):
            return redirect(settings.LOGIN_URL + '?' + self._get_redirect_query_string(request))

        return self.get_response(request)

    def _should_redirect(self, request):
        """
        Determines if a request should be redirected to login.
        """
        if not settings.FEATURES.get('ENABLE_REDIRECT_UNAUTHENTICATED_USERS_TO_LOGIN', False):
            return False

        is_get_request = request.method == 'GET'
        is_login_or_register_url = request.path in (settings.LOGIN_URL, '/register')

        return (
            is_get_request and
            (not is_login_or_register_url) and
            (not request.user.is_authenticated)
        )

    def _get_redirect_query_string(self, request):
        """
        Generates query string for redirect.
        """
        # calling copy to get mutable QueryDict
        query = QueryDict().copy()
        query['next'] = request.get_full_path()
        return query.urlencode()
