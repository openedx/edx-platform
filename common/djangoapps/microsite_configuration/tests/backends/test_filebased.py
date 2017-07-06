"""
Test Microsite filebased backends.
"""
import unittest
from mock import patch

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from microsite_configuration.backends.base import (
    BaseMicrositeBackend,
    BaseMicrositeTemplateBackend,
)
from microsite_configuration import microsite
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@patch(
    'microsite_configuration.microsite.BACKEND',
    microsite.get_backend(
        'microsite_configuration.backends.filebased.FilebasedMicrositeBackend', BaseMicrositeBackend
    )
)
class FilebasedMicrositeBackendTests(TestCase):
    """
    Go through and test the FilebasedMicrositeBackend class
    """
    def setUp(self):
        super(FilebasedMicrositeBackendTests, self).setUp()
        self.microsite_subdomain = 'test-site'

    def tearDown(self):
        super(FilebasedMicrositeBackendTests, self).tearDown()
        microsite.clear()

    def test_get_value(self):
        """
        Tests microsite.get_value works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertEqual(microsite.get_value('platform_name'), 'Test Site')

    def test_is_request_in_microsite(self):
        """
        Tests microsite.is_request_in_microsite works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertTrue(microsite.is_request_in_microsite())

    def test_has_override_value(self):
        """
        Tests microsite.has_override_value works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertTrue(microsite.has_override_value('platform_name'))

    def test_get_value_for_org(self):
        """
        Tests microsite.get_value_for_org works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertEqual(
            microsite.get_value_for_org('TestSiteX', 'platform_name'),
            'Test Site'
        )

        # if no config is set
        microsite.clear()
        with patch('django.conf.settings.MICROSITE_CONFIGURATION', False):
            self.assertEqual(
                microsite.get_value_for_org('TestSiteX', 'platform_name', 'Default Value'),
                'Default Value'
            )

    def test_get_all_orgs(self):
        """
        Tests microsite.get_all_orgs works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertEqual(
            microsite.get_all_orgs(),
            set(['TestSiteX', 'LogistrationX'])
        )

        # if no config is set
        microsite.clear()
        with patch('django.conf.settings.MICROSITE_CONFIGURATION', False):
            self.assertEqual(
                microsite.get_all_orgs(),
                set()
            )

    def test_clear(self):
        """
        Tests microsite.clear works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertEqual(
            microsite.get_value('platform_name'),
            'Test Site'
        )
        microsite.clear()
        self.assertIsNone(microsite.get_value('platform_name'))

    def test_get_all_configs(self):
        """
        Tests microsite.get_all_config works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        configs = microsite.get_all_config()
        self.assertEqual(len(configs.keys()), 3)

    def test_set_config_by_domain(self):
        """
        Tests microsite.set_config_by_domain works as expected.
        """
        microsite.clear()
        # if microsite config does not exist default config should be used
        microsite.set_by_domain('unknown')
        self.assertEqual(microsite.get_value('university'), 'default_university')

    def test_has_configuration_set(self):
        """
        Tests microsite.has_configuration_set works as expected.
        """
        self.assertTrue(microsite.BACKEND.has_configuration_set())

        with patch('django.conf.settings.MICROSITE_CONFIGURATION', {}):
            self.assertFalse(microsite.BACKEND.has_configuration_set())


@patch(
    'microsite_configuration.microsite.TEMPLATES_BACKEND',
    microsite.get_backend(
        'microsite_configuration.backends.filebased.FilebasedMicrositeTemplateBackend', BaseMicrositeTemplateBackend
    )
)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class FilebasedMicrositeTemplateBackendTests(ModuleStoreTestCase):
    """
    Go through and test the FilebasedMicrositeTemplateBackend class
    """
    def setUp(self):
        super(FilebasedMicrositeTemplateBackendTests, self).setUp()
        self.microsite_subdomain = 'test-site'
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")

    def test_get_template_path(self):
        """
        Tests get template path works for both relative and absolute paths.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        CourseEnrollmentFactory(
            course_id=self.course.id,
            user=self.user
        )

        response = self.client.get(
            reverse('syllabus', args=[unicode(self.course.id)]),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME,
        )

        self.assertContains(response, "Microsite relative path template contents")
        self.assertContains(response, "Microsite absolute path template contents")
