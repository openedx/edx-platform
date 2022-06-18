"""
Middleware to ensure best practices of DRF and other endpoints.
"""
import warnings

from django.utils.deprecation import MiddlewareMixin
from edx_django_utils import monitoring
from edx_django_utils.cache import DEFAULT_REQUEST_CACHE

from edx_rest_framework_extensions.auth.jwt.constants import USE_JWT_COOKIE_HEADER
from edx_rest_framework_extensions.auth.jwt.cookies import jwt_cookie_name


class RequestCustomAttributesMiddleware(MiddlewareMixin):
    """
    Adds various request related custom attributes.

    Possible custom attributes include:
        request_authenticated_user_set_in_middleware:
            Example values: 'process_request', 'process_view', 'process_response',
            or 'process_exception'. Attribute won't exist if user is not authenticated.
        request_auth_type_guess: Example values include: no-user, unauthenticated,
            jwt, bearer, other-token-type, jwt-cookie, or session-or-other
            Note: These are just guesses because if a token was expired, for example,
              the user could have been authenticated by some other means.
        request_client_name: The client name from edx-rest-api-client calls.
        request_referer
        request_user_agent: The user agent string from the request header.
        request_user_id: The user id of the request user.
        request_is_staff_or_superuser: `staff` or `superuser` depending on whether the
            user in the request is a django staff or superuser.

    This middleware is dependent on the RequestCacheMiddleware. You must
    include this middleware later.  For example::

        MIDDLEWARE = (
            'edx_django_utils.cache.middleware.RequestCacheMiddleware',
            'edx_rest_framework_extensions.middleware.RequestCustomAttributesMiddleware',
        )

    This middleware should also appear after any authentication middleware.

    """
    def process_request(self, request):
        """
        Caches if authenticated user was found.
        """
        self._cache_if_authenticated_user_found_in_middleware(request, 'process_request')

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Caches if authenticated user was found.
        """
        self._cache_if_authenticated_user_found_in_middleware(request, 'process_view')

    def process_response(self, request, response):
        """
        Add custom attributes for various details of the request.
        """
        self._cache_if_authenticated_user_found_in_middleware(request, 'process_response')
        self._set_all_request_attributes(request)
        return response

    def process_exception(self, request, exception):  # pylint: disable=unused-argument
        """
        Django middleware handler to process an exception
        """
        self._cache_if_authenticated_user_found_in_middleware(request, 'process_exception')
        self._set_all_request_attributes(request)

    def _set_all_request_attributes(self, request):
        """
        Sets all the request custom attributes
        """
        self._set_request_auth_type_guess_attribute(request)
        self._set_request_user_agent_attributes(request)
        self._set_request_referer_attribute(request)
        self._set_request_user_id_attribute(request)
        self._set_request_authenticated_user_found_in_middleware_attribute()
        self._set_request_is_staff_or_superuser(request)

    def _set_request_is_staff_or_superuser(self, request):
        """
        Add `request_is_staff_or_superuser` custom attribute.

        Custom Attributes:
            request_is_staff_or_superuser
        """
        value = None
        if hasattr(request, 'user') and request.user:
            if request.user.is_superuser:
                value = 'superuser'
            elif request.user.is_staff:
                value = 'staff'

            if value:
                monitoring.set_custom_attribute('request_is_staff_or_superuser', value)

    def _set_request_user_id_attribute(self, request):
        """
        Add request_user_id custom attribute

        Custom Attributes:
             request_user_id
        """
        if hasattr(request, 'user') and hasattr(request.user, 'id') and request.user.id:
            monitoring.set_custom_attribute('request_user_id', request.user.id)

    def _set_request_referer_attribute(self, request):
        """
        Add custom attribute 'request_referer' for http referer.
        """
        if 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER']:
            monitoring.set_custom_attribute('request_referer', request.META['HTTP_REFERER'])

    def _set_request_user_agent_attributes(self, request):
        """
        Add custom attributes for user agent for python.

        Custom Attributes:
             request_user_agent
             request_client_name: The client name from edx-rest-api-client calls.
        """
        if 'HTTP_USER_AGENT' in request.META and request.META['HTTP_USER_AGENT']:
            user_agent = request.META['HTTP_USER_AGENT']
            monitoring.set_custom_attribute('request_user_agent', user_agent)
            if user_agent:
                # Example agent string from edx-rest-api-client:
                #    python-requests/2.9.1 edx-rest-api-client/1.7.2 ecommerce
                #    See https://github.com/edx/edx-rest-api-client/commit/692903c30b157f7a4edabc2f53aae1742db3a019
                user_agent_parts = user_agent.split()
                if len(user_agent_parts) == 3 and user_agent_parts[1].startswith('edx-rest-api-client/'):
                    monitoring.set_custom_attribute('request_client_name', user_agent_parts[2])

    def _set_request_auth_type_guess_attribute(self, request):
        """
        Add custom attribute 'request_auth_type_guess' for the authentication type used.

        NOTE: This is a best guess at this point.  Possible values include:
            no-user
            unauthenticated
            jwt/bearer/other-token-type
            jwt-cookie
            session-or-other (catch all)

        """
        if not hasattr(request, 'user') or not request.user:
            auth_type = 'no-user'
        elif not request.user.is_authenticated:
            auth_type = 'unauthenticated'
        elif 'HTTP_AUTHORIZATION' in request.META and request.META['HTTP_AUTHORIZATION']:
            token_parts = request.META['HTTP_AUTHORIZATION'].split()
            # Example: "JWT eyJhbGciO..."
            if len(token_parts) == 2:
                auth_type = token_parts[0].lower()  # 'jwt' or 'bearer' (for example)
            else:
                auth_type = 'other-token-type'
        elif USE_JWT_COOKIE_HEADER in request.META and jwt_cookie_name() in request.COOKIES:
            auth_type = 'jwt-cookie'
        else:
            auth_type = 'session-or-other'
        monitoring.set_custom_attribute('request_auth_type_guess', auth_type)

    AUTHENTICATED_USER_FOUND_CACHE_KEY = 'edx-drf-extensions.authenticated_user_found_in_middleware'

    def _set_request_authenticated_user_found_in_middleware_attribute(self):
        """
        Add custom attribute 'request_authenticated_user_found_in_middleware' if authenticated user was found.
        """
        cached_response = DEFAULT_REQUEST_CACHE.get_cached_response(self.AUTHENTICATED_USER_FOUND_CACHE_KEY)
        if cached_response.is_found:
            monitoring.set_custom_attribute(
                'request_authenticated_user_found_in_middleware',
                cached_response.value
            )

    def _cache_if_authenticated_user_found_in_middleware(self, request, value):
        """
        Updates the cached process step in which the authenticated user was found, if it hasn't already been found.
        """
        cached_response = DEFAULT_REQUEST_CACHE.get_cached_response(self.AUTHENTICATED_USER_FOUND_CACHE_KEY)
        if cached_response.is_found:
            # since we are tracking the earliest point the authenticated user was found,
            # and the value was already set in earlier middleware step, do not set again.
            return

        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            DEFAULT_REQUEST_CACHE.set(self.AUTHENTICATED_USER_FOUND_CACHE_KEY, value)


class RequestMetricsMiddleware(RequestCustomAttributesMiddleware):
    """
    Deprecated class for handling middleware. Class has been renamed to RequestCustomAttributesMiddleware.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        msg = "Use 'RequestCustomAttributesMiddleware' in place of 'RequestMetricsMiddleware'."
        warnings.warn(msg, DeprecationWarning)
