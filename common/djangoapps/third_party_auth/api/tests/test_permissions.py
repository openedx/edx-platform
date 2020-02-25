"""
Tests for the Third Party Auth permissions
"""


import unittest

import ddt
from django.conf import settings
from django.test import RequestFactory, TestCase
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.jwt.tests.utils import generate_jwt
from mock import patch
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from student.tests.factories import UserFactory

from third_party_auth.api.permissions import TPA_PERMISSIONS

IDP_SLUG_TESTSHIB = 'testshib'
PROVIDER_ID_TESTSHIB = 'saml-' + IDP_SLUG_TESTSHIB


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ThirdPartyAuthPermissionTest(TestCase):
    """ Tests for third party auth TPA_PERMISSIONS """

    class SomeTpaClassView(APIView):
        """view used to test TPA_permissions"""
        authentication_classes = (JwtAuthentication, SessionAuthentication)
        permission_classes = (TPA_PERMISSIONS,)
        required_scopes = ['tpa:read']

        def get(self, request, provider_id=None):
            return Response(data="Success")

    def _create_user(self, is_superuser=False):
        return UserFactory(username='this_user', is_superuser=is_superuser)

    def _create_request(self, auth_header=None):
        url = '/'
        extra = dict(HTTP_AUTHORIZATION=auth_header) if auth_header else dict()
        return RequestFactory().get(url, **extra)

    def _create_session(self, request, user):
        request.user = user

    def _create_jwt_header(self, user, is_restricted=False, scopes=None, filters=None):
        token = generate_jwt(user, is_restricted=is_restricted, scopes=scopes, filters=filters)
        return "JWT {}".format(token)

    def test_anonymous_fails(self):
        request = self._create_request()
        response = self.SomeTpaClassView().dispatch(request)
        self.assertEqual(response.status_code, 401)

    def test_session_superuser_succeeds(self):
        user = self._create_user(is_superuser=True)
        request = self._create_request()
        self._create_session(request, user)

        response = self.SomeTpaClassView().dispatch(request)
        self.assertEqual(response.status_code, 200)

    def test_session_user_fails(self):
        user = self._create_user()
        request = self._create_request()
        self._create_session(request, user)

        response = self.SomeTpaClassView().dispatch(request)
        self.assertEqual(response.status_code, 403)

    @ddt.data(
        # **** Unenforced ****
        # unrestricted
        dict(
            is_enforced=False,
            is_restricted=False,
            expected_response=403,
        ),

        # restricted
        dict(
            is_enforced=False,
            is_restricted=True,
            expected_response=403,
        ),

        # **** Enforced ****
        # unrestricted (for example, jwt cookies)
        dict(
            is_enforced=True,
            is_restricted=False,
            expected_response=403,
        ),

        # restricted (note: further test cases for scopes and filters are in tests below)
        dict(
            is_enforced=True,
            is_restricted=True,
            expected_response=403,
        ),
    )
    @ddt.unpack
    def test_jwt_without_scopes_and_filters(
            self,
            is_enforced,
            is_restricted,
            expected_response,
    ):
        # pylint: disable=line-too-long
        # Note: Unenforced tests can be retired when rollout waffle switch `oauth2.enforce_jwt_scopes` is retired.
        # See https://github.com/edx/edx-drf-extensions/blob/609e1dbaa98f476b36e50143de97732f2f6a9b4f/edx_rest_framework_extensions/config.py#L5
        # pylint: enable=line-too-long
        with patch('edx_rest_framework_extensions.permissions.waffle.switch_is_active') as mock_toggle:
            mock_toggle.return_value = is_enforced
            user = self._create_user()

            auth_header = self._create_jwt_header(user, is_restricted=is_restricted)
            request = self._create_request(
                auth_header=auth_header,
            )

            response = self.SomeTpaClassView().dispatch(request)
            self.assertEqual(response.status_code, expected_response)

    @ddt.data(
        # valid scopes
        dict(scopes=['tpa:read'], expected_response=200),
        dict(scopes=['tpa:read', 'another_scope'], expected_response=200),

        # invalid scopes
        dict(scopes=[], expected_response=403),
        dict(scopes=['another_scope'], expected_response=403),
    )
    @ddt.unpack
    def test_jwt_scopes(self, scopes, expected_response):
        self._assert_jwt_enforced_restricted_case(
            scopes=scopes,
            filters=['tpa_provider:some_tpa_provider'],
            expected_response=expected_response,
        )

    @ddt.data(
        # valid provider filters
        dict(
            filters=['tpa_provider:some_tpa_provider', 'tpa_provider:another_tpa_provider'],
            expected_response=200,
        ),

        # invalid provider filters
        dict(
            filters=['tpa_provider:another_tpa_provider'],
            expected_response=403,
        ),
        dict(
            filters=[],
            expected_response=403,
        ),
    )
    @ddt.unpack
    def test_jwt_org_filters(self, filters, expected_response):
        self._assert_jwt_enforced_restricted_case(
            scopes=['tpa:read'],
            filters=filters,
            expected_response=expected_response,
        )

    def _assert_jwt_enforced_restricted_case(self, scopes, filters, expected_response):
        with patch('edx_rest_framework_extensions.permissions.waffle.switch_is_active') as mock_toggle:
            mock_toggle.return_value = True
            user = self._create_user()

            auth_header = self._create_jwt_header(user, is_restricted=True, scopes=scopes, filters=filters)
            request = self._create_request(auth_header=auth_header)

            response = self.SomeTpaClassView().dispatch(request, provider_id='some_tpa_provider')
            self.assertEqual(response.status_code, expected_response)
