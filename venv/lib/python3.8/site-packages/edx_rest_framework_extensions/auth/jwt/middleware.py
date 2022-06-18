"""
Middleware supporting JWT Authentication.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.middleware import get_user
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from edx_django_utils import monitoring
from edx_django_utils.cache import RequestCache
from rest_framework.permissions import OperandHolder, SingleOperandHolder
from rest_framework.request import Request
from rest_framework.settings import api_settings
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from edx_rest_framework_extensions.auth.jwt.constants import (
    JWT_DELIMITER,
    USE_JWT_COOKIE_HEADER,
)
from edx_rest_framework_extensions.auth.jwt.cookies import (
    jwt_cookie_header_payload_name,
    jwt_cookie_name,
    jwt_cookie_signature_name,
)
from edx_rest_framework_extensions.config import ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE
from edx_rest_framework_extensions.permissions import (
    LoginRedirectIfUnauthenticated,
    NotJwtRestrictedApplication,
)
from edx_rest_framework_extensions.settings import get_setting


log = logging.getLogger(__name__)


class EnsureJWTAuthSettingsMiddleware(MiddlewareMixin):
    """
    Django middleware object that ensures the proper Permission classes
    are set on all endpoints that use JWTAuthentication.
    """
    _required_permission_classes = (NotJwtRestrictedApplication,)

    def _iter_included_base_classes(self, view_permissions):
        """
        Yield all the permissions that are encapsulated in provided view_permissions, directly or as
        a part of DRF's composed permissions.
        """
        # Not all permissions are classes, some will be OperandHolder
        # objects from DRF. So we have to crawl all those and expand them to see
        # if our target classes are inside the conditionals somewhere.
        for permission in view_permissions:
            # Composition using DRF native support in 3.9+:
            # IsStaff | IsSuperuser -> [IsStaff, IsSuperuser]
            # IsOwner | IsStaff | IsSuperuser -> [IsOwner | IsStaff, IsSuperuser]
            if isinstance(permission, OperandHolder):
                decomposed_permissions = [permission.op1_class, permission.op2_class]
                yield from self._iter_included_base_classes(decomposed_permissions)
            elif isinstance(permission, SingleOperandHolder):
                yield permission.op1_class
            else:
                yield permission

    def _add_missing_jwt_permission_classes(self, view_class):
        """
        Adds permissions classes that should exist for Jwt based authentication,
        if needed.
        """
        classes_to_add = []
        view_permissions = list(getattr(view_class, 'permission_classes', []))

        for perm_class in self._required_permission_classes:
            if not _includes_base_class(self._iter_included_base_classes(view_permissions), perm_class):
                message = (
                    "The view %s allows Jwt Authentication. The required permission class, %s,",
                    " was automatically added."
                )
                log.info(
                    message,
                    view_class.__name__,
                    perm_class.__name__,
                )
                classes_to_add.append(perm_class)

        if classes_to_add:
            view_class.permission_classes += tuple(classes_to_add)

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        view_class = _get_view_class(view_func)

        view_authentication_classes = getattr(view_class, 'authentication_classes', tuple())
        if _includes_base_class(view_authentication_classes, JSONWebTokenAuthentication):
            self._add_missing_jwt_permission_classes(view_class)


class JwtRedirectToLoginIfUnauthenticatedMiddleware(MiddlewareMixin):
    """
    Middleware enables the DRF JwtAuthentication authentication class for endpoints
    using the LoginRedirectIfUnauthenticated permission class.

    Enables a DRF view to redirect the user to login when they are unauthenticated.
    It automatically enables JWT-cookie-based authentication by setting the
    `USE_JWT_COOKIE_HEADER` for endpoints using the LoginRedirectIfUnauthenticated
    permission.

    This can be used to convert a plain Django view using @login_required into a
    DRF APIView, which is useful to enable our DRF JwtAuthentication class.

    Usage Notes:
    - This middleware must be added before JwtAuthCookieMiddleware.
    - Only affects endpoints using the LoginRedirectIfUnauthenticated permission class.

    See https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0009-jwt-in-session-cookie.rst  # noqa E501 line too long
    """
    def get_login_url(self, request):  # pylint: disable=unused-argument
        """
        Return None for default login url.

        Can be overridden for slow-rollout or A/B testing of transition to other login mechanisms.
        """
        return None

    def is_jwt_auth_enabled_with_login_required(self, request, view_func):  # pylint: disable=unused-argument
        """
        Returns True if JwtAuthentication is enabled with the LoginRedirectIfUnauthenticated permission class.

        Can be overridden for slow roll-out or A/B testing.
        """
        return self._is_login_required_found()

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Enables Jwt Authentication for endpoints using the LoginRedirectIfUnauthenticated permission class.
        """
        self._check_and_cache_login_required_found(view_func)
        if self.is_jwt_auth_enabled_with_login_required(request, view_func):
            request.META[USE_JWT_COOKIE_HEADER] = 'true'

    def process_response(self, request, response):
        """
        Redirects unauthenticated users to login when LoginRedirectIfUnauthenticated permission class was used.
        """
        if self._is_login_required_found() and not request.user.is_authenticated:
            login_url = self.get_login_url(request)  # pylint: disable=assignment-from-none
            return login_required(function=lambda request: None, login_url=login_url)(request)

        return response

    _REQUEST_CACHE_NAMESPACE = 'JwtRedirectToLoginIfUnauthenticatedMiddleware'
    _LOGIN_REQUIRED_FOUND_CACHE_KEY = 'login_required_found'

    def _get_request_cache(self):
        return RequestCache(self._REQUEST_CACHE_NAMESPACE).data

    def _is_login_required_found(self):
        """
        Returns True if LoginRedirectIfUnauthenticated permission was found, and False otherwise.
        """
        return self._get_request_cache().get(self._LOGIN_REQUIRED_FOUND_CACHE_KEY, False)

    def _check_and_cache_login_required_found(self, view_func):
        """
        Checks for LoginRedirectIfUnauthenticated permission and caches the result.
        """
        view_class = _get_view_class(view_func)
        view_permission_classes = getattr(view_class, 'permission_classes', tuple())
        is_login_required_found = _includes_base_class(view_permission_classes, LoginRedirectIfUnauthenticated)
        self._get_request_cache()[self._LOGIN_REQUIRED_FOUND_CACHE_KEY] = is_login_required_found


class JwtAuthCookieMiddleware(MiddlewareMixin):
    """
    Reconstitutes JWT auth cookies for use by API views which use the JwtAuthentication
    authentication class.

    Has side effect of setting request.user to be available for Jwt Authentication
    to Middleware using process_view, but not process_request.

    We split the JWT across two separate cookies in the browser for security reasons. This
    middleware reconstitutes the full JWT into a new cookie on the request object for use
    by the JwtAuthentication class.

    See the full decision here:
        https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0009-jwt-in-session-cookie.rst

    Also, sets the custom attribute 'request_jwt_cookie' with one of the following values:
        'success': Value when reconstitution is successful.
        'not-requested': Value when jwt cookie authentication was not requested by the client.
        'missing-both': Value when both cookies are missing and reconstitution is not possible.
        'missing-XXX': Value when one of the 2 required cookies is missing.  XXX will be
            replaced by the cookie name, which may be set as a setting.  Defaults would
            be 'missing-edx-jwt-cookie-header-payload' or 'missing-edx-jwt-cookie-signature'.

    This middleware must appear before any AuthenticationMiddleware.  For example::

        MIDDLEWARE = (
            'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        )

    """

    def _get_missing_cookie_message_and_attribute(self, cookie_name):
        """ Returns tuple with missing cookie (log_message, custom_attribute_value) """
        cookie_missing_message = '{} cookie is missing. JWT auth cookies will not be reconstituted.'.format(
                cookie_name
        )
        request_jwt_cookie = f'missing-{cookie_name}'
        return cookie_missing_message, request_jwt_cookie

    # Note: Using `process_view` over `process_request` so JwtRedirectToLoginIfUnauthenticatedMiddleware which
    # uses `process_view` can update the request before this middleware. Method `process_request` happened too early.
    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Reconstitute the full JWT and add a new cookie on the request object.
        """
        assert hasattr(request, 'session'), "The Django authentication middleware requires session middleware to be installed. Edit your MIDDLEWARE setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."  # noqa E501 line too long

        use_jwt_cookie_requested = request.META.get(USE_JWT_COOKIE_HEADER)
        header_payload_cookie = request.COOKIES.get(jwt_cookie_header_payload_name())
        signature_cookie = request.COOKIES.get(jwt_cookie_signature_name())

        is_set_request_user_for_jwt_cookie_enabled = get_setting(ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE)
        if use_jwt_cookie_requested and is_set_request_user_for_jwt_cookie_enabled:
            # DRF does not set request.user until process_response. This makes it available in process_view.
            # For more info, see https://github.com/jpadilla/django-rest-framework-jwt/issues/45#issuecomment-74996698
            request.user = SimpleLazyObject(lambda: _get_user_from_jwt(request, view_func))

        if not use_jwt_cookie_requested:
            attribute_value = 'not-requested'
        elif header_payload_cookie and signature_cookie:
            # Reconstitute JWT auth cookie if split cookies are available and jwt cookie
            # authentication was requested by the client.
            request.COOKIES[jwt_cookie_name()] = '{}{}{}'.format(
                header_payload_cookie,
                JWT_DELIMITER,
                signature_cookie,
            )
            attribute_value = 'success'
        elif header_payload_cookie or signature_cookie:
            # Log unexpected case of only finding one cookie.
            if not header_payload_cookie:
                log_message, attribute_value = self._get_missing_cookie_message_and_attribute(
                    jwt_cookie_header_payload_name()
                )
            if not signature_cookie:
                log_message, attribute_value = self._get_missing_cookie_message_and_attribute(
                    jwt_cookie_signature_name()
                )
            log.warning(log_message)
        else:
            attribute_value = 'missing-both'
            log.warning('Both JWT auth cookies missing. JWT auth cookies will not be reconstituted.')

        monitoring.set_custom_attribute('request_jwt_cookie', attribute_value)


def _get_user_from_jwt(request, view_func):
    user = get_user(request)
    if user.is_authenticated:
        return user

    try:
        jwt_authentication_class = _get_jwt_authentication_class(view_func)
        if jwt_authentication_class:
            user_jwt = jwt_authentication_class().authenticate(Request(
                request,
                parsers=api_settings.DEFAULT_PARSER_CLASSES
            ))
            if user_jwt is not None:
                return user_jwt[0]
            else:
                log.warning('Jwt Authentication failed and request.user could not be set.')
        else:
            log.warning(
                'Jwt Authentication expected, but view %s is not using a JwtAuthentication class.', view_func
            )
    except Exception:  # pylint: disable=broad-except
        log.exception('Unknown error attempting to complete Jwt Authentication.')  # pragma: no cover

    return user


def _get_jwt_authentication_class(view_func):
    """
    Returns the first DRF Authentication class that is a subclass of JSONWebTokenAuthentication
    """
    view_class = _get_view_class(view_func)
    view_authentication_classes = getattr(view_class, 'authentication_classes', tuple())
    if _includes_base_class(view_authentication_classes, JSONWebTokenAuthentication):
        return next(
            current_class for current_class in view_authentication_classes
            if issubclass(current_class, JSONWebTokenAuthentication)
        )
    return None


def _includes_base_class(iter_classes, base_class):
    """
    Returns whether any class in iter_class is a subclass of the given base_class.
    """
    return any(
        issubclass(current_class, base_class) for current_class in iter_classes
    )


def _get_view_class(view_func):
    # Views as functions store the view's class in the 'view_class' attribute.
    # Viewsets store the view's class in the 'cls' attribute.
    view_class = getattr(
        view_func,
        'view_class',
        getattr(view_func, 'cls', view_func),
    )
    return view_class
