"""Tests for the create_fake_certs management command. """
from django.test import TestCase
from django.core.management.base import CommandError
from nose.plugins.attrib import attr

from opaque_keys.edx.locator import CourseLocator
from student.tests.factories import UserFactory
from certificates.management.commands import create_fake_cert
from certificates.models import GeneratedCertificate


@attr(shard=1)
class CreateFakeCertTest(TestCase):
    """Tests for the create_fake_certs management command. """

    USERNAME = "test"
    COURSE_KEY = CourseLocator(org='edX', course='DemoX', run='Demo_Course')

    def setUp(self):
        super(CreateFakeCertTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME)

    def test_create_fake_cert(self):
        # No existing cert, so create it
        self._run_command(
            self.USERNAME,
            unicode(self.COURSE_KEY),
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
            unicode(self.COURSE_KEY),
            cert_mode='honor'
        )
        cert = GeneratedCertificate.eligible_certificates.get(user=self.user, course_id=self.COURSE_KEY)
        self.assertEqual(cert.mode, 'honor')

    def test_too_few_args(self):
        with self.assertRaisesRegexp(CommandError, 'Usage'):
            self._run_command(self.USERNAME)

    def _run_command(self, *args, **kwargs):
        """Run the management command to generate a fake cert. """
        command = create_fake_cert.Command()
        return command.handle(*args, **kwargs)
