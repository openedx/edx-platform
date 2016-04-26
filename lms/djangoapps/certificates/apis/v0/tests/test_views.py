"""
Tests for the Certificate REST APIs.
"""
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from certificates.models import CertificateStatuses
from certificates.tests.factories import GeneratedCertificateFactory
from course_modes.models import CourseMode
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


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

        self.student = UserFactory.create(password='test')
        self.student_no_cert = UserFactory.create(password='test')
        self.staff_user = UserFactory.create(password='test', is_staff=True)

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
            grade="0.88"
        )

        self.namespaced_url = 'certificates_api:v0:certificates:detail'

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

    def test_permissions(self):
        """
        Test that only the owner of the certificate can access the url
        """
        # anonymous user
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # another student
        self.client.login(username=self.student_no_cert.username, password='test')
        resp = self.client.get(self.get_url(self.student.username))
        # gets 404 instead of 403 for security reasons
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {u'detail': u'Not found.'})  # pylint: disable=no-member
        self.client.logout()

        # same student of the certificate
        self.client.login(username=self.student.username, password='test')
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.logout()

        # staff user
        self.client.login(username=self.staff_user.username, password='test')
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_no_certificate_for_user(self):
        """
        Test for case with no certificate available
        """
        self.client.login(username=self.student_no_cert.username, password='test')
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
        self.client.login(username=self.student.username, password='test')
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
