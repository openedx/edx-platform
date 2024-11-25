"""Tests for LinkedIn Add to Profile configuration. """


from urllib.parse import quote
import ddt

from django.conf import settings
from django.test import TestCase

from lms.djangoapps.certificates.tests.factories import LinkedInAddToProfileConfigurationFactory
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context


@ddt.ddt
class LinkedInAddToProfileUrlTests(TestCase):
    """Tests for URL generation of LinkedInAddToProfileConfig. """

    COURSE_NAME = 'Test Course ☃'
    CERT_URL = 'http://s3.edx/cert'
    SITE_CONFIGURATION = {
        'SOCIAL_SHARING_SETTINGS': {
            'CERTIFICATE_LINKEDIN_MODE_TO_CERT_NAME': {
                'honor': '{platform_name} Honor Code Credential for {course_name}',
                'verified': '{platform_name} Verified Credential for {course_name}',
                'professional': '{platform_name} Professional Credential for {course_name}',
                'no-id-professional': '{platform_name} Professional Credential for {course_name}',
            }
        }
    }

    @ddt.data(
        ('honor', 'Honor+Code+Certificate+for+Test+Course+%E2%98%83'),
        ('verified', 'Verified+Certificate+for+Test+Course+%E2%98%83'),
        ('professional', 'Professional+Certificate+for+Test+Course+%E2%98%83'),
        ('default_mode', 'Certificate+for+Test+Course+%E2%98%83')
    )
    @ddt.unpack
    def test_linked_in_url(self, cert_mode, expected_cert_name):
        config = LinkedInAddToProfileConfigurationFactory()

<<<<<<< HEAD
        # We can switch to this once edx-platform reaches Python 3.8
        # expected_url = (
        #     'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&'
        #     'name={platform}+{cert_name}&certUrl={cert_url}&'
        #     'organizationId={company_identifier}'
        # ).format(
        #     platform=quote(settings.PLATFORM_NAME.encode('utf-8')),
        #     cert_name=expected_cert_name,
        #     cert_url=quote(self.CERT_URL, safe=''),
        #     company_identifier=config.company_identifier,
        # )

        actual_url = config.add_to_profile_url(self.COURSE_NAME, cert_mode, self.CERT_URL)

        # We can switch to this instead of the assertIn once edx-platform reaches Python 3.8
        # There was a problem with dict ordering in the add_to_profile_url function that will go away then.
        # self.assertEqual(actual_url, expected_url)

        assert 'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME' in actual_url
        assert f'&name={quote(settings.PLATFORM_NAME.encode("utf-8"))}+{expected_cert_name}' in actual_url
        assert '&certUrl={cert_url}'.format(cert_url=quote(self.CERT_URL, safe='')) in actual_url
        assert f'&organizationId={config.company_identifier}' in actual_url
=======
        expected_url = (
            'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&'
            'name={platform}+{cert_name}&certUrl={cert_url}&'
            'organizationId={company_identifier}'
        ).format(
            platform=quote(settings.PLATFORM_NAME.encode('utf-8')),
            cert_name=expected_cert_name,
            cert_url=quote(self.CERT_URL, safe=''),
            company_identifier=config.company_identifier,
        )

        actual_url = config.add_to_profile_url(self.COURSE_NAME, cert_mode, self.CERT_URL)

        self.assertEqual(actual_url, expected_url)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @ddt.data(
        ('honor', 'Honor+Code+Credential+for+Test+Course+%E2%98%83'),
        ('verified', 'Verified+Credential+for+Test+Course+%E2%98%83'),
        ('professional', 'Professional+Credential+for+Test+Course+%E2%98%83'),
        ('no-id-professional', 'Professional+Credential+for+Test+Course+%E2%98%83'),
        ('default_mode', 'Certificate+for+Test+Course+%E2%98%83')
    )
    @ddt.unpack
    def test_linked_in_url_with_cert_name_override(self, cert_mode, expected_cert_name):
        config = LinkedInAddToProfileConfigurationFactory()

<<<<<<< HEAD
        # We can switch to this once edx-platform reaches Python 3.8
        # expected_url = (
        #     'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&'
        #     'name={platform}+{cert_name}&certUrl={cert_url}&'
        #     'organizationId={company_identifier}'
        # ).format(
        #     platform=quote(settings.PLATFORM_NAME.encode('utf-8')),
        #     cert_name=expected_cert_name,
        #     cert_url=quote(self.CERT_URL, safe=''),
        #     company_identifier=config.company_identifier,
        # )
=======
        expected_url = (
            'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&'
            'name={platform}+{cert_name}&certUrl={cert_url}&'
            'organizationId={company_identifier}'
        ).format(
            platform=quote(settings.PLATFORM_NAME.encode('utf-8')),
            cert_name=expected_cert_name,
            cert_url=quote(self.CERT_URL, safe=''),
            company_identifier=config.company_identifier,
        )
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        with with_site_configuration_context(configuration=self.SITE_CONFIGURATION):
            actual_url = config.add_to_profile_url(self.COURSE_NAME, cert_mode, self.CERT_URL)

<<<<<<< HEAD
            # We can switch to this instead of the assertIn once edx-platform reaches Python 3.8
            # There was a problem with dict ordering in the add_to_profile_url function that will go away then.
            # self.assertEqual(actual_url, expected_url)

            assert 'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME' in actual_url
            assert f'&name={quote(settings.PLATFORM_NAME.encode("utf-8"))}+{expected_cert_name}' in actual_url
            assert '&certUrl={cert_url}'.format(cert_url=quote(self.CERT_URL, safe='')) in actual_url
            assert f'&organizationId={config.company_identifier}' in actual_url
=======
        self.assertEqual(actual_url, expected_url)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
