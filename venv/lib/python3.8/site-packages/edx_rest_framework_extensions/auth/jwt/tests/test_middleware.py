"""
Unit tests for jwt authentication middlewares.
"""
from itertools import product
from unittest.mock import ANY, patch

import ddt
from django.http.cookie import SimpleCookie
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import re_path as url_pattern
from django.utils.deprecation import MiddlewareMixin
from edx_django_utils.cache import RequestCache
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from edx_rest_framework_extensions.auth.jwt.constants import USE_JWT_COOKIE_HEADER
from edx_rest_framework_extensions.auth.jwt.cookies import (
    jwt_cookie_header_payload_name,
    jwt_cookie_name,
    jwt_cookie_signature_name,
)
from edx_rest_framework_extensions.auth.jwt.middleware import (
    EnsureJWTAuthSettingsMiddleware,
    JwtAuthCookieMiddleware,
    JwtRedirectToLoginIfUnauthenticatedMiddleware,
)
from edx_rest_framework_extensions.config import ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE
from edx_rest_framework_extensions.permissions import (
    IsStaff,
    IsSuperuser,
    JwtHasContentOrgFilterForRequestedCourse,
    LoginRedirectIfUnauthenticated,
    NotJwtRestrictedApplication,
)
from edx_rest_framework_extensions.tests.factories import UserFactory


class SomeIncludedPermissionClass:
    pass


class SomeJwtAuthenticationSubclass(JSONWebTokenAuthentication):
    pass


def some_auth_decorator(include_jwt_auth, include_required_perm):
    def _decorator(f):
        f.permission_classes = (SomeIncludedPermissionClass,)
        f.authentication_classes = (SessionAuthentication,)
        if include_jwt_auth:
            f.authentication_classes += (SomeJwtAuthenticationSubclass,)
        if include_required_perm:
            f.permission_classes += (NotJwtRestrictedApplication,)
        return f
    return _decorator


@ddt.ddt
class TestEnsureJWTAuthSettingsMiddleware(TestCase):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get('/')
        self.middleware = EnsureJWTAuthSettingsMiddleware()

    def _assert_included(self, item, iterator, should_be_included):
        if should_be_included:
            self.assertIn(item, iterator)
        else:
            self.assertNotIn(item, iterator)

    @ddt.data(
        *product(
            ('view_set', 'class_view', 'function_view'),
            (True, False),
            (True, False),
        )
    )
    @ddt.unpack
    def test_api_views(self, view_type, include_jwt_auth, include_required_perm):
        @some_auth_decorator(include_jwt_auth, include_required_perm)
        class SomeClassView(APIView):
            pass

        @some_auth_decorator(include_jwt_auth, include_required_perm)
        class SomeClassViewSet(ViewSet):
            pass

        @api_view(["GET"])
        @some_auth_decorator(include_jwt_auth, include_required_perm)
        def some_function_view(request):  # pylint: disable=unused-argument
            pass

        views = dict(
            class_view=SomeClassView,
            view_set=SomeClassViewSet.as_view({'get': 'list'}),
            function_view=some_function_view,
        )
        view_classes = dict(
            class_view=SomeClassView,
            view_set=views['view_set'].cls,  # pylint: disable=no-member
            function_view=views['function_view'].view_class,
        )
        view = views[view_type]
        view_class = view_classes[view_type]

        # verify pre-conditions
        self._assert_included(
            SomeJwtAuthenticationSubclass,
            view_class.authentication_classes,
            should_be_included=include_jwt_auth,
        )

        with patch('edx_rest_framework_extensions.auth.jwt.middleware.log.info') as mock_info:
            self.assertIsNone(
                self.middleware.process_view(self.request, view, None, None)
            )
            self.assertEqual(mock_info.called, include_jwt_auth and not include_required_perm)

        # verify post-conditions

        # verify permission class updates
        self._assert_included(
            NotJwtRestrictedApplication,
            view_class.permission_classes,
            should_be_included=include_required_perm or include_jwt_auth,
        )

    def test_simple_view(self):
        """
        Verify middleware works for views that don't have an api_view decorator.
        """
        def some_simple_view(request):  # pylint: disable=unused-argument
            pass

        self.assertIsNone(
            self.middleware.process_view(self.request, some_simple_view, None, None)
        )

    def test_conditional_permissions_drf(self):
        """
        Make sure we handle conditional permissions composed using the inbuilt-support in DRF>=3.9
        """
        class HasCondPermView(APIView):
            authentication_classes = (SomeJwtAuthenticationSubclass,)
            original_permission_classes = (
                JwtHasContentOrgFilterForRequestedCourse & NotJwtRestrictedApplication,
                IsSuperuser | IsStaff,
            )
            permission_classes = original_permission_classes

        class HasNegatedCondPermView(APIView):
            authentication_classes = (SomeJwtAuthenticationSubclass,)
            original_permission_classes = (
                ~NotJwtRestrictedApplication & JwtHasContentOrgFilterForRequestedCourse,
                IsSuperuser | IsStaff,
            )
            permission_classes = original_permission_classes

        class HasNoCondPermView(APIView):
            authentication_classes = (SomeJwtAuthenticationSubclass,)
            original_permission_classes = (
                JwtHasContentOrgFilterForRequestedCourse,
                IsSuperuser | IsStaff,
            )
            permission_classes = original_permission_classes

        # NotJwtRestrictedApplication exists (it's nested in a conditional), so the middleware
        # shouldn't modify this class.
        self.middleware.process_view(self.request, HasCondPermView, None, None)

        # Note: ConditionalPermissions don't implement __eq__
        self.assertIs(
            HasCondPermView.original_permission_classes,
            HasCondPermView.permission_classes
        )

        # NotJwtRestrictedApplication exists (it's nested in a conditional), so the middleware
        # shouldn't modify this class.
        self.middleware.process_view(self.request, HasNegatedCondPermView, None, None)

        # Note: ConditionalPermissions don't implement __eq__
        self.assertIs(
            HasNegatedCondPermView.original_permission_classes,
            HasNegatedCondPermView.permission_classes
        )

        # NotJwtRestrictedApplication does not exist anywhere, so it should be appended
        self.middleware.process_view(self.request, HasNoCondPermView, None, None)

        # Note: ConditionalPermissions don't implement __eq__
        self.assertIsNot(
            HasNoCondPermView.original_permission_classes,
            HasNoCondPermView.permission_classes
        )
        self.assertIn(NotJwtRestrictedApplication, HasNoCondPermView.permission_classes)


class MockJwtAuthentication(JSONWebTokenAuthentication):
    """
    Authenticates a user if the reconstituted jwt cookie contains the expected value.

    The reconstituted value would only be available if JwtAuthCookieMiddleware can
    correctly reconstitute it.
    """
    def authenticate(self, request):
        if request.COOKIES.get(jwt_cookie_name(), None) != 'header.payload.signature':
            return None

        # authenticate was failing on POST calls because it previously wasn't passing the
        # supported parsers into the new Request object. This retrieval of POST data
        # simulates the CSRF POST data checks in the non-test authenticate method. This
        # line lets us verify that the parsers are being correctly passed to the request
        request.POST.get('csrfmiddlewaretoken', '')

        user = UserFactory()
        return (user, None)


class MockUnauthenticatedView(APIView):
    def get(self, request):  # pylint: disable=unused-argument
        return Response({'success': True})


class MockJwtAuthenticationView(APIView):
    authentication_classes = (MockJwtAuthentication,)

    def get(self, request):  # pylint: disable=unused-argument
        return Response({'success': True})

    def post(self, request):  # pylint: disable=unused-argument
        return Response({'success': True})


class LoginRedirectIfUnauthenticatedView(MockJwtAuthenticationView):
    permission_classes = (LoginRedirectIfUnauthenticated,)


class IsAuthenticatedAndLoginRedirectIfUnauthenticatedView(MockJwtAuthenticationView):
    """ If unnecessary IsAuthenticated is added, LoginRedirectIfUnauthenticated should still work. """
    permission_classes = (IsAuthenticated, LoginRedirectIfUnauthenticated,)


class IsAuthenticatedView(MockJwtAuthenticationView):
    permission_classes = (IsAuthenticated,)


class NoPermissionsRequiredView(MockJwtAuthenticationView):
    pass


urlpatterns = [
    url_pattern(
        r'^loginredirectifunauthenticated/$',
        LoginRedirectIfUnauthenticatedView.as_view(),
    ),
    url_pattern(
        r'^isauthenticatedandloginredirect/$',
        IsAuthenticatedAndLoginRedirectIfUnauthenticatedView.as_view()),
    url_pattern(
        r'^isauthenticated/$',
        IsAuthenticatedView.as_view(),
    ),
    url_pattern(
        r'^nopermissionsrequired/$',
        NoPermissionsRequiredView.as_view(),
    ),
    url_pattern(
        r'^unauthenticated/$',
        MockUnauthenticatedView.as_view(),
    ),
]


class OverriddenJwtRedirectToLoginIfUnauthenticatedMiddleware(JwtRedirectToLoginIfUnauthenticatedMiddleware):
    def get_login_url(self, request):
        return '/overridden/login/'

    def is_jwt_auth_enabled_with_login_required(self, request, view_func):
        # force disable jwt cookie reconstitution in all cases
        return False


@ddt.ddt
class TestJwtRedirectToLoginIfUnauthenticatedMiddleware(TestCase):
    """
    Tests integration of JwtRedirectToLoginIfUnauthenticatedMiddleware with JwtAuthCookieMiddleware.

    Note: using an integration test over a unit test, because initial integration was broken.
    """

    def setUp(self):
        super().setUp()
        RequestCache.clear_all_namespaces()
        self.client = Client()

    @ddt.data(
        ('/loginredirectifunauthenticated/', False, 302),
        ('/loginredirectifunauthenticated/', True, 200),
        ('/isauthenticatedandloginredirect/', False, 302),
        ('/isauthenticatedandloginredirect/', True, 200),
        ('/isauthenticated/', False, 401),
        ('/isauthenticated/', True, 401),
        ('/nopermissionsrequired/', False, 200),
        ('/nopermissionsrequired/', True, 200),
    )
    @ddt.unpack
    @override_settings(
        ROOT_URLCONF='edx_rest_framework_extensions.auth.jwt.tests.test_middleware',
        MIDDLEWARE=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'edx_rest_framework_extensions.auth.jwt.middleware.JwtRedirectToLoginIfUnauthenticatedMiddleware',
            'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',
        ),
        LOGIN_URL='/test/login/',
    )
    def test_login_required_middleware(self, url, has_jwt_cookies, expected_status):
        if has_jwt_cookies:
            self.client.cookies = _get_test_cookie()
        response = self.client.get(url)
        self.assertEqual(expected_status, response.status_code)
        if response.status_code == 302:
            self.assertEqual('/test/login/?next=' + url, response.url)

    @ddt.data(
        ('/loginredirectifunauthenticated/', False, 302),
        ('/loginredirectifunauthenticated/', True, 302),
        ('/isauthenticatedandloginredirect/', False, 302),
        ('/isauthenticatedandloginredirect/', True, 302),
        ('/isauthenticated/', False, 401),
        ('/isauthenticated/', True, 401),
        ('/nopermissionsrequired/', False, 200),
        ('/nopermissionsrequired/', True, 200),
    )
    @ddt.unpack
    @override_settings(
        ROOT_URLCONF='edx_rest_framework_extensions.auth.jwt.tests.test_middleware',
        MIDDLEWARE=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'edx_rest_framework_extensions.auth.jwt.tests.test_middleware.OverriddenJwtRedirectToLoginIfUnauthenticatedMiddleware',  # noqa E501 line too long
            'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',
        ),
        LOGIN_URL='/test/login/',
    )
    def test_login_required_overridden_middleware(self, url, has_jwt_cookies, expected_status):
        if has_jwt_cookies:
            self.client.cookies = _get_test_cookie()
        response = self.client.get(url)
        self.assertEqual(expected_status, response.status_code)
        if response.status_code == 302:
            self.assertEqual('/overridden/login/?next=' + url, response.url)


class CheckRequestUserForJwtAuthMiddleware(MiddlewareMixin):
    """
    This test middleware can be used to confirm that our Jwt Authentication related middleware correctly
    set the request.user.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        assert request.user.is_authenticated, 'Request.user was expected to be authenticated.'


class CheckRequestUserAnonymousForJwtAuthMiddleware(MiddlewareMixin):
    """
    This test middleware can be used to confirm that when Jwt Authentication related middleware does not set
    the user (e.g. a failed cookie).
    """
    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        assert not request.user.is_authenticated, 'Request.user was expected to be anonymous.'


@ddt.ddt
class TestJwtAuthCookieMiddleware(TestCase):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get('/')
        self.request.session = 'mock session'
        self.middleware = JwtAuthCookieMiddleware()

    @patch('edx_django_utils.monitoring.set_custom_attribute')
    def test_do_not_use_jwt_cookies(self, mock_set_custom_attribute):
        self.middleware.process_view(self.request, None, None, None)
        self.assertIsNone(self.request.COOKIES.get(jwt_cookie_name()))
        mock_set_custom_attribute.assert_called_once_with('request_jwt_cookie', 'not-requested')

    @ddt.data(
        (jwt_cookie_header_payload_name(), jwt_cookie_signature_name()),
        (jwt_cookie_signature_name(), jwt_cookie_header_payload_name()),
    )
    @ddt.unpack
    @patch('edx_rest_framework_extensions.auth.jwt.middleware.log')
    @patch('edx_django_utils.monitoring.set_custom_attribute')
    def test_missing_cookies(
            self, set_cookie_name, missing_cookie_name, mock_set_custom_attribute, mock_log
    ):
        self.request.META[USE_JWT_COOKIE_HEADER] = 'true'
        self.request.COOKIES[set_cookie_name] = 'test'
        self.middleware.process_view(self.request, None, None, None)
        self.assertIsNone(self.request.COOKIES.get(jwt_cookie_name()))
        mock_log.warning.assert_called_once_with(
            '%s cookie is missing. JWT auth cookies will not be reconstituted.' %
            missing_cookie_name
        )
        mock_set_custom_attribute.assert_called_once_with(
            'request_jwt_cookie', f'missing-{missing_cookie_name}'
        )

    @patch('edx_django_utils.monitoring.set_custom_attribute')
    def test_no_cookies(self, mock_set_custom_attribute):
        self.request.META[USE_JWT_COOKIE_HEADER] = 'true'
        self.middleware.process_view(self.request, None, None, None)
        self.assertIsNone(self.request.COOKIES.get(jwt_cookie_name()))
        mock_set_custom_attribute.assert_called_once_with('request_jwt_cookie', 'missing-both')

    @patch('edx_django_utils.monitoring.set_custom_attribute')
    def test_success(self, mock_set_custom_attribute):
        self.request.META[USE_JWT_COOKIE_HEADER] = 'true'
        self.request.COOKIES[jwt_cookie_header_payload_name()] = 'header.payload'
        self.request.COOKIES[jwt_cookie_signature_name()] = 'signature'
        self.middleware.process_view(self.request, None, None, None)
        self.assertEqual(self.request.COOKIES[jwt_cookie_name()], 'header.payload.signature')
        mock_set_custom_attribute.assert_called_once_with('request_jwt_cookie', 'success')

    _LOG_WARN_AUTHENTICATION_FAILED = 0
    _LOG_WARN_MISSING_JWT_AUTHENTICATION_CLASS = 1

    @patch('edx_rest_framework_extensions.auth.jwt.middleware.log')
    @ddt.data(
        ('/nopermissionsrequired/', True, True, True, None, False),
        ('/nopermissionsrequired/', True, False, False, None, False),
        ('/nopermissionsrequired/', False, False, True, _LOG_WARN_AUTHENTICATION_FAILED, False),
        ('/nopermissionsrequired/', False, False, False, None, False),
        ('/nopermissionsrequired/', True, True, True, None, True),
        ('/unauthenticated/', True, False, True, _LOG_WARN_MISSING_JWT_AUTHENTICATION_CLASS, False),
        ('/unauthenticated/', True, False, True, None, False),
    )
    @ddt.unpack
    def test_set_request_user_with_use_jwt_cookie(
            self, url, is_cookie_valid, is_request_user_set, is_toggle_enabled, log_warning,
            send_post, mock_log,
    ):
        header = {USE_JWT_COOKIE_HEADER: 'true'}
        self.client.cookies = _get_test_cookie(is_cookie_valid=is_cookie_valid)
        check_user_middleware_assertion_class = (
            'CheckRequestUserForJwtAuthMiddleware'
            if is_request_user_set else
            'CheckRequestUserAnonymousForJwtAuthMiddleware'
        )
        with override_settings(
            ROOT_URLCONF='edx_rest_framework_extensions.auth.jwt.tests.test_middleware',
            MIDDLEWARE=(
                    'django.contrib.sessions.middleware.SessionMiddleware',
                    'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',
                    'django.contrib.auth.middleware.AuthenticationMiddleware',
                    'edx_rest_framework_extensions.auth.jwt.tests.test_middleware.{}'.format(
                        check_user_middleware_assertion_class
                    ),
            ),
            EDX_DRF_EXTENSIONS={
                ENABLE_SET_REQUEST_USER_FOR_JWT_COOKIE: is_toggle_enabled,
            }
        ):
            if send_post:
                response = self.client.post(url, {}, content_type="application/json", **header)
            else:
                response = self.client.get(url, **header)
            self.assertEqual(200, response.status_code)

            if log_warning == self._LOG_WARN_AUTHENTICATION_FAILED:
                mock_log.warning.assert_called_once_with('Jwt Authentication failed and request.user could not be set.')
            elif log_warning == self._LOG_WARN_MISSING_JWT_AUTHENTICATION_CLASS:
                mock_log.warning.assert_called_once_with(
                    'Jwt Authentication expected, but view %s is not using a JwtAuthentication class.', ANY
                )
            else:
                mock_log.warn.assert_not_called()


def _get_test_cookie(is_cookie_valid=True):
    header_payload_value = 'header.payload' if is_cookie_valid else 'header.payload.invalid'
    return SimpleCookie({
        jwt_cookie_header_payload_name(): header_payload_value,
        jwt_cookie_signature_name(): 'signature',
    })
