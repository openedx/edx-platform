"""
Tests for the Certificate REST APIs.
"""
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from oauth2_provider import models as dot_models
from rest_framework import status
from rest_framework.test import APITestCase

from certificates.models import CertificateStatuses
from certificates.tests.factories import GeneratedCertificateFactory
from course_modes.models import CourseMode
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

    def get_url(self, username):
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

    def assert_oauth_status(self, access_token, expected_status):
        """
        Helper method for requests with OAUTH token
        """
        self.client.logout()
        auth_header = "Bearer {0}".format(access_token)
        response = self.client.get(self.get_url(self.student.username), HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, expected_status)

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
