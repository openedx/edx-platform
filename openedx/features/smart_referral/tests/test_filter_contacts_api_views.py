import json
import mock

from ddt import ddt, file_data
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.onboarding.tests.factories import UserFactory

from .constants import (
    UNSORTED_CONTACT_LIST_INDEX,
    SORTED_PLATFORM_CONTACT_LIST_INDEX,
    SORTED_PLATFORM_CONTACT_LIST_KEY,
    SORTED_NON_PLATFORM_CONTACT_LIST_INDEX,
    SORTED_NON_PLATFORM_CONTACT_LIST_KEY
)


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
