import json
import mock

from ddt import data, ddt, file_data
from django.urls import reverse
from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from lms.djangoapps.onboarding.tests.factories import UserFactory

from .constants import (
    CONTACT_EMAIL,
    SELECTED_CONTACTS_LIST,
    SELECTED_CONTACTS_LIST_INDEX,
    SORTED_PLATFORM_CONTACT_LIST_INDEX,
    SORTED_PLATFORM_CONTACT_LIST_KEY,
    SORTED_NON_PLATFORM_CONTACT_LIST_INDEX,
    SORTED_NON_PLATFORM_CONTACT_LIST_KEY,
    UNSORTED_CONTACT_LIST_INDEX
)
from .factories import SmartReferralFactory


@ddt
class SmartReferralInvitationAPIViewTest(APITestCase):

    def setUp(self):
        super(SmartReferralInvitationAPIViewTest, self).setUp()
        self.user = UserFactory()
        self.user.set_password('password')
        self.user.save()
        self.client.login(username=self.user.username, password='password')

    @file_data('data/test_data_invites.json')
    @mock.patch('openedx.features.smart_referral.api_views.task_send_referral_and_toolkit_emails.delay')
    def test_send_initial_emails_and_save_record_success(self, invites_data, mock_task_send_emails):
        """Successfully send referral emails to two users and current user will receive a toolkit email"""

        data = invites_data[SELECTED_CONTACTS_LIST_INDEX][SELECTED_CONTACTS_LIST]
        response = self.client.post(reverse('initial_referral_emails'), data=json.dumps(data),
                                    content_type='application/json')

        contact_emails = [data[0][CONTACT_EMAIL], data[1][CONTACT_EMAIL]]
        mock_task_send_emails.assert_called_once_with(contact_emails=contact_emails, user_email=self.user.email)
        self.assertEqual(response.status_code, HTTP_200_OK)

    @mock.patch('openedx.features.smart_referral.api_views.task_send_referral_and_toolkit_emails.delay')
    @data('This is invalid json', None, '', [], {})
    def test_send_initial_emails_and_save_record_invalid_request_json(self, invalid_json,
                                                                                  mock_task_send_emails):
        """Submit smart referral invitation request with invalid json"""

        response = self.client.post(
            reverse('initial_referral_emails'),
            data=invalid_json,
            content_type='application/json'
        )

        assert not mock_task_send_emails.called
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @file_data('data/test_data_invalid_invites.json')
    @mock.patch('openedx.features.smart_referral.api_views.task_send_referral_and_toolkit_emails.delay')
    def test_send_initial_emails_and_save_record_invalid_request_json_elements(self, invalid_data,
                                                                                           mock_task_send_emails):
        """Submit smart referral invitation request with invalid json elements"""

        response = self.client.post(
            reverse('initial_referral_emails'),
            data=json.dumps(invalid_data[0]),
            content_type='application/json'
        )

        assert not mock_task_send_emails.called
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @file_data('data/test_data_invites.json')
    @mock.patch('openedx.features.smart_referral.api_views.task_send_referral_and_toolkit_emails.delay')
    def test_send_initial_emails_and_save_record_refer_particular_user_once(self, invites_data,
                                                                                        mock_task_send_emails):
        """Submit smart referral invitation request and assert that user can refer other, particular, user only once"""

        data = invites_data[SELECTED_CONTACTS_LIST_INDEX][SELECTED_CONTACTS_LIST][0]
        SmartReferralFactory(user=self.user, contact_email=data[CONTACT_EMAIL])

        response = self.client.post(
            reverse('initial_referral_emails'),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert not mock_task_send_emails.called
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @file_data('data/test_data_invites.json')
    @mock.patch('webpack_loader.loader.WebpackLoader.get_bundle')
    @mock.patch('openedx.features.smart_referral.api_views.task_send_referral_and_toolkit_emails.delay')
    def test_send_initial_emails_and_save_record_login_required(self, invites_data, mock_task_send_emails,
                                                                            mock_bundle):
        """Submit smart referral invitation request without authentication"""

        self.client.logout()

        data = invites_data[SELECTED_CONTACTS_LIST_INDEX][SELECTED_CONTACTS_LIST][0]
        response = self.client.post(
            reverse('initial_referral_emails'),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert not mock_task_send_emails.called
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)


@ddt
class FilterContactsAPIViewTestCases(APITestCase):

    def setUp(self):
        super(FilterContactsAPIViewTestCases, self).setUp()
        self.user = UserFactory()

    @file_data('data/test_data_contacts.json')
    @mock.patch('openedx.features.smart_referral.api_views.sort_contacts_by_org_and_user_domain')
    @mock.patch('openedx.features.smart_referral.api_views.get_platform_contacts_and_non_platform_contacts')
    def test_filter_contacts_api(self, contacts_data,
                                 mock_get_platform_contacts_and_non_platform_contacts,
                                 mock_sort_contacts_by_org_and_user_domain):
        """
        Testcase to test filter contacts api' request and response
        :param contacts_data: Json data that is read from json file provided in test annotation.
        :param mock_get_platform_contacts_and_non_platform_contacts: mocking helper method
        :param mock_sort_contacts_by_org_and_user_domain: mocking helper method
        :return: None
        """
        user_contact_list = contacts_data[UNSORTED_CONTACT_LIST_INDEX]
        platform_contacts = contacts_data[SORTED_PLATFORM_CONTACT_LIST_INDEX][SORTED_PLATFORM_CONTACT_LIST_KEY]
        non_platform_contacts = \
            contacts_data[SORTED_NON_PLATFORM_CONTACT_LIST_INDEX][SORTED_NON_PLATFORM_CONTACT_LIST_KEY]

        mock_get_platform_contacts_and_non_platform_contacts.return_value = (
            platform_contacts, non_platform_contacts
        )
        mock_sort_contacts_by_org_and_user_domain.side_effect = [platform_contacts, non_platform_contacts]

        self.client.login(username=self.user.username, password='test')
        response = self.client.post(reverse('filter_user_contacts'),
                                    data=json.dumps(user_contact_list), content_type='application/json')

        response_dict = json.loads(response.content)
        response_platform_contacts = response_dict['platform_contacts']
        response_non_platform_contacts = response_dict['non_platform_contacts']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(platform_contacts, response_platform_contacts)
        self.assertEqual(non_platform_contacts, response_non_platform_contacts)
