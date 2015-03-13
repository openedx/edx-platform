"""Tests for certificate Django models. """
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings

from opaque_keys.edx.locator import CourseLocator
from certificates.models import (
    ExampleCertificate,
    ExampleCertificateSet,
    CertificateHtmlViewConfiguration
)

FEATURES_INVALID_FILE_PATH = settings.FEATURES.copy()
FEATURES_INVALID_FILE_PATH['CERTS_HTML_VIEW_CONFIG_PATH'] = 'invalid/path/to/config.json'


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


class CertificateHtmlViewConfigurationTest(TestCase):
    """
    Test the CertificateHtmlViewConfiguration model.
    """
    def setUp(self):
        super(CertificateHtmlViewConfigurationTest, self).setUp()
        self.configuration_string = """{
            "default": {
                "url": "http://www.edx.org",
                "logo_src": "http://www.edx.org/static/images/logo.png",
                "logo_alt": "Valid Certificate"
            },
            "honor": {
                "logo_src": "http://www.edx.org/static/images/honor-logo.png",
                "logo_alt": "Honor Certificate"
            }
        }"""
        self.config = CertificateHtmlViewConfiguration(configuration=self.configuration_string)

    def test_create(self):
        """
        Tests creation of configuration.
        """
        self.config.save()
        self.assertEquals(self.config.configuration, self.configuration_string)

    def test_clean_bad_json(self):
        """
        Tests if bad JSON string was given.
        """
        self.config = CertificateHtmlViewConfiguration(configuration='{"bad":"test"')
        self.assertRaises(ValidationError, self.config.clean)

    def test_get(self):
        """
        Tests get configuration from saved string.
        """
        self.config.enabled = True
        self.config.save()
        expected_config = {
            "default": {
                "url": "http://www.edx.org",
                "logo_src": "http://www.edx.org/static/images/logo.png",
                "logo_alt": "Valid Certificate"
            },
            "honor": {
                "logo_src": "http://www.edx.org/static/images/honor-logo.png",
                "logo_alt": "Honor Certificate"
            }
        }
        self.assertEquals(self.config.get_config(), expected_config)

    def test_get_not_enabled_returns_blank(self):
        """
        Tests get configuration that is not enabled.
        """
        self.config.enabled = False
        self.config.save()
        self.assertEquals(len(self.config.get_config()), 0)

    @override_settings(FEATURES=FEATURES_INVALID_FILE_PATH)
    def test_get_no_database_no_file(self):
        """
        Tests get configuration that is not enabled.
        """
        self.config.configuration = ''
        self.config.save()
        self.assertEquals(self.config.get_config(), {})
