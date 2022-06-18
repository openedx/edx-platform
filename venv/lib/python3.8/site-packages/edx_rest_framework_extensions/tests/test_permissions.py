""" Tests for permission classes. """

from collections import namedtuple
from itertools import product
from unittest.mock import Mock, patch

import ddt
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.jwt.tests.utils import generate_jwt
from edx_rest_framework_extensions.tests import factories
from edx_rest_framework_extensions.tests.factories import UserFactory


@ddt.ddt
class IsSuperuserTests(TestCase):
    """ Tests for the IsSuperuser permission class. """

    @ddt.data(True, False)
    def test_superuser_has_permission(self, has_permission):
        request = RequestFactory().get('/')
        request.user = factories.UserFactory(is_superuser=has_permission)
        permission = permissions.IsSuperuser()
        self.assertEqual(permission.has_permission(request, None), has_permission)

    @ddt.data(None, AnonymousUser())
    def test_invalid_user_has_no_permission(self, user):
        request = RequestFactory().get('/')
        request.user = user
        permission = permissions.IsSuperuser()
        self.assertFalse(permission.has_permission(request, None))


@ddt.ddt
class IsStaffTests(TestCase):
    """ Tests for the IsStaff permission class. """

    @ddt.data(True, False)
    def test_has_permission(self, is_staff):
        request = RequestFactory().get('/')
        request.user = factories.UserFactory(is_staff=is_staff)
        self.assertEqual(permissions.IsStaff().has_permission(request, None), is_staff)


@ddt.ddt
class IsUserInUrlTests(TestCase):
    """ Tests for the IsUserInUrl permission class. """

    def _create_request(self, user, username_in_param=None, username_in_resource=None):
        url = '/'
        if username_in_param:
            url += f'?username={username_in_param}'
        request = RequestFactory().get(url)
        request.user = user
        if username_in_resource:
            request.parser_context = dict(kwargs=dict(username=username_in_resource))
        return request

    @ddt.data(True, False)
    def test_user_in_url_param(self, has_user_in_url):
        user = factories.UserFactory(username='this_user')
        request = self._create_request(
            user,
            username_in_param=user.username if has_user_in_url else 'another_user',
        )
        self.assertEqual(permissions.IsUserInUrl().has_permission(request, None), has_user_in_url)

    @ddt.data(True, False)
    def test_user_in_url_resource(self, has_user_in_resource):
        user = factories.UserFactory(username='this_user')
        request = self._create_request(
            user,
            username_in_resource=user.username if has_user_in_resource else 'another_user',
        )
        self.assertEqual(permissions.IsUserInUrl().has_permission(request, None), has_user_in_resource)

    def test_resource_takes_precedence_over_param(self):
        user = factories.UserFactory(username='this_user')
        request = self._create_request(
            user,
            username_in_resource='another_user',
            username_in_param='this_user',
        )
        self.assertFalse(permissions.IsUserInUrl().has_permission(request, None))

        request = self._create_request(
            user,
            username_in_resource='this_user',
            username_in_param='another_user',
        )
        self.assertTrue(permissions.IsUserInUrl().has_permission(request, None))


@ddt.ddt
class JwtApplicationPermissionsTests(TestCase):
    """ Tests for the JwtRestrictedApplication and NotJwtRestrictedApplication permission classes. """

    @ddt.data(
        *product(
            (permissions.JwtRestrictedApplication, permissions.NotJwtRestrictedApplication),
            (JwtAuthentication, JSONWebTokenAuthentication, SessionAuthentication, None),
            (True, False),
        )
    )
    @ddt.unpack
    def test_has_permission(self, permission_class, authentication_class, is_restricted):
        request = RequestFactory().get('/')
        request.successful_authenticator = authentication_class() if authentication_class else None
        request.user = factories.UserFactory()
        request.auth = generate_jwt(request.user, is_restricted=is_restricted)

        is_jwt_auth_subclass = issubclass(type(request.successful_authenticator), JSONWebTokenAuthentication)

        has_permission = permission_class().has_permission(request, view=None)
        expected_restricted_permission = is_restricted and is_jwt_auth_subclass
        if permission_class == permissions.JwtRestrictedApplication:
            self.assertEqual(has_permission, expected_restricted_permission)
        else:
            self.assertEqual(has_permission, not expected_restricted_permission)


@ddt.ddt
class JwtHasScopeTests(TestCase):
    """ Tests for JwtHasScope permission class. """
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @ddt.data(
        (JwtAuthentication(), ('test:read',), ('test:read',), True),  # match
        (JwtAuthentication(), ('test:write'), ('test:read',), False),  # mismatch
        (JwtAuthentication(), ('test:read'), (), False),  # empty on API
        (JwtAuthentication(), ('test:read'), None, False),  # missing on API
        (JwtAuthentication(), (), ('test:read',), False),  # missing on jwt
        (JwtAuthentication(), (), None, False),  # missing on both
        (None, (), ('test:read'), False),  # no auth
    )
    @ddt.unpack
    def test_has_permission(self, authentication_class, jwt_scopes, required_scopes, expected_result):
        request = RequestFactory().get('/')
        request.successful_authenticator = authentication_class
        request.auth = generate_jwt(self.user, scopes=jwt_scopes)
        if required_scopes is None:
            view = APIView()
        else:
            view = Mock(required_scopes=required_scopes)
        self.assertEqual(permissions.JwtHasScope().has_permission(request, view), expected_result)


@ddt.ddt
class JwtHasContentOrgFilterForRequestedCourseTests(TestCase):
    """ Tests for JwtHasContentOrgFilterForRequestedCourse permission class. """
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @ddt.data(
        (JwtAuthentication(), ['content_org:edX'], {'course_id': 'course-v1:edX+DemoX+Demo_Course'}, True),
        (JwtAuthentication(), ['content_org:TestX'], {'course_id': 'course-v1:edX+DemoX+Demo_Course'}, False),
        (JwtAuthentication(), ['test:TestX'], {'course_id': 'course-v1:edX+DemoX+Demo_Course'}, False),
        (JwtAuthentication(), [], {'course_id': 'course-v1:edX+DemoX+Demo_Course'}, False),
        (None, [], {'course_id': 'course-v1:edX+DemoX+Demo_Course'}, False),
    )
    @ddt.unpack
    def test_has_permission(self, authentication_class, jwt_filters, view_kwargs, expected_result):
        request = RequestFactory().get('/')
        request.successful_authenticator = authentication_class
        request.auth = generate_jwt(self.user, filters=jwt_filters)
        view = Mock(kwargs=view_kwargs)
        self.assertEqual(
            permissions.JwtHasContentOrgFilterForRequestedCourse().has_permission(request, view),
            expected_result,
        )


@ddt.ddt
class JwtHasUserFilterForRequestedUserTests(TestCase):
    """ Tests for JwtHasUserFilterForRequestedUserTests permission class. """

    def _create_request(self, user_filters, requested_username):
        url = f'/?username={requested_username}'
        request = RequestFactory().get(url)
        request.user = UserFactory(username='this_user')
        request.auth = generate_jwt(request.user, filters=user_filters)
        return request

    @ddt.data(
        # no user filters
        ([], 'this_user', True),
        ([], 'another_user', True),

        # accessing self
        (['user:me'], 'this_user', True),
        (['user:this_user'], 'this_user', True),

        # accessing another
        (['user:me'], 'another_user', False),
        (['user:this_user'], 'another_user', False),
        (['user:another_user'], 'another_user', True),
    )
    @ddt.unpack
    def test_has_permission(self, user_filters, requested_username, expected_result):
        request = self._create_request(user_filters, requested_username)
        self.assertEqual(
            permissions.JwtHasUserFilterForRequestedUser().has_permission(request, None),
            expected_result,
        )


@ddt.ddt
class JwtRestrictedApplicationOrUserAccessTests(TestCase):
    ExpectedLog = namedtuple('ExpectedLog', 'method, text, param')

    IsUserInUrlLog = ExpectedLog('info', 'IsUserInUrl', None)
    JwtIsUnrestrictedDebugLog = ExpectedLog('debug', 'JwtRestrictedApplication', False)
    JwtIsRestrictedDebugLog = ExpectedLog('debug', 'JwtRestrictedApplication', True)
    JwtScopesErrorLog = ExpectedLog('warning', 'JwtHasScope', None)
    JwtOrgFilterErrorLog = ExpectedLog('warning', 'JwtHasContentOrgFilterForRequestedCourse', None)
    JwtUserFilterErrorLog = ExpectedLog('warning', 'JwtHasUserFilterForRequestedUser', None)

    class SomeClassView(APIView):
        authentication_classes = (JwtAuthentication, SessionAuthentication)
        permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)
        required_scopes = ['required_scope']

        def get(self, request, course_id=None):  # pylint: disable=unused-argument
            return Response(data="Success")

    def _create_user(self, is_staff=False):
        return UserFactory(username='this_user', is_staff=is_staff)

    def _create_request(self, username_in_url=None, auth_header=None):
        url = '/'
        if username_in_url:
            url += f'?username={username_in_url}'
        extra = {"HTTP_AUTHORIZATION": auth_header} if auth_header else {}
        return RequestFactory().get(url, **extra)

    def _create_session(self, request, user):
        request.user = user

    def _create_jwt_header(self, user, is_restricted=False, scopes=None, filters=None):
        token = generate_jwt(user, is_restricted=is_restricted, scopes=scopes, filters=filters)
        return f"JWT {token}"

    def _assert_log(self, mock_log, expected_log):
        mock_log_method = getattr(mock_log, expected_log.method)
        self.assertTrue(mock_log_method.called)
        self.assertIn(expected_log.text, mock_log_method.call_args_list[0][0][0])
        if expected_log.param is not None:
            self.assertEqual(mock_log_method.call_args_list[0][0][1], expected_log.param)

    def test_anonymous_fails(self):
        request = self._create_request()
        response = self.SomeClassView().dispatch(request)
        self.assertEqual(response.status_code, 401)

    def test_session_staff_succeeds(self):
        user = self._create_user(is_staff=True)
        request = self._create_request()
        self._create_session(request, user)

        response = self.SomeClassView().dispatch(request)
        self.assertEqual(response.status_code, 200)

    @patch('edx_rest_framework_extensions.permissions.log')
    def test_session_user_not_in_url_fails(self, mock_log):
        user = self._create_user()
        request = self._create_request()
        self._create_session(request, user)

        response = self.SomeClassView().dispatch(request)
        self.assertEqual(response.status_code, 403)
        self._assert_log(mock_log, self.IsUserInUrlLog)

    def test_session_user_in_url_succeeds(self):
        user = self._create_user()
        request = self._create_request(username_in_url=user.username)
        self._create_session(request, user)

        response = self.SomeClassView().dispatch(request)
        self.assertEqual(response.status_code, 200)

    @ddt.data(
        # unrestricted
        dict(
            is_restricted=False,
            is_user_in_url=True,
            expected_response=200,
            expected_log=JwtIsUnrestrictedDebugLog
        ),
        dict(
            is_restricted=False,
            is_user_in_url=False,
            expected_response=403,
            expected_log=IsUserInUrlLog
        ),

        # restricted (note: further test cases for scopes and filters are in tests below)
        dict(
            is_restricted=True,
            is_user_in_url=True,
            expected_response=403,
            expected_log=JwtScopesErrorLog
        ),
        dict(
            is_restricted=True,
            is_user_in_url=False,
            expected_response=403,
            expected_log=JwtScopesErrorLog
        ),
    )
    @ddt.unpack
    def test_jwt_without_scopes_and_filters(
            self,
            is_restricted,
            is_user_in_url,
            expected_response,
            expected_log
    ):
        with patch('edx_rest_framework_extensions.permissions.log') as mock_log:
            user = self._create_user()

            auth_header = self._create_jwt_header(user, is_restricted=is_restricted)
            request = self._create_request(
                username_in_url=user.username if is_user_in_url else None,
                auth_header=auth_header,
            )

            response = self.SomeClassView().dispatch(request)
            self.assertEqual(response.status_code, expected_response)
            self._assert_log(mock_log, expected_log)

    @ddt.data(
        # valid scopes
        dict(scopes=['required_scope'], expected_response=200, expected_log=JwtIsRestrictedDebugLog),
        dict(scopes=['required_scope', 'another_scope'], expected_response=200, expected_log=JwtIsRestrictedDebugLog),

        # invalid scopes
        dict(scopes=[], expected_response=403, expected_log=JwtScopesErrorLog),
        dict(scopes=['another_scope'], expected_response=403, expected_log=JwtScopesErrorLog),
    )
    @ddt.unpack
    def test_jwt_scopes(self, scopes, expected_response, expected_log):
        self._assert_jwt_restricted_case(
            scopes=scopes,
            filters=['content_org:some_org'],
            is_user_in_url=False,
            expected_response=expected_response,
            expected_log=expected_log,
        )

    @ddt.data(
        # valid org filters
        dict(
            filters=['content_org:some_org', 'content_org:another_org'],
            expected_response=200,
            expected_log=JwtIsRestrictedDebugLog
        ),

        # invalid org filters
        dict(
            filters=['content_org:another_org'],
            expected_response=403,
            expected_log=JwtOrgFilterErrorLog
        ),
        dict(
            filters=[],
            expected_response=403,
            expected_log=JwtOrgFilterErrorLog
        ),
    )
    @ddt.unpack
    def test_jwt_org_filters(self, filters, expected_response, expected_log):
        self._assert_jwt_restricted_case(
            scopes=['required_scope'],
            filters=filters,
            is_user_in_url=False,
            expected_response=expected_response,
            expected_log=expected_log,
        )

    @ddt.data(
        # valid user filters
        dict(
            user_filters=['user:me'], is_user_in_url=True,
            expected_response=200,
            expected_log=JwtIsRestrictedDebugLog,
        ),

        # invalid user filters
        dict(
            user_filters=['user:me'], is_user_in_url=False,
            expected_response=403,
            expected_log=JwtUserFilterErrorLog,
        ),
        dict(
            user_filters=['user:another'], is_user_in_url=True,
            expected_response=403,
            expected_log=JwtUserFilterErrorLog,
        ),
    )
    @ddt.unpack
    def test_jwt_user_filters(self, user_filters, is_user_in_url, expected_response, expected_log):
        self._assert_jwt_restricted_case(
            scopes=['required_scope'],
            filters=['content_org:some_org'] + user_filters,
            is_user_in_url=is_user_in_url,
            expected_response=expected_response,
            expected_log=expected_log,
        )

    def _assert_jwt_restricted_case(self, scopes, filters, is_user_in_url, expected_response, expected_log):
        with patch('edx_rest_framework_extensions.permissions.log') as mock_log:
            user = self._create_user()

            auth_header = self._create_jwt_header(user, is_restricted=True, scopes=scopes, filters=filters)
            request = self._create_request(
                username_in_url=user.username if is_user_in_url else None,
                auth_header=auth_header,
            )

            response = self.SomeClassView().dispatch(request, course_id='some_org/course/run')
            self.assertEqual(response.status_code, expected_response)
            self._assert_log(mock_log, expected_log)
