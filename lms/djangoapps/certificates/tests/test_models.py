"""Tests for certificate Django models. """
from django.test import TestCase

from opaque_keys.edx.locator import CourseLocator
from certificates.models import (
    ExampleCertificate,
    ExampleCertificateSet
)


class ExampleCertificateTest(TestCase):
    """Tests for the ExampleCertificate model. """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')

    DESCRIPTION = 'test'
    TEMPLATE = 'test.pdf'
    DOWNLOAD_URL = 'http://www.example.com'
    ERROR_REASON = 'Kaboom!'

    def setUp(self):
        super(ExampleCertificateTest, self).setUp()
        self.cert_set = ExampleCertificateSet.objects.create(course_key=self.COURSE_KEY)
        self.cert = ExampleCertificate.objects.create(
            example_cert_set=self.cert_set,
            description=self.DESCRIPTION,
            template=self.TEMPLATE
        )

    def test_update_status_success(self):
        self.cert.update_status(
            ExampleCertificate.STATUS_SUCCESS,
            download_url=self.DOWNLOAD_URL
        )
        self.assertEqual(
            self.cert.status_dict,
            {
                'description': self.DESCRIPTION,
                'status': ExampleCertificate.STATUS_SUCCESS,
                'download_url': self.DOWNLOAD_URL
            }
        )

    def test_update_status_error(self):
        self.cert.update_status(
            ExampleCertificate.STATUS_ERROR,
            error_reason=self.ERROR_REASON
        )
        self.assertEqual(
            self.cert.status_dict,
            {
                'description': self.DESCRIPTION,
                'status': ExampleCertificate.STATUS_ERROR,
                'error_reason': self.ERROR_REASON
            }
        )

    def test_update_status_invalid(self):
        with self.assertRaisesRegexp(ValueError, 'status'):
            self.cert.update_status('invalid')

    def test_latest_status_unavailable(self):
        # Delete any existing statuses
        ExampleCertificateSet.objects.all().delete()

        # Verify that the "latest" status is None
        result = ExampleCertificateSet.latest_status(self.COURSE_KEY)
        self.assertIs(result, None)

    def test_latest_status_is_course_specific(self):
        other_course = CourseLocator(org='other', course='other', run='other')
        result = ExampleCertificateSet.latest_status(other_course)
        self.assertIs(result, None)
