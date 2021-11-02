"""
This file contains Django middleware related to the site_configuration app.
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class SessionCookieDomainOverrideMiddleware(MiddlewareMixin):
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
                                    httponly=False, samesite=None):
                """
                Wrapper function for set_cookie() which applies SESSION_COOKIE_DOMAIN override
                """

                # only override if we are setting the cookie name to be the one the Django Session Middleware uses
                # as defined in settings.SESSION_COOKIE_NAME
                if key == configuration_helpers.get_value('SESSION_COOKIE_NAME', settings.SESSION_COOKIE_NAME):
                    domain = session_cookie_domain

                kwargs = {
                    'max_age': max_age,
                    'expires': expires,
                    'path': path,
                    'domain': domain,
                    'secure': secure,
                    'httponly': httponly,
                    'samesite': samesite
                }

                # then call down into the normal Django set_cookie method
                return response.set_cookie_wrapped_func(key, value, **kwargs)

            # then point the HttpResponse.set_cookie to point to the wrapper and keep
            # the original around
            response.set_cookie_wrapped_func = response.set_cookie
            response.set_cookie = _set_cookie_wrapper

        return response
