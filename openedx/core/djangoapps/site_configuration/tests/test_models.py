"""
Tests for site configuration's django models.
"""

from django.test import TestCase
from django.db import IntegrityError, transaction
from django.contrib.sites.models import Site

from openedx.core.djangoapps.site_configuration.models import SiteConfigurationHistory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory


class SiteConfigurationTests(TestCase):
    """
    Tests for SiteConfiguration and its signals/receivers.
    """
    domain = 'site_configuration_post_save_receiver_example.com'
    name = 'site_configuration_post_save_receiver_example'

    @classmethod
    def setUpClass(cls):
        super(SiteConfigurationTests, cls).setUpClass()
        cls.site, _ = Site.objects.get_or_create(domain=cls.domain, name=cls.domain)

    def test_site_configuration_post_save_receiver(self):
        """
        Test that and entry is added to SiteConfigurationHistory model each time a new
        SiteConfiguration is added.
        """
        # add SiteConfiguration to database
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
        )

        # Verify an entry to SiteConfigurationHistory was added.
        site_configuration_history = SiteConfigurationHistory.objects.filter(
            site=site_configuration.site,
        ).all()

        # Make sure an entry (and only one entry) is saved for SiteConfiguration
        self.assertEqual(len(site_configuration_history), 1)

    def test_site_configuration_post_update_receiver(self):
        """
        Test that and entry is added to SiteConfigurationHistory each time a
        SiteConfiguration is updated.
        """
        # add SiteConfiguration to database
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
        )

        site_configuration.values = {'test': 'test'}
        site_configuration.save()

        # Verify an entry to SiteConfigurationHistory was added.
        site_configuration_history = SiteConfigurationHistory.objects.filter(
            site=site_configuration.site,
        ).all()

        # Make sure two entries (one for save and one for update) are saved for SiteConfiguration
        self.assertEqual(len(site_configuration_history), 2)

    def test_no_entry_is_saved_for_errors(self):
        """
        Test that and entry is not added to SiteConfigurationHistory if there is an error while
        saving SiteConfiguration.
        """
        # add SiteConfiguration to database
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
        )

        # Verify an entry to SiteConfigurationHistory was added.
        site_configuration_history = SiteConfigurationHistory.objects.filter(
            site=site_configuration.site,
        ).all()

        # Make sure entry is saved if there is no error
        self.assertEqual(len(site_configuration_history), 1)

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                # try to add a duplicate entry
                site_configuration = SiteConfigurationFactory.create(
                    site=self.site,
                )
        site_configuration_history = SiteConfigurationHistory.objects.filter(
            site=site_configuration.site,
        ).all()

        # Make sure no entry is saved if there an error
        self.assertEqual(len(site_configuration_history), 1)
