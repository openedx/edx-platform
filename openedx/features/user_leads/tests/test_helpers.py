import random

from django.db import IntegrityError
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import ResolverMatch

from mock import patch
from student.tests.factories import AnonymousUserFactory, UserFactory

from ..constants import (
    UTM_CAMPAIGN_KEY,
    UTM_CONTENT_KEY,
    UTM_MEDIUM_KEY,
    UTM_PARAM_NAMES,
    UTM_SOURCE_KEY,
    UTM_TERM_KEY
)
from ..helpers import get_utm_params, save_user_utm
from ..models import UserLeads


class UserLeadsHelpersTest(TestCase):
    """ Test cases for openedx user_leads feature helpers """

    def setUp(self):
        super(UserLeadsHelpersTest, self).setUp()

        self.request_data = {
            UTM_PARAM_NAMES[UTM_SOURCE_KEY]: u'test-source',
            UTM_PARAM_NAMES[UTM_MEDIUM_KEY]: u'test-medium',
            UTM_PARAM_NAMES[UTM_CONTENT_KEY]: u'test-content',
            UTM_PARAM_NAMES[UTM_CAMPAIGN_KEY]: u'test-campaign',
            UTM_PARAM_NAMES[UTM_TERM_KEY]: u'test-term',
        }

        self.user = UserFactory()
        self.anonymous_user = AnonymousUserFactory()
        self.url_path = '/dummy_path/'
        self.url_name = 'dummy_name'

    def test_get_utm_params_with_all_keys(self):
        """
        Test that a dict is returned with all the given utm params
        extracted from request
        """
        request = RequestFactory().get(self.url_path, self.request_data)
        returned_utm_params = get_utm_params(request)

        self.assertDictEqual(returned_utm_params, self.request_data)

    def test_get_utm_params_with_missing_key(self):
        """
        Test that a dict is returned without the missing utm param
        """
        utm_params = self.request_data.copy()
        del utm_params[random.choice(list(utm_params.keys()))]

        request = RequestFactory().get(self.url_path, utm_params)
        returned_utm_params = get_utm_params(request)

        self.assertDictEqual(utm_params, returned_utm_params)

    def test_save_user_utm_registered_user_no_existing_lead(self):
        """
        Test that for a registered user, who has no existing lead against
        the current page, a lead is stored in the UserLeads table
        """
        request = RequestFactory().get(self.url_path, self.request_data)
        request.user = self.user
        request.resolver_match = ResolverMatch('get', (), {})
        request.resolver_match.url_name = self.url_name

        existing_lead_count = UserLeads.objects.filter(user=self.user, origin=self.url_name).count()
        self.assertTrue(existing_lead_count == 0)

        save_user_utm(request)

        existing_lead_count = UserLeads.objects.filter(user=self.user, origin=self.url_name).count()
        self.assertTrue(existing_lead_count == 1)

    def test_save_user_utm_registered_user_existing_lead(self):
        """
        Test that for a registered user, who has an existing lead against
        the current page, an exception is thrown when trying to insert
        another lead in the UserLeads table.
        """
        request = RequestFactory().get(self.url_path, self.request_data)
        request.user = self.user
        request.resolver_match = ResolverMatch('get', (), {})
        request.resolver_match.url_name = self.url_name

        UserLeads.objects.create(user=self.user, origin=self.url_name, **self.request_data)
        existing_lead_count = UserLeads.objects.filter(user=self.user, origin=self.url_name).count()
        self.assertTrue(existing_lead_count == 1)

        self.assertRaises(IntegrityError, save_user_utm(request))

    @patch('openedx.features.user_leads.helpers.UserLeads.objects.create')
    @patch('openedx.features.user_leads.helpers.UserLeads.objects.filter')
    def test_save_user_utm_anon_user(self,mocked_user_leads_object_filter_method,
                                     mocked_user_leads_object_create_method):
        """
        Test that for an anonymous user a lead is not stored in the UserLeads table.
        """
        request = RequestFactory().get(self.url_path, self.request_data)
        request.user = self.anonymous_user
        request.resolver_match = ResolverMatch('get', (), {})
        request.resolver_match.url_name = self.url_name

        save_user_utm(request)

        mocked_user_leads_object_create_method.assert_not_called()
        mocked_user_leads_object_filter_method.assert_not_called()
