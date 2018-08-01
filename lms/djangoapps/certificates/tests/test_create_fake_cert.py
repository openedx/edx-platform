"""Tests for the create_fake_certs management command. """

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator
from six import text_type

from lms.djangoapps.certificates.models import GeneratedCertificate
from student.tests.factories import UserFactory


class CreateFakeCertTest(TestCase):
    """Tests for the create_fake_certs management command. """
    shard = 1
    USERNAME = "test"
    COURSE_KEY = CourseLocator(org='edX', course='DemoX', run='Demo_Course')

    def setUp(self):
        super(CreateFakeCertTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME)

    def test_create_fake_cert(self):
        # No existing cert, so create it
        self._run_command(
            self.USERNAME,
            text_type(self.COURSE_KEY),
            cert_mode='verified',
            grade='0.89'
        )
        cert = GeneratedCertificate.eligible_certificates.get(user=self.user, course_id=self.COURSE_KEY)
        self.assertEqual(cert.status, 'downloadable')
        self.assertEqual(cert.mode, 'verified')
        self.assertEqual(cert.grade, '0.89')
        self.assertEqual(cert.download_uuid, 'test')
        self.assertEqual(cert.download_url, 'http://www.example.com')

        # Cert already exists; modify it
        self._run_command(
            self.USERNAME,
            text_type(self.COURSE_KEY),
            cert_mode='honor'
        )
        cert = GeneratedCertificate.eligible_certificates.get(user=self.user, course_id=self.COURSE_KEY)
        self.assertEqual(cert.mode, 'honor')

    def test_too_few_args(self):
        with self.assertRaisesRegexp(CommandError, 'Error: too few arguments'):
            self._run_command(self.USERNAME)

    def _run_command(self, *args, **kwargs):
        """Run the management command to generate a fake cert. """
        return call_command('create_fake_cert', *args, **kwargs)
