"""Test models for credentials service app."""
from path import Path

from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from opaque_keys.edx.locator import CourseLocator

from openedx.core.djangoapps.credentials_service.models import (
    CertificateTemplateAsset, CourseCertificate,
    ProgramCertificate, Signatory, SiteConfiguration
)

# pylint: disable=invalid-name
TEST_DIR = Path(__file__).dirname()
TEST_DATA_DIR = 'common/test/data/'
PLATFORM_ROOT = TEST_DIR.parent.parent.parent.parent.parent
TEST_DATA_ROOT = PLATFORM_ROOT / TEST_DATA_DIR


class TestSiteConfiguration(TestCase):
    """Test SiteConfiguration Model."""
    def setUp(self):
        super(TestSiteConfiguration, self).setUp()
        self.site = Site.objects.create(domain='test', name='test')
        self.lms_url_root = 'http://edx.org'

    def test_unicode_value(self):
        """Test unicode value."""
        site_configuration = SiteConfiguration.objects.create(
            site=self.site, lms_url_root=self.lms_url_root, theme_scss_path='test.scss'
        )
        self.assertEqual(unicode(site_configuration), 'Site Configuration ' + unicode(self.site))


class TestSignatory(TestCase):
    """Test Signatory model."""
    def get_image(self, name):
        """Get one of the test images from the test data directory."""
        return ImageFile(open(TEST_DATA_ROOT / 'credentials' / name + '.png'))

    def create_clean(self, file_obj):
        """
        Shortcut to create a Signatory with a specific file.
        """
        Signatory(name='test_signatory', title='Test Signatory', image=file_obj).full_clean()

    def test_good_image(self):
        """Verify that saving a valid signatory image is no problem."""
        good_image = self.get_image('good')
        Signatory(name='test_signatory', title='Test Signatory', image=good_image).full_clean()

    def test_large_image(self):
        """Upload of large image size should raise validation exception."""
        large_image = self.get_image('large')
        self.assertRaises(ValidationError, self.create_clean, large_image)


class TestCertificateTemplateAsset(TestCase):
    """
    Test Assets are uploading/saving successfully for CertificateTemplateAsset.
    """
    def test_asset_file_saving(self):
        """
        Verify that asset file is saving with actual name and on correct path.
        """
        CertificateTemplateAsset(name='test name', asset_file=SimpleUploadedFile(
            'picture1.jpg',
            'file contents!')).save()
        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(
            certificate_template_asset.asset_file, 'certificate_template_assets/1/picture1.jpg'
        )

        # Now replace the asset with another file
        certificate_template_asset.asset_file = SimpleUploadedFile('picture2.jpg', 'file contents')
        certificate_template_asset.save()

        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(
            certificate_template_asset.asset_file, 'certificate_template_assets/1/picture2.jpg'
        )

    def test_unicode_value(self):
        """Test unicode value is correct."""
        CertificateTemplateAsset(name='test name', asset_file=SimpleUploadedFile(
            'picture1.jpg',
            'file contents!')).save()
        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(unicode(certificate_template_asset), 'test name')


class TestCertificates(TestCase):
    """Basic setup for certificate tests."""
    def setUp(self):
        super(TestCertificates, self).setUp()
        self.site = Site.objects.create(domain='test', name='test')
        Signatory(name='test name', title='test title', image=SimpleUploadedFile(
            'picture1.jpg',
            'image contents!')).save()
        self.signatory = Signatory.objects.get(id=1)


class TestProgramCertificate(TestCertificates):
    """Test Program Certificate model."""

    def test_unicode_value(self):
        """Test unicode value is correct."""
        program_certificate = ProgramCertificate.objects.create(site=self.site, is_active=True, program_id='123')
        program_certificate.signatories.add(self.signatory)
        self.assertEqual(unicode(program_certificate), 'ProgramCertificate for program 123')


class TestCourseCertificate(TestCertificates):
    """Test Course Certificate model."""

    def setUp(self):
        super(TestCourseCertificate, self).setUp()
        self.course_key = CourseLocator(org='test', course='test', run='test')

    def test_unicode_value(self):
        """Test unicode value is correct."""
        course_certificate = CourseCertificate.objects.create(
            site=self.site, is_active=True, course_id=self.course_key, certificate_type='Honor'
        )
        course_certificate.signatories.add(self.signatory)
        self.assertEqual(unicode(course_certificate), 'CourseCertificate ' + unicode(self.course_key) + ', Honor')

    def test_invalid_course_key(self):
        """Test Validation Error occurs for invalid course key."""
        with self.assertRaises(ValidationError) as context:
            CourseCertificate(
                site=self.site, is_active=True, course_id='test_invalid', certificate_type='Honor'
            ).full_clean()

        self.assertEqual(context.exception.message_dict, {'course_id': ['Invalid course key.']})
