"""
Test the sync_hubspot_contacts management command
"""
import json
from datetime import timedelta
from mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.utils.six import StringIO

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.user_api.management.commands.sync_hubspot_contacts import Command as sync_command
from student.models import UserAttribute, UserProfile
from student.tests.factories import UserFactory


@skip_unless_lms
class TestHubspotSyncCommand(TestCase):
    """
    Test sync_hubspot_contacts management command.
    """

    @classmethod
    def setUpClass(cls):
        super(TestHubspotSyncCommand, cls).setUpClass()
        cls.site_config = SiteConfigurationFactory()
        cls.hubspot_site_config = SiteConfigurationFactory.create(
            values={'HUBSPOT_API_KEY': 'test_key'},
        )
        cls.users = []
        cls._create_users(cls.hubspot_site_config)  # users for a site with hubspot integration enabled
        cls._create_users(cls.site_config)

    @classmethod
    def _create_users(cls, site_conf):
        # Create some test users
        for i in range(1, 11):
            profile_meta = {
                "first_name": "First Name{0}".format(i),
                "last_name": "Last Name{0}".format(i),
                "company": "Company{0}".format(i),
                "title": "Title{0}".format(i),
                "state": "State{0}".format(i),
                "country": "US",
            }
            loe = UserProfile.LEVEL_OF_EDUCATION_CHOICES[0][0]
            date_joined = timezone.now() - timedelta(i)
            user = UserFactory(date_joined=date_joined)
            user_profile = user.profile
            user_profile.level_of_education = loe
            user_profile.meta = json.dumps(profile_meta)
            user_profile.save()  # pylint: disable=no-member
            UserAttribute.set_user_attribute(user, 'created_on_site', site_conf.site.domain)
            cls.users.append(user)

    def test_without_any_hubspot_api_key(self):
        """
        Test no recent contact call is made if hubspot integration is not enabled for any site
        """
        orig_values = self.hubspot_site_config.values
        self.hubspot_site_config.values = {}
        self.hubspot_site_config.save()
        last_synced_contact_email = patch.object(sync_command, '_get_last_synced_contact_email')
        mock_last_synced_contact_email = last_synced_contact_email.start()
        call_command('sync_hubspot_contacts')
        self.assertFalse(mock_last_synced_contact_email.called, "Recent contact API should not be called")
        last_synced_contact_email.stop()
        # put values back
        self.hubspot_site_config.values = orig_values
        self.hubspot_site_config.save()

    def test_recent_contact_called(self):
        """
        Test recent contact API is called
        """
        last_synced_contact_email = patch.object(sync_command, '_get_last_synced_contact_email')
        mock_last_synced_contact_email = last_synced_contact_email.start()
        mock_last_synced_contact_email.return_value = None
        call_command('sync_hubspot_contacts')
        self.assertTrue(mock_last_synced_contact_email.called, "Recent contact API should be called")
        last_synced_contact_email.stop()

    def test_with_no_recent_contact_found(self):
        """
        Test if no recent contact found it should sync all contacts
        """
        with patch.object(sync_command, '_get_last_synced_contact_email', return_value=None):
            sync_with_hubspot = patch.object(sync_command, '_sync_with_hubspot')
            mock_sync_with_hubspot = sync_with_hubspot.start()
            out = StringIO()
            call_command('sync_hubspot_contacts', '--initial-sync-days=20', '--batch-size=2', stdout=out)
            output = out.getvalue()
            self.assertIn('Successfully synced users', output)
            self.assertEqual(mock_sync_with_hubspot.call_count, 5)
            sync_with_hubspot.stop()

    def test_with_recent_contact_found(self):
        """
        Test only not synched contacts are synced
        """
        with patch.object(sync_command, '_get_last_synced_contact_email', return_value=self.users[3].email):
            sync_with_hubspot = patch.object(sync_command, '_sync_with_hubspot')
            mock_sync_with_hubspot = sync_with_hubspot.start()
            out = StringIO()
            call_command('sync_hubspot_contacts', '--batch-size=3', stdout=out)
            output = out.getvalue()
            self.assertIn('Successfully synced users', output)
            self.assertEqual(mock_sync_with_hubspot.call_count, 2)
            sync_with_hubspot.stop()
