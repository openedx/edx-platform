# -*- coding: utf-8 -*-
"""
Test Microsite backends.
"""
import logging
from mock import patch

from django.conf import settings
from django.test import TestCase

from microsite_configuration.backends.base import BaseMicrositeBackend, BaseMicrositeTemplateBackend
from microsite_configuration import microsite
from microsite_configuration.models import (
    Microsite,
    MicrositeTemplate,
    MicrositeHistory,
)
from microsite_configuration.tests.tests import (
    DatabaseMicrositeTest,
)
from microsite_configuration.tests.factories import (
    MicrositeFactory,
    MicrositeTemplateFactory,
)

log = logging.getLogger(__name__)


class NullBackend(BaseMicrositeBackend):
    """
    A class that does nothing but inherit from the base class
    """
    def set_config_by_domain(self, domain):
        """
        For a given request domain, find a match in our microsite configuration
        and make it available to the complete django request process
        """
        return super(NullBackend, self).set_config_by_domain(domain)

    def get_template_path(self, relative_path, **kwargs):
        """
        Returns a path (string) to a Mako template, which can either be in
        an override or will just return what is passed in which is expected to be a string
        """
        return super(NullBackend, self).get_template_path(relative_path, **kwargs)

    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        return super(NullBackend, self).get_value(val_name, default, **kwargs)

    def get_dict(self, dict_name, default=None, **kwargs):
        """
        Returns a dictionary product of merging the request's microsite and
        the default value.
        This can be used, for example, to return a merged dictonary from the
        settings.FEATURES dict, including values defined at the microsite
        """
        return super(NullBackend, self).get_dict(dict_name, default, **kwargs)

    def is_request_in_microsite(self):
        """
        This will return True/False if the current request is a request within a microsite
        """
        return super(NullBackend, self).is_request_in_microsite()

    def has_override_value(self, val_name):
        """
        Returns True/False whether a Microsite has a definition for the
        specified named value
        """
        return super(NullBackend, self).has_override_value(val_name)

    def get_all_config(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        return super(NullBackend, self).get_all_config()

    def get_value_for_org(self, org, val_name, default=None):
        """
        This returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        return super(NullBackend, self).get_value_for_org(org, val_name, default)

    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within a microsite. This can be used,
        for example, to do filtering
        """
        return super(NullBackend, self).get_all_orgs()

    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        return super(NullBackend, self).clear()


class BaseBackendTests(TestCase):
    """
    Go through and test the base abstract class
    """

    def test_cant_create_instance(self):
        """
        We shouldn't be able to create an instance of the base abstract class
        """

        with self.assertRaises(TypeError):
            BaseMicrositeBackend()  # pylint: disable=abstract-class-instantiated

    def test_not_yet_implemented(self):
        """
        Make sure all base methods raise a NotImplementedError exception
        """

        backend = NullBackend()

        with self.assertRaises(NotImplementedError):
            backend.set_config_by_domain(None)

        with self.assertRaises(NotImplementedError):
            backend.get_value(None, None)

        with self.assertRaises(NotImplementedError):
            backend.get_dict(None, None)

        with self.assertRaises(NotImplementedError):
            backend.is_request_in_microsite()

        with self.assertRaises(NotImplementedError):
            backend.has_override_value(None)

        with self.assertRaises(NotImplementedError):
            backend.get_all_config()

        with self.assertRaises(NotImplementedError):
            backend.clear()

        with self.assertRaises(NotImplementedError):
            backend.get_value_for_org(None, None, None)

        with self.assertRaises(NotImplementedError):
            backend.get_all_orgs()


@patch(
    'microsite_configuration.microsite.BACKEND',
    microsite.get_backend('microsite_configuration.backends.database.DatabaseMicrositeBackend', BaseMicrositeBackend)
)
class DatabaseMicrositeBackendTests(DatabaseMicrositeTest):
    """
    Go through and test the DatabaseMicrositeBackend  class
    """
    def setUp(self):
        super(DatabaseMicrositeBackendTests, self).setUp()

    def tearDown(self):
        super(DatabaseMicrositeBackendTests, self).tearDown()
        microsite.clear()

    def test_get_value(self):
        """
        Tests microsite.get_value works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertEqual(microsite.get_value('email_from_address'), self.microsite.values['email_from_address'])

    def test_is_request_in_microsite(self):
        """
        Tests microsite.is_request_in_microsite works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertTrue(microsite.is_request_in_microsite())

    def test_get_dict(self):
        """
        Tests microsite.get_dict works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertEqual(microsite.get_dict('nested_dict'), self.microsite.values['nested_dict'])

    def test_has_override_value(self):
        """
        Tests microsite.has_override_value works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertTrue(microsite.has_override_value('platform_name'))

    def test_get_value_for_org(self):
        """
        Tests microsite.get_value_for_org works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertEqual(
            microsite.get_value_for_org(self.microsite.get_orgs()[0], 'platform_name'),
            self.microsite.values['platform_name']
        )

    def test_get_all_orgs(self):
        """
        Tests microsite.get_all_orgs works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertEqual(
            microsite.get_all_orgs(),
            set(self.microsite.get_orgs())
        )

    def test_clear(self):
        """
        Tests microsite.clear works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        self.assertEqual(
            microsite.get_value('platform_name'),
            self.microsite.values['platform_name']
        )
        microsite.clear()
        self.assertIsNone(microsite.get_value('platform_name'))

    def test_enable_microsites(self):
        """
        Tests microsite.enable_microsites works as expected.
        """
        # remove microsite root directory paths first
        settings.DEFAULT_TEMPLATE_ENGINE['DIRS'] = [
            path for path in settings.DEFAULT_TEMPLATE_ENGINE['DIRS']
            if path != settings.MICROSITE_ROOT_DIR
        ]
        with patch.dict('django.conf.settings.FEATURES', {'USE_MICROSITES': False}):
            microsite.enable_microsites(log)
            self.assertNotIn(settings.MICROSITE_ROOT_DIR, settings.DEFAULT_TEMPLATE_ENGINE['DIRS'])
        with patch.dict('django.conf.settings.FEATURES', {'USE_MICROSITES': True}):
            microsite.enable_microsites(log)
            self.assertIn(settings.MICROSITE_ROOT_DIR, settings.DEFAULT_TEMPLATE_ENGINE['DIRS'])

    def test_get_all_configs(self):
        """
        Tests microsite.get_all_config works as expected.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        configs = microsite.get_all_config()
        self.assertEqual(len(configs.keys()), 1)
        self.assertEqual(configs[self.microsite.key], self.microsite.values)

    def test_set_config_by_domain(self):
        """
        Tests microsite.set_config_by_domain works as expected.
        """
        microsite.clear()
        # if microsite config does not exist
        microsite.set_by_domain('unknown')
        self.assertIsNone(microsite.get_value('platform_name'))

        # if no microsite exists
        Microsite.objects.all().delete()
        microsite.clear()
        microsite.set_by_domain('unknown')
        self.assertIsNone(microsite.get_value('platform_name'))

        # if microsite site has no organization it should raise exception
        new_microsite = MicrositeFactory.create()
        new_microsite.key = 'test_microsite'
        new_microsite.subdomain = 'microsite.test'
        # This would update microsite so we test MicrositeHistory has old microsite
        new_microsite.save()
        self.assertEqual(MicrositeHistory.objects.all().count(), 2)
        with self.assertRaises(Exception):
            microsite.set_by_domain('microsite.test')


@patch(
    'microsite_configuration.microsite.BACKEND',
    microsite.get_backend(
        'microsite_configuration.backends.filebased.SettingsFileMicrositeBackend', BaseMicrositeBackend
    )
)
class FilebasedMicrositeBackendTests(TestCase):
    """
    Go through and test the SettingsFileMicrositeBackend  class
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


@patch(
    'microsite_configuration.microsite.TEMPLATES_BACKEND',
    microsite.get_backend(
        'microsite_configuration.backends.database.DatabaseMicrositeTemplateBackend', BaseMicrositeTemplateBackend
    )
)
class DatabaseMicrositeTemplateBackendTests(DatabaseMicrositeTest):
    """
    Go through and test the DatabaseMicrositeTemplateBackend class
    """
    def setUp(self):
        super(DatabaseMicrositeTemplateBackendTests, self).setUp()
        MicrositeTemplateFactory.create(
            microsite=self.microsite,
            template_uri='about.html',
            template="""
            <html>
                <body>
                About this microsite.
                </body>
            </html>
            """,
        )

    def tearDown(self):
        super(DatabaseMicrositeTemplateBackendTests, self).tearDown()
        microsite.clear()

    def test_microsite_get_template_when_no_template_exists(self):
        """
        Test microsite.get_template return None if there is not template in DB.
        """
        MicrositeTemplate.objects.all().delete()
        microsite.set_by_domain(self.microsite.subdomain)
        template = microsite.get_template('about.html')
        self.assertIsNone(template)

    def test_microsite_get_template(self):
        """
        Test microsite.get_template return appropriate template.
        """
        microsite.set_by_domain(self.microsite.subdomain)
        template = microsite.get_template('about.html')
        self.assertIn('About this microsite', template.render())
