"""
This file contains Django middleware related to the site_configuration app.
"""

from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.contrib.auth.decorators import login_required
from django.conf import settings
from re import compile


class SessionCookieDomainOverrideMiddleware(object):
    """
    Special case middleware which should be at the very end of the MIDDLEWARE list (so that it runs first
    on the process_response chain). This middleware will define a wrapper function for the set_cookie() function
    on the HttpResponse object, if the request is running in a middleware.

    This wrapped set_cookie will change the SESSION_COOKIE_DOMAIN setting so that the cookie can be bound to a
    fully customized URL.
    """

    def process_response(self, __, response):
        """
        Django middleware hook for process responses
        """

        # Check for SESSION_COOKIE_DOMAIN setting override
        session_cookie_domain = configuration_helpers.get_value('SESSION_COOKIE_DOMAIN')
        if session_cookie_domain:
            def _set_cookie_wrapper(key, value='', max_age=None, expires=None, path='/', domain=None, secure=None,
                                    httponly=False):
                """
                Wrapper function for set_cookie() which applies SESSION_COOKIE_DOMAIN override
                """

                # only override if we are setting the cookie name to be the one the Django Session Middleware uses
                # as defined in settings.SESSION_COOKIE_NAME
                if key == configuration_helpers.get_value('SESSION_COOKIE_NAME', settings.SESSION_COOKIE_NAME):
                    domain = session_cookie_domain

                # then call down into the normal Django set_cookie method
                return response.set_cookie_wrapped_func(
                    key,
                    value,
                    max_age=max_age,
                    expires=expires,
                    path=path,
                    domain=domain,
                    secure=secure,
                    httponly=httponly
                )

            # then point the HttpResponse.set_cookie to point to the wrapper and keep
            # the original around
            response.set_cookie_wrapped_func = response.set_cookie
            response.set_cookie = _set_cookie_wrapper

        return response

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from any urls.py).
    """

    def __init__(self):
        self.LOGIN_URL = settings.LOGIN_URL or '/login/'
        self.LOGIN_EXEMPT_URLS = list()

        # Needed for user to be able to login at all
        self.DEFAULT_LOGIN_EXEMPT_URLS = [
            r'^user_api/v1/account/.*$',
            r'^auth/.*$',
            r'^register.*$',
            r'^create_account.*$',
            r'^admin.*$'
        ]
        self.RESTRICT_SITE_TO_LOGGED_IN_USERS = None
        self.EXEMPT_URLS = [compile(self.LOGIN_URL.lstrip('/'))]

    def process_view(self, request, view_func, view_args, view_kwargs):

        '''
        If the site is configured to restrict not logged in users to the LOGIN_EXEMPT_URLS
        from accessing pages, wrap the next view with the django login_required middleware
        '''

        if request.user.is_authenticated():
            return None

        self.RESTRICT_SITE_TO_LOGGED_IN_USERS = self.RESTRICT_SITE_TO_LOGGED_IN_USERS or configuration_helpers.get_value(
            'RESTRICT_SITE_TO_LOGGED_IN_USERS',
            settings.FEATURES.get('RESTRICT_SITE_TO_LOGGED_IN_USERS', False)
        )

        if self.RESTRICT_SITE_TO_LOGGED_IN_USERS:
            self.LOGIN_EXEMPT_URLS = self.LOGIN_EXEMPT_URLS or configuration_helpers.get_value(
                'LOGIN_EXEMPT_URLS',
                settings.FEATURES.get('LOGIN_EXEMPT_URLS', None)
            )

            if self.LOGIN_EXEMPT_URLS:
                if type(self.LOGIN_EXEMPT_URLS) is str or type(self.LOGIN_EXEMPT_URLS) is unicode:
                    self.LOGIN_EXEMPT_URLS = [self.LOGIN_EXEMPT_URLS]
                self.EXEMPT_URLS += [compile(expr) for expr in self.LOGIN_EXEMPT_URLS + self.DEFAULT_LOGIN_EXEMPT_URLS]
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in self.EXEMPT_URLS):
                return login_required(view_func)(request, view_args, view_kwargs)

        return None
