# coding=UTF-8
"""Tests for helpers methods of smart referral."""
import mock

from ddt import ddt, file_data
from django.test import TestCase
from lms.djangoapps.onboarding.tests.factories import OrganizationFactory, UserFactory

from .constants import (
    SORTED_PLATFORM_CONTACT_LIST_KEY,
    SORTED_PLATFORM_CONTACT_LIST_INDEX,
    SORTED_NON_PLATFORM_CONTACT_LIST_KEY,
    SORTED_NON_PLATFORM_CONTACT_LIST_INDEX,
    SORTED_CONTACT_LIST_KEY,
    SORTED_CONTACT_LIST_INDEX,
    UNSORTED_CONTACT_LIST_KEY,
    UNSORTED_CONTACT_LIST_INDEX,
)
from .. import helpers as filter_contacts_helpers


@ddt
class FilterContactsAPIViewTestHelpers(TestCase):

    def setUp(self):
        super(FilterContactsAPIViewTestHelpers, self).setUp()

    def test_get_email_domain(self):
        """
        Test email domain, extracted from email address provided to 'get_email_domain' helper method.
        :return: None
        """
        test_email = 'testing.101@test.com'
        expected_output = 'test.com'
        actual_output = filter_contacts_helpers.get_email_domain(test_email)
        self.assertEqual(expected_output, actual_output)

    @file_data('data/test_data_contacts.json')
    def test_sort_contacts_by_org_and_user_domain(self, contacts_data):
        """
        Test sorting of contacts by two criteria first one is organization's admin email domain and
        second one is user's email domain name.
        :param contacts_data: Json data that is read from json file provided in test annotation.
        :return: None
        """
        org_admin_email = 'admin@test.com'
        admin_user = UserFactory(email=org_admin_email)
        org = OrganizationFactory(admin=admin_user)

        user = UserFactory(email='testing.101@edx.com')
        user.extended_profile.organization = org
        user.extended_profile.save()

        contact_list = contacts_data[UNSORTED_CONTACT_LIST_INDEX][UNSORTED_CONTACT_LIST_KEY]
        expected_output = contacts_data[SORTED_CONTACT_LIST_INDEX][SORTED_CONTACT_LIST_KEY]

        actual_output = filter_contacts_helpers.sort_contacts_by_org_and_user_domain(contact_list, user=user)
        self.assertEqual(expected_output, actual_output)

    @file_data('data/test_data_contacts.json')
    def test_get_platform_contacts_and_non_platform_contacts(self, contacts_data):
        """
        Test to get two separated list contacts, one of those contacts who are
        registered on our platform, second one are not.
        :param contacts_data: Json data that is read from json file provided in test annotation.
        :return: None
        """
        UserFactory(email='testing.101@test.com')
        UserFactory(email='testing.201@edx.com')

        contact_list = contacts_data[SORTED_CONTACT_LIST_INDEX][SORTED_CONTACT_LIST_KEY]
        expected_output_platform_contacts = \
            contacts_data[SORTED_PLATFORM_CONTACT_LIST_INDEX][SORTED_PLATFORM_CONTACT_LIST_KEY]
        expected_output_non_platform_contacts = \
            contacts_data[SORTED_NON_PLATFORM_CONTACT_LIST_INDEX][SORTED_NON_PLATFORM_CONTACT_LIST_KEY]

        actual_output_platform_contacts, actual_output_non_platform_contacts = \
            filter_contacts_helpers.get_platform_contacts_and_non_platform_contacts(contact_list)

        self.assertEqual(expected_output_platform_contacts, actual_output_platform_contacts)
        self.assertEqual(expected_output_non_platform_contacts, actual_output_non_platform_contacts)

    def test_get_org_admin_email_org_with_admin(self):
        """
        Test to get admin's email of an organization from which user is affiliated
        :return: None
        """
        org_admin_email = 'admin@organization101.com'
        admin_user = UserFactory(email=org_admin_email)
        org = OrganizationFactory(admin=admin_user)

        user = UserFactory(email='testing.101@test.com')
        user.extended_profile.organization = org
        user.extended_profile.save()

        actual_result = filter_contacts_helpers.get_org_admin_email(user)
        self.assertEqual(org_admin_email, actual_result)

    def test_get_org_admin_email_org_without_admin(self):
        """
        Test to get admin's email of an organization from which user is affiliated.
        In this case organization don't have an admin hence resultant email address should be 'None'.
        :return: None
        """
        org = OrganizationFactory()

        user = UserFactory(email='testing.101@test.com')
        user.extended_profile.organization = org
        user.extended_profile.save()

        actual_result = filter_contacts_helpers.get_org_admin_email(user)
        self.assertIsNone(actual_result)

    def test_get_org_admin_email_unaffiliated_user(self):
        """
        Test to get admin's email of an organization from which user isn't affiliated, since
        our user isn't affiliated so resultant email address should be 'None'.
        :return: None
        """
        user = UserFactory(email='testing.101@test.com')
        actual_result = filter_contacts_helpers.get_org_admin_email(user)
        self.assertIsNone(actual_result)
