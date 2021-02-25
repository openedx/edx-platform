"""
Tests related to the signals.py file of the mailchimp_pipeline app
"""
import json

from django.conf import settings
from django.test import TestCase
from mock import ANY, patch

from lms.djangoapps.onboarding.models import EmailPreference, GranteeOptIn
from lms.djangoapps.onboarding.tests.factories import UserFactory
from mailchimp_pipeline.client import Connection
from mailchimp_pipeline.helpers import get_org_data_for_mandrill
from mailchimp_pipeline.tests.helpers import (
    create_organization,
    create_organization_partner_object,
    generate_mailchimp_url
)


class MailchimpPipelineSignalTestClass(TestCase):
    """
    Tests for signals handlers
    """

    @patch("nodebb.signals.handlers.get_current_request", autospec=True)
    def setUp(self, mocked_nodebb_request):  # pylint: disable=unused-argument, arguments-differ
        super(MailchimpPipelineSignalTestClass, self).setUp()
        patcher = patch('mailchimp_pipeline.client.request', autospec=True)
        self.mock_request = patcher.start()
        self.mock_request.return_value.status_code = 204
        self.addCleanup(patcher.stop)
        self.user = UserFactory(is_staff=False, password='test')

        self.connection = Connection.get_connection()
        self.mail_chimp_root_url = self.connection.root

    def test_sync_user_profile_with_mailchimp(self):
        """
        Test if user profile post-save signal is generated and its handler is sending user profile
        data perfectly to the MailChimp expected URL
        """
        user_profile = self.user.profile
        user_profile.language = 'test_language'
        user_profile.city = 'test_city'
        user_profile.save()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "LANG": user_profile.language,
                "COUNTRY": "",
                "CITY": user_profile.city
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_sync_email_preference_with_mailchimp_optin_false(self):
        """
        Test if email preference post-save signal is generated and its handler is sending email
        preference Opt-in option as False (user does not want to get email updates) to the
        MailChimp expected URL
        """
        email_preference = EmailPreference.objects.get(user=self.user)
        email_preference.opt_in = "no"
        email_preference.save()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "OPTIN": "FALSE"
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_sync_email_preference_with_mailchimp_optin_true(self):
        """
        Test if email preference post-save signal is generated and its handler is sending email preference
        Opt-in option as True (user wants to email updates) to the MailChimp expected URL
        """
        email_preference = EmailPreference.objects.get(user=self.user)
        email_preference.opt_in = "yes"
        email_preference.save()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "OPTIN": "TRUE"
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_sync_email_preference_with_mailchimp_optin_empty(self):
        """
        Test if Email preference post-save signal is generated and its handler is sending email
        preference Opt-in option as an empty string to the MailChimp expected URL
        """
        email_preference = EmailPreference.objects.get(user=self.user)
        email_preference.opt_in = ""
        email_preference.save()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "OPTIN": ""
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_sync_grantee_optin_with_mailchimp(self):
        """
        Test if Grantee Opt-In post-save signal is generated and its handler is sending right data
        to the MailChimp expected URL
        """
        org_partner = create_organization_partner_object(self.user)
        grant_opt_in = GranteeOptIn(user=self.user, agreed=True, organization_partner=org_partner)
        grant_opt_in.save()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "ECHIDNA": 'TRUE',
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    @patch("nodebb.signals.handlers.get_current_request", autospec=True)
    def test_sync_extended_profile_with_mailchimp(self, nodebb_request):  # pylint: disable=unused-argument
        """
        Test if the Extended profile post-save signal is generated and its handler is sending
        user extended profile data perfectly to the MailChimp expected URL
        :param nodebb_request: Mocked request used in function that sync user extended profile with NodeBB
        """
        extended_profile = self.user.extended_profile
        extended_profile.organization = create_organization(self.user)
        extended_profile.save()  # pylint: disable=no-member
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        org_label, org_type, work_area = get_org_data_for_mandrill(extended_profile.organization)
        expected_data = {
            "merge_fields": {
                "ORG": org_label,
                "ORGTYPE": org_type,
                "WORKAREA": work_area
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    @patch("mailchimp_pipeline.signals.handlers.update_org_details_at_mailchimp.delay", autospec=True)
    def test_sync_organization_with_mailchimp(self, mocked_delay):
        """
        Test if Organization post-save signal is generated and the delay of the update_org_details_at_mailchimp
        task is called with right parameters from its handler.
        :param mocked_delay: Mocked task delay to check if task has been called.
        """
        organization = create_organization(self.user)
        org_label, org_type, work_area = get_org_data_for_mandrill(organization)
        mocked_delay.assert_called_with(
            org_label, org_type, work_area, organization.id, settings.MAILCHIMP_LEARNERS_LIST_ID
        )
