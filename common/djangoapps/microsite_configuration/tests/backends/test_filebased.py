"""
Test Microsite filebased backends.
"""
from mock import patch

from django.test import TestCase

from microsite_configuration.backends.base import (
    BaseMicrositeBackend,
)
from microsite_configuration import microsite


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
        self.microsite_subdomain = 'testmicrosite'

    def tearDown(self):
        super(FilebasedMicrositeBackendTests, self).tearDown()
        microsite.clear()

    def test_get_value(self):
        """
        Tests microsite.get_value works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertEqual(microsite.get_value('platform_name'), 'Test Microsite')

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
            microsite.get_value_for_org('TestMicrositeX', 'platform_name'),
            'Test Microsite'
        )

        # if no config is set
        microsite.clear()
        with patch('django.conf.settings.MICROSITE_CONFIGURATION', False):
            self.assertEqual(
                microsite.get_value_for_org('TestMicrositeX', 'platform_name', 'Default Value'),
                'Default Value'
            )

    def test_get_all_orgs(self):
        """
        Tests microsite.get_all_orgs works as expected.
        """
        microsite.set_by_domain(self.microsite_subdomain)
        self.assertEqual(
            microsite.get_all_orgs(),
            set(['TestMicrositeX', 'LogistrationX'])
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
            'Test Microsite'
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
