"""Tests for certificate Django models. """
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from nose.plugins.attrib import attr
from path import Path as path

from certificates.models import (
    ExampleCertificate,
    ExampleCertificateSet,
    CertificateHtmlViewConfiguration,
    CertificateTemplateAsset,
    BadgeImageConfiguration,
    EligibleCertificateManager,
    GeneratedCertificate,
    CertificateStatuses,
)
from certificates.tests.factories import GeneratedCertificateFactory
from opaque_keys.edx.locator import CourseLocator
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

FEATURES_INVALID_FILE_PATH = settings.FEATURES.copy()
FEATURES_INVALID_FILE_PATH['CERTS_HTML_VIEW_CONFIG_PATH'] = 'invalid/path/to/config.json'

# pylint: disable=invalid-name
TEST_DIR = path(__file__).dirname()
TEST_DATA_DIR = 'common/test/data/'
PLATFORM_ROOT = TEST_DIR.parent.parent.parent.parent
TEST_DATA_ROOT = PLATFORM_ROOT / TEST_DATA_DIR


@attr('shard_1')
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


@attr('shard_1')
class CertificateHtmlViewConfigurationTest(TestCase):
    """
    Test the CertificateHtmlViewConfiguration model.
    """
    def setUp(self):
        super(CertificateHtmlViewConfigurationTest, self).setUp()
        self.configuration_string = """{
            "default": {
                "url": "http://www.edx.org",
                "logo_src": "http://www.edx.org/static/images/logo.png"
            },
            "honor": {
                "logo_src": "http://www.edx.org/static/images/honor-logo.png"
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
                "logo_src": "http://www.edx.org/static/images/logo.png"
            },
            "honor": {
                "logo_src": "http://www.edx.org/static/images/honor-logo.png"
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


@attr('shard_1')
class BadgeImageConfigurationTest(TestCase):
    """
    Test the validation features of BadgeImageConfiguration.
    """
    def get_image(self, name):
        """
        Get one of the test images from the test data directory.
        """
        return ImageFile(open(TEST_DATA_ROOT / 'badges' / name + '.png'))

    def create_clean(self, file_obj):
        """
        Shortcut to create a BadgeImageConfiguration with a specific file.
        """
        BadgeImageConfiguration(mode='honor', icon=file_obj).full_clean()

    def test_good_image(self):
        """
        Verify that saving a valid badge image is no problem.
        """
        good = self.get_image('good')
        BadgeImageConfiguration(mode='honor', icon=good).full_clean()

    def test_unbalanced_image(self):
        """
        Verify that setting an image with an uneven width and height raises an error.
        """
        unbalanced = ImageFile(self.get_image('unbalanced'))
        self.assertRaises(ValidationError, self.create_clean, unbalanced)

    def test_large_image(self):
        """
        Verify that setting an image that is too big raises an error.
        """
        large = self.get_image('large')
        self.assertRaises(ValidationError, self.create_clean, large)

    def test_no_double_default(self):
        """
        Verify that creating two configurations as default is not permitted.
        """
        BadgeImageConfiguration(mode='test', icon=self.get_image('good'), default=True).save()
        self.assertRaises(
            ValidationError,
            BadgeImageConfiguration(mode='test2', icon=self.get_image('good'), default=True).full_clean
        )


@attr('shard_1')
class CertificateTemplateAssetTest(TestCase):
    """
    Test Assets are uploading/saving successfully for CertificateTemplateAsset.
    """
    def test_asset_file_saving_with_actual_name(self):
        """
        Verify that asset file is saving with actual name, No hash tag should be appended with the asset filename.
        """
        CertificateTemplateAsset(description='test description', asset=SimpleUploadedFile(
            'picture1.jpg',
            'these are the file contents!')).save()
        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(certificate_template_asset.asset, 'certificate_template_assets/1/picture1.jpg')

        # Now save asset with same file again, New file will be uploaded after deleting the old one with the same name.
        certificate_template_asset.asset = SimpleUploadedFile('picture1.jpg', 'file contents')
        certificate_template_asset.save()
        self.assertEqual(certificate_template_asset.asset, 'certificate_template_assets/1/picture1.jpg')

        # Now replace the asset with another file
        certificate_template_asset.asset = SimpleUploadedFile('picture2.jpg', 'file contents')
        certificate_template_asset.save()

        certificate_template_asset = CertificateTemplateAsset.objects.get(id=1)
        self.assertEqual(certificate_template_asset.asset, 'certificate_template_assets/1/picture2.jpg')


@attr('shard_1')
class EligibleCertificateManagerTest(SharedModuleStoreTestCase):
    """
    Test the GeneratedCertificate model's object manager for filtering
    out ineligible certs.
    """

    @classmethod
    def setUpClass(cls):
        super(EligibleCertificateManagerTest, cls).setUpClass()
        cls.courses = (CourseFactory(), CourseFactory())

    def setUp(self):
        super(EligibleCertificateManagerTest, self).setUp()
        self.user = UserFactory()
        self.eligible_cert = GeneratedCertificateFactory.create(
            status=CertificateStatuses.downloadable,
            user=self.user,
            course_id=self.courses[0].id  # pylint: disable=no-member
        )
        self.ineligible_cert = GeneratedCertificateFactory.create(
            status=CertificateStatuses.audit_passing,
            user=self.user,
            course_id=self.courses[1].id  # pylint: disable=no-member
        )

    def test_filter_ineligible_certificates(self):
        """
        Verify that the EligibleCertificateManager filters out
        certificates marked as ineligible, and that the default object
        manager for GeneratedCertificate does not filter them out.
        """
        self.assertEqual(list(GeneratedCertificate.eligible_certificates.filter(user=self.user)), [self.eligible_cert])
        self.assertEqual(
            list(GeneratedCertificate.objects.filter(user=self.user)),  # pylint: disable=no-member
            [self.eligible_cert, self.ineligible_cert]
        )
