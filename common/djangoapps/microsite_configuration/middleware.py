"""
This file implements the Middleware support for the Open edX platform.
A microsite enables the following features:

1) Mapping of sub-domain name to a 'brand', e.g. foo-university.edx.org
2) Present a landing page with a listing of courses that are specific to the 'brand'
3) Ability to swap out some branding elements in the website
"""

from django.conf import settings
from microsite_configuration import microsite


class MicrositeMiddleware(object):
    """
    Middleware class which will bind configuration information regarding 'microsites' on a per request basis.
    The actual configuration information is taken from Django settings information
    """

    def process_request(self, request):
        """
        Middleware entry point on every request processing. This will associate a request's domain name
        with a 'University' and any corresponding microsite configuration information
        """
        microsite.clear()

        domain = request.META.get('HTTP_HOST', None)

        microsite.set_by_domain(domain)

        return None

    def process_response(self, request, response):
        """
        Middleware entry point for request completion.
        """
        microsite.clear()
        return response


class MicrositeSessionCookieDomainMiddleware():
    """
    Special case middleware which should be at the very end of the MIDDLEWARE list (so that it runs first
    on the process_response chain). This middleware will define a wrapper function for the set_cookie() function
    on the HttpResponse object, if the request is running in a middleware.

    This wrapped set_cookie will change the SESSION_COOKIE_DOMAIN setting so that the cookie can be bound to a
    fully customized URL.
    """

    def process_response(self, request, response):
        """
        Standard Middleware entry point
        """

        # See if we are running in a Microsite *AND* we have a custom SESSION_COOKIE_DOMAIN defined
        # in configuration
        if microsite.has_override_value('SESSION_COOKIE_DOMAIN'):

            # define wrapper function for the standard set_cookie()
            def _set_cookie_wrapper(key, value='', max_age=None, expires=None, path='/', domain=None, secure=None, httponly=False):

                # only override if we are setting the cookie name to be the one the Django Session Middleware uses
                # as defined in settings.SESSION_COOKIE_NAME
                if key == settings.SESSION_COOKIE_NAME:
                    domain = microsite.get_value('SESSION_COOKIE_DOMAIN', domain)

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
