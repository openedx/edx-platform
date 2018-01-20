"""
Tests for the Certificate REST APIs.
"""
from datetime import datetime, timedelta
import json

from django.core.urlresolvers import reverse
from oauth2_provider import models as dot_models
from rest_framework import status
from rest_framework.test import APITestCase

from certificates.models import CertificateStatuses
from certificates.tests.factories import GeneratedCertificateFactory
from course_modes.models import CourseMode
from openedx.core.djangoapps.oauth_dispatch.models import RestrictedApplication
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

USER_PASSWORD = 'test'


class CertificatesRestApiTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Certificates REST APIs
    """
    @classmethod
    def setUpClass(cls):
        super(CertificatesRestApiTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )
        cls.not_edx_course = CourseFactory.create(
            org='NotEdx',
            number='verified',
            display_name='Not a Edx Course'
        )

    def setUp(self):
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

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.not_edx_course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
            grade="0.88"
        )

        self.namespaced_url = 'certificates_api:v0:certificates:detail'

        # create a configuration for django-oauth-toolkit (DOT)
        dot_app_user = UserFactory.create(password=USER_PASSWORD)
        dot_app = dot_models.Application.objects.create(
            name='test app',
            user=dot_app_user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        self.dot_access_token = dot_models.AccessToken.objects.create(
            user=self.student,
            application=dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='read write',
            token='16MGyP3OaQYHmpT1lK7Q6MMNAZsjwF'
        )

        # create a restricted application DOT application
        restricted_dot_app = dot_models.Application.objects.create(
            name='restricted test app',
            user=dot_app_user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        RestrictedApplication.objects.create(
            application=restricted_dot_app,
            _org_associations='edx',
            _allowed_scopes='certficates:read'
        )
        self.restricted_dot_access_token = dot_models.AccessToken.objects.create(
            user=self.student,
            application=restricted_dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='certificates:read',
            token='29MGyP3OaQYHmpT1lK7Q6MMNAZsjwF'
        )
        self.restricted_dot_access_token_bad_scope = dot_models.AccessToken.objects.create(
            user=self.student,
            application=restricted_dot_app,
            expires=datetime.utcnow() + timedelta(weeks=1),
            scope='profile',
            token='34MGyP3OaQYHmpT1lK7Q6MMNAZsjwF'
        )

    def get_url(self, username, course_id=None):
        """
        Helper function to create the url for certificates
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_id if course_id else self.course.id,
                'username': username
            }
        )

    def assert_oauth_status(self, access_token, expected_status, course_id=None):
        """
        Helper method for requests with OAUTH token
        """
        self.client.logout()
        auth_header = "Bearer {0}".format(access_token)
        response = self.client.get(
            self.get_url(self.student.username, course_id=course_id),
            HTTP_AUTHORIZATION=auth_header
        )
        self.assertEqual(response.status_code, expected_status)

        return response

    def test_permissions(self):
        """
        Test that only the owner of the certificate can access the url
        """
        # anonymous user
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # another student
        self.client.login(username=self.student_no_cert.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username))
        # gets 404 instead of 403 for security reasons
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})  # pylint: disable=no-member
        self.client.logout()

        # same student of the certificate
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.logout()

        # staff user
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_inactive_user_access(self):
        """
        Verify inactive users - those who have not verified their email addresses -
        are allowed to access the endpoint.
        """
        self.client.login(username=self.student.username, password=USER_PASSWORD)

        self.student.is_active = False
        self.student.save()

        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_dot_valid_accesstoken(self):
        """
        Verify access with a valid Django Oauth Toolkit access token.
        """
        self.assert_oauth_status(self.dot_access_token, status.HTTP_200_OK)

    def test_dot_invalid_accesstoken(self):
        """
        Verify the endpoint is inaccessible for authorization
        attempts made with an invalid OAuth access token.
        """
        self.assert_oauth_status("fooooooooooToken", status.HTTP_401_UNAUTHORIZED)

    def test_invalid_restricted_application(self):
        """
        Verify that we cannot access the API with an access token for a
        RestrictedApplication which does not have the 'certificates:read' scope
        """
        self.assert_oauth_status(
            self.restricted_dot_access_token_bad_scope,
            status.HTTP_403_FORBIDDEN
        )

    def test_valid_restricted_application(self):
        """
        Verify that we can access the API with an access token for a
        RestrictedApplication which does have the 'certificates:read' scope
        """
        response = self.assert_oauth_status(
            self.restricted_dot_access_token,
            status.HTTP_200_OK
        )
        data = json.loads(response.content)
        self.assertEqual(data['course_id'], unicode(self.course.id))

    def test_restricted_application_invalid_org(self):
        """
        Verify that we can access the API with an access token for a
        RestrictedApplication which does have the 'certificates:read' scope
        but we cannot get a certificate data for an org with which we are
        not associated
        """
        response = self.assert_oauth_status(
            self.restricted_dot_access_token,
            status.HTTP_403_FORBIDDEN,
            course_id=self.not_edx_course.id,
        )
        data = json.loads(response.content)
        self.assertEqual(data['error_code'], 'course_org_not_associated_with_calling_application')

    def test_dot_expired_accesstoken(self):
        """
        Verify the endpoint is inaccessible for authorization
        attempts made with an expired OAuth access token.
        """
        # set the expiration date in the past
        self.dot_access_token.expires = datetime.utcnow() - timedelta(weeks=1)
        self.dot_access_token.save()
        self.assert_oauth_status(self.dot_access_token, status.HTTP_401_UNAUTHORIZED)

    def test_no_certificate_for_user(self):
        """
        Test for case with no certificate available
        """
        self.client.login(username=self.student_no_cert.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student_no_cert.username))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)  # pylint: disable=no-member
        self.assertEqual(
            resp.data['error_code'],  # pylint: disable=no-member
            'no_certificate_for_user'
        )

    def test_certificate_for_user(self):
        """
        Tests case user that pulls her own certificate
        """
        self.client.login(username=self.student.username, password=USER_PASSWORD)
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data,  # pylint: disable=no-member
            {
                'username': self.student.username,
                'status': CertificateStatuses.downloadable,
                'grade': '0.88',
                'download_url': 'www.google.com',
                'certificate_type': CourseMode.VERIFIED,
                'course_id': unicode(self.course.id),
            }
        )
