"""
Test Microsite database backends.
"""
import logging
from mock import patch

from django.conf import settings

from microsite_configuration.backends.base import (
    BaseMicrositeBackend,
    BaseMicrositeTemplateBackend,
)
from microsite_configuration import microsite
from microsite_configuration.models import (
    Microsite,
    MicrositeHistory,
    MicrositeTemplate,
)
from microsite_configuration.tests.tests import (
    DatabaseMicrositeTestCase,
)
from microsite_configuration.tests.factories import (
    SiteFactory,
    MicrositeFactory,
    MicrositeTemplateFactory,
)

log = logging.getLogger(__name__)


@patch(
    'microsite_configuration.microsite.BACKEND',
    microsite.get_backend(
        'microsite_configuration.backends.database.DatabaseMicrositeBackend', BaseMicrositeBackend
    )
)
class DatabaseMicrositeBackendTests(DatabaseMicrositeTestCase):
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
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertEqual(microsite.get_value('email_from_address'), self.microsite.values['email_from_address'])

    def test_is_request_in_microsite(self):
        """
        Tests microsite.is_request_in_microsite works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertTrue(microsite.is_request_in_microsite())

    def test_get_dict(self):
        """
        Tests microsite.get_dict works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertEqual(microsite.get_dict('nested_dict'), self.microsite.values['nested_dict'])

    def test_has_override_value(self):
        """
        Tests microsite.has_override_value works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertTrue(microsite.has_override_value('platform_name'))

    def test_get_value_for_org(self):
        """
        Tests microsite.get_value_for_org works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertEqual(
            microsite.get_value_for_org(self.microsite.get_organizations()[0], 'platform_name'),
            self.microsite.values['platform_name']
        )

    def test_get_all_orgs(self):
        """
        Tests microsite.get_all_orgs works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertEqual(
            microsite.get_all_orgs(),
            set(self.microsite.get_organizations())
        )

    def test_clear(self):
        """
        Tests microsite.clear works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        self.assertEqual(
            microsite.get_value('platform_name'),
            self.microsite.values['platform_name']
        )
        microsite.clear()
        self.assertIsNone(microsite.get_value('platform_name'))

    def test_enable_microsites_pre_startup(self):
        """
        Tests microsite.test_enable_microsites_pre_startup works as expected.
        """
        # remove microsite root directory paths first
        settings.DEFAULT_TEMPLATE_ENGINE['DIRS'] = [
            path for path in settings.DEFAULT_TEMPLATE_ENGINE['DIRS']
            if path != settings.MICROSITE_ROOT_DIR
        ]
        with patch.dict('django.conf.settings.FEATURES', {'USE_MICROSITES': False}):
            microsite.enable_microsites_pre_startup(log)
            self.assertNotIn(settings.MICROSITE_ROOT_DIR, settings.DEFAULT_TEMPLATE_ENGINE['DIRS'])
        with patch.dict('django.conf.settings.FEATURES', {'USE_MICROSITES': True}):
            microsite.enable_microsites_pre_startup(log)
            self.assertIn(settings.MICROSITE_ROOT_DIR, settings.DEFAULT_TEMPLATE_ENGINE['DIRS'])
            self.assertIn(settings.MICROSITE_ROOT_DIR, settings.MAKO_TEMPLATES['main'])

    @patch('openedx.core.djangoapps.edxmako.paths.add_lookup')
    def test_enable_microsites(self, add_lookup):
        """
        Tests microsite.enable_microsites works as expected.
        """
        # remove microsite root directory paths first
        settings.STATICFILES_DIRS = [
            path for path in settings.STATICFILES_DIRS
            if path != settings.MICROSITE_ROOT_DIR
        ]
        with patch.dict('django.conf.settings.FEATURES', {'USE_MICROSITES': False}):
            microsite.enable_microsites(log)
            self.assertNotIn(settings.MICROSITE_ROOT_DIR, settings.STATICFILES_DIRS)
            add_lookup.assert_not_called()
        with patch.dict('django.conf.settings.FEATURES', {'USE_MICROSITES': True}):
            microsite.enable_microsites(log)
            self.assertIn(settings.MICROSITE_ROOT_DIR, settings.STATICFILES_DIRS)

    def test_get_all_configs(self):
        """
        Tests microsite.get_all_config works as expected.
        """
        microsite.set_by_domain(self.microsite.site.domain)
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
        new_microsite = MicrositeFactory.create(key="test_microsite2")
        new_microsite.site = SiteFactory.create(domain='test.microsite2.com')
        # This would update microsite so we test MicrositeHistory has old microsite
        new_microsite.save()
        self.assertEqual(MicrositeHistory.objects.all().count(), 2)
        with self.assertRaises(Exception):
            microsite.set_by_domain('test.microsite2.com')

    def test_has_configuration_set(self):
        """
        Tests microsite.has_configuration_set works as expected on this backend.
        """
        self.assertTrue(microsite.BACKEND.has_configuration_set())

        Microsite.objects.all().delete()
        self.assertFalse(microsite.BACKEND.has_configuration_set())


@patch(
    'microsite_configuration.microsite.TEMPLATES_BACKEND',
    microsite.get_backend(
        'microsite_configuration.backends.database.DatabaseMicrositeTemplateBackend', BaseMicrositeTemplateBackend
    )
)
class DatabaseMicrositeTemplateBackendTests(DatabaseMicrositeTestCase):
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
        microsite.set_by_domain(self.microsite.site.domain)
        template = microsite.get_template('about.html')
        self.assertIsNone(template)

    def test_microsite_get_template(self):
        """
        Test microsite.get_template return appropriate template.
        """
        microsite.set_by_domain(self.microsite.site.domain)
        template = microsite.get_template('about.html')
        self.assertIn('About this microsite', template.render())
