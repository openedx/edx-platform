"""
Tests for the Certificate REST APIs.
"""
# pylint: disable=missing-docstring
from datetime import datetime, timedelta
from enum import Enum
from itertools import product
import ddt
from mock import patch

from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from oauth2_provider import models as dot_models
from rest_framework import status
from rest_framework.test import APITestCase

from course_modes.models import CourseMode
from lms.djangoapps.certificates.apis.v0.views import CertificatesDetailView
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.oauth_dispatch.toggles import ENFORCE_JWT_SCOPES
from openedx.core.lib.token_utils import JwtBuilder
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

USER_PASSWORD = 'test'


class AuthType(Enum):
    session = 1
    oauth = 2
    jwt = 3
    jwt_restricted = 4


JWT_AUTH_TYPES = [AuthType.jwt, AuthType.jwt_restricted]


@ddt.ddt
class CertificatesRestApiTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Certificates REST APIs
    """
    shard = 4
    now = timezone.now()

    @classmethod
    def setUpClass(cls):
        super(CertificatesRestApiTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CertificatesRestApiTest, self).setUp()

        self.student = UserFactory.create(password=USER_PASSWORD)
        self.student_no_cert = UserFactory.create(password=USER_PASSWORD)
        self.staff_user = UserFactory.create(password=USER_PASSWORD, is_staff=True)

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
            grade="0.88"
        )

        self.namespaced_url = 'certificates_api:v0:certificates:detail'

    def _assert_certificate_response(self, response):
        self.assertEqual(
            response.data,
            {
                'username': self.student.username,
                'status': CertificateStatuses.downloadable,
                'is_passing': True,
                'grade': '0.88',
                'download_url': 'www.google.com',
                'certificate_type': CourseMode.VERIFIED,
                'course_id': unicode(self.course.id),
                'created_date': self.now,
            }
        )

    def _get_url(self, username):
        """
        Helper function to create the url for certificates
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': self.course.id,
                'username': username
            }
        )

    def _create_oauth_token(self, user):
        dot_app_user = UserFactory.create(password=USER_PASSWORD)
        dot_app = dot_models.Application.objects.create(
            name='test app',
            user=dot_app_user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        return dot_models.AccessToken.objects.create(
            user=user,
            application=dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='read write',
            token='test_token',
        )

    def _create_jwt_token(self, user, auth_type, scopes=None, include_org_filter=True, include_me_filter=False):
        filters = []
        if include_org_filter:
            filters += ['content_org:{}'.format(self.course.id.org)]
        if include_me_filter:
            filters += ['user:me']

        if scopes is None:
            scopes = CertificatesDetailView.required_scopes

        return JwtBuilder(user).build_token(
            scopes,
            additional_claims=dict(
                is_restricted=(auth_type == AuthType.jwt_restricted),
                filters=filters,
            ),
        )

    def _get_response(self, requesting_user, auth_type, url=None, token=None):
        auth_header = None
        if auth_type == AuthType.session:
            self.client.login(username=requesting_user.username, password=USER_PASSWORD)
        elif auth_type == AuthType.oauth:
            if not token:
                token = self._create_oauth_token(requesting_user)
            auth_header = "Bearer {0}".format(token)
        else:
            assert auth_type in JWT_AUTH_TYPES
            if not token:
                token = self._create_jwt_token(requesting_user, auth_type)
            auth_header = "JWT {0}".format(token)

        extra = dict(HTTP_AUTHORIZATION=auth_header) if auth_header else {}
        return self.client.get(
            url if url else self._get_url(self.student.username),
            **extra
        )

    def _assert_in_log(self, text, mock_log_method):
        self.assertTrue(mock_log_method.called)
        self.assertIn(text, mock_log_method.call_args_list[0][0][0])

    def test_anonymous_user(self):
        resp = self.client.get(self._get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @ddt.data(*list(AuthType))
    def test_no_certificate(self, auth_type):
        resp = self._get_response(
            self.student_no_cert,
            auth_type,
            url=self._get_url(self.student_no_cert.username),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)
        self.assertEqual(
            resp.data['error_code'],
            'no_certificate_for_user',
        )

    @ddt.data(*product(list(AuthType), (True, False)))
    @ddt.unpack
    def test_self_user(self, auth_type, scopes_enforced):
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            resp = self._get_response(self.student, auth_type)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self._assert_certificate_response(resp)

    @ddt.data(*product(list(AuthType), (True, False)))
    @ddt.unpack
    def test_inactive_user(self, auth_type, scopes_enforced):
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            self.student.is_active = False
            self.student.save()

            resp = self._get_response(self.student, auth_type)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @ddt.data(*product(list(AuthType), (True, False)))
    @ddt.unpack
    def test_staff_user(self, auth_type, scopes_enforced):
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            resp = self._get_response(self.staff_user, auth_type)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(*product(list(AuthType), (True, False)))
    @ddt.unpack
    def test_another_user(self, auth_type, scopes_enforced, mock_log):
        """ Returns 403 for OAuth and Session auth with IsUserInUrl. """
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            resp = self._get_response(self.student_no_cert, auth_type)

            # Restricted JWT tokens without the user:me filter have access to other users
            expected_jwt_access_granted = scopes_enforced and auth_type == AuthType.jwt_restricted

            self.assertEqual(
                resp.status_code,
                status.HTTP_200_OK if expected_jwt_access_granted else status.HTTP_403_FORBIDDEN,
            )
            if not expected_jwt_access_granted:
                self._assert_in_log("IsUserInUrl", mock_log.info)

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(*product(JWT_AUTH_TYPES, (True, False)))
    @ddt.unpack
    def test_jwt_no_scopes(self, auth_type, scopes_enforced, mock_log):
        """ Returns 403 when scopes are enforced with JwtHasScope. """
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(self.student, auth_type, scopes=[])
            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)

            is_enforced = scopes_enforced and auth_type == AuthType.jwt_restricted
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN if is_enforced else status.HTTP_200_OK)

            if is_enforced:
                self._assert_in_log("JwtHasScope", mock_log.warning)

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(*product(JWT_AUTH_TYPES, (True, False)))
    @ddt.unpack
    def test_jwt_no_filter(self, auth_type, scopes_enforced, mock_log):
        """ Returns 403 when scopes are enforced with JwtHasContentOrgFilterForRequestedCourse. """
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(self.student, auth_type, include_org_filter=False)
            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)

            is_enforced = scopes_enforced and auth_type == AuthType.jwt_restricted
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN if is_enforced else status.HTTP_200_OK)

            if is_enforced:
                self._assert_in_log("JwtHasContentOrgFilterForRequestedCourse", mock_log.warning)

    @ddt.data(*product(JWT_AUTH_TYPES, (True, False)))
    @ddt.unpack
    def test_jwt_on_behalf_of_user(self, auth_type, scopes_enforced):
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(self.student, auth_type, include_me_filter=True)

            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(*product(JWT_AUTH_TYPES, (True, False)))
    @ddt.unpack
    def test_jwt_on_behalf_of_other_user(self, auth_type, scopes_enforced, mock_log):
        """ Returns 403 when scopes are enforced with JwtHasUserFilterForRequestedUser. """
        with ENFORCE_JWT_SCOPES.override(active=scopes_enforced):
            jwt_token = self._create_jwt_token(self.student_no_cert, auth_type, include_me_filter=True)
            resp = self._get_response(self.student, AuthType.jwt, token=jwt_token)

            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

            if scopes_enforced and auth_type == AuthType.jwt_restricted:
                self._assert_in_log("JwtHasUserFilterForRequestedUser", mock_log.warning)
            else:
                self._assert_in_log("IsUserInUrl", mock_log.info)

    def test_valid_oauth_token(self):
        resp = self._get_response(self.student, AuthType.oauth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_invalid_oauth_token(self):
        resp = self._get_response(self.student, AuthType.oauth, token="fooooooooooToken")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_oauth_token(self):
        token = self._create_oauth_token(self.student)
        token.expires = datetime.utcnow() - timedelta(weeks=1)
        token.save()
        resp = self._get_response(self.student, AuthType.oauth, token=token)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
