""" Tests for views related to account settings. """
# -*- coding: utf-8 -*-
import mock
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.urls import reverse
from django.http import HttpRequest
from django.test import TestCase
from edx_rest_api_client import exceptions

from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.tests import factories
from lms.djangoapps.commerce.tests.mocks import mock_get_orders
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.djangoapps.user_api.accounts.settings_views import account_settings_context, get_user_orders
from student.tests.factories import UserFactory
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin


@skip_unless_lms
class AccountSettingsViewTest(ThirdPartyAuthTestMixin, TestCase, ProgramsApiConfigMixin):
    """ Tests for the account settings view. """

    USERNAME = 'student'
    PASSWORD = 'password'
    FIELDS = [
        'country',
        'gender',
        'language',
        'level_of_education',
        'password',
        'year_of_birth',
        'preferred_language',
        'time_zone',
    ]

    @mock.patch("django.conf.settings.MESSAGE_STORAGE", 'django.contrib.messages.storage.cookie.CookieStorage')
    def setUp(self):  # pylint: disable=arguments-differ
        super(AccountSettingsViewTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        CommerceConfiguration.objects.create(cache_ttl=10, enabled=True)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

        self.request = HttpRequest()
        self.request.user = self.user

        # For these tests, two third party auth providers are enabled by default:
        self.configure_google_provider(enabled=True, visible=True)
        self.configure_facebook_provider(enabled=True, visible=True)

        # Python-social saves auth failure notifcations in Django messages.
        # See pipeline.get_duplicate_provider() for details.
        self.request.COOKIES = {}
        MessageMiddleware().process_request(self.request)
        messages.error(self.request, 'Facebook is already in use.', extra_tags='Auth facebook')

    @mock.patch('openedx.features.enterprise_support.api.get_enterprise_customer_for_learner')
    def test_context(self, mock_get_enterprise_customer_for_learner):
        self.request.site = SiteFactory.create()
        mock_get_enterprise_customer_for_learner.return_value = {}
        context = account_settings_context(self.request)

        user_accounts_api_url = reverse("accounts_api", kwargs={'username': self.user.username})
        self.assertEqual(context['user_accounts_api_url'], user_accounts_api_url)

        user_preferences_api_url = reverse('preferences_api', kwargs={'username': self.user.username})
        self.assertEqual(context['user_preferences_api_url'], user_preferences_api_url)

        for attribute in self.FIELDS:
            self.assertIn(attribute, context['fields'])

        self.assertEqual(
            context['user_accounts_api_url'], reverse("accounts_api", kwargs={'username': self.user.username})
        )
        self.assertEqual(
            context['user_preferences_api_url'], reverse('preferences_api', kwargs={'username': self.user.username})
        )

        self.assertEqual(context['duplicate_provider'], 'facebook')
        self.assertEqual(context['auth']['providers'][0]['name'], 'Facebook')
        self.assertEqual(context['auth']['providers'][1]['name'], 'Google')

        self.assertEqual(context['sync_learner_profile_data'], False)
        self.assertEqual(context['edx_support_url'], settings.SUPPORT_SITE_LINK)
        self.assertEqual(context['enterprise_name'], None)
        self.assertEqual(
            context['enterprise_readonly_account_fields'], {'fields': settings.ENTERPRISE_READONLY_ACCOUNT_FIELDS}
        )

    @mock.patch('openedx.core.djangoapps.user_api.accounts.settings_views.get_enterprise_customer_for_learner')
    @mock.patch('openedx.features.enterprise_support.utils.third_party_auth.provider.Registry.get')
    def test_context_for_enterprise_learner(
            self, mock_get_auth_provider, mock_get_enterprise_customer_for_learner
    ):
        dummy_enterprise_customer = {
            'uuid': 'real-ent-uuid',
            'name': 'Dummy Enterprise',
            'identity_provider': 'saml-ubc'
        }
        mock_get_enterprise_customer_for_learner.return_value = dummy_enterprise_customer
        self.request.site = SiteFactory.create()
        mock_get_auth_provider.return_value.sync_learner_profile_data = True
        context = account_settings_context(self.request)

        user_accounts_api_url = reverse("accounts_api", kwargs={'username': self.user.username})
        self.assertEqual(context['user_accounts_api_url'], user_accounts_api_url)

        user_preferences_api_url = reverse('preferences_api', kwargs={'username': self.user.username})
        self.assertEqual(context['user_preferences_api_url'], user_preferences_api_url)

        for attribute in self.FIELDS:
            self.assertIn(attribute, context['fields'])

        self.assertEqual(
            context['user_accounts_api_url'], reverse("accounts_api", kwargs={'username': self.user.username})
        )
        self.assertEqual(
            context['user_preferences_api_url'], reverse('preferences_api', kwargs={'username': self.user.username})
        )

        self.assertEqual(context['duplicate_provider'], 'facebook')
        self.assertEqual(context['auth']['providers'][0]['name'], 'Facebook')
        self.assertEqual(context['auth']['providers'][1]['name'], 'Google')

        self.assertEqual(
            context['sync_learner_profile_data'], mock_get_auth_provider.return_value.sync_learner_profile_data
        )
        self.assertEqual(context['edx_support_url'], settings.SUPPORT_SITE_LINK)
        self.assertEqual(context['enterprise_name'], dummy_enterprise_customer['name'])
        self.assertEqual(
            context['enterprise_readonly_account_fields'], {'fields': settings.ENTERPRISE_READONLY_ACCOUNT_FIELDS}
        )

    def test_view(self):
        """
        Test that all fields are  visible
        """
        view_path = reverse('account_settings')
        response = self.client.get(path=view_path)

        for attribute in self.FIELDS:
            self.assertIn(attribute, response.content)

    def test_header_with_programs_listing_enabled(self):
        """
        Verify that tabs header will be shown while program listing is enabled.
        """
        self.create_programs_config()
        view_path = reverse('account_settings')
        response = self.client.get(path=view_path)

        self.assertContains(response, 'global-header')

    def test_header_with_programs_listing_disabled(self):
        """
        Verify that nav header will be shown while program listing is disabled.
        """
        self.create_programs_config(enabled=False)
        view_path = reverse('account_settings')
        response = self.client.get(path=view_path)

        self.assertContains(response, 'global-header')

    def test_commerce_order_detail(self):
        """
        Verify that get_user_orders returns the correct order data.
        """
        with mock_get_orders():
            order_detail = get_user_orders(self.user)

        for i, order in enumerate(mock_get_orders.default_response['results']):
            expected = {
                'number': order['number'],
                'price': order['total_excl_tax'],
                'order_date': 'Jan 01, 2016',
                'receipt_url': '/checkout/receipt/?order_number=' + order['number'],
                'lines': order['lines'],
            }
            self.assertEqual(order_detail[i], expected)

    def test_commerce_order_detail_exception(self):
        with mock_get_orders(exception=exceptions.HttpNotFoundError):
            order_detail = get_user_orders(self.user)

        self.assertEqual(order_detail, [])

    def test_incomplete_order_detail(self):
        response = {
            'results': [
                factories.OrderFactory(
                    status='Incomplete',
                    lines=[
                        factories.OrderLineFactory(
                            product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory()])
                        )
                    ]
                )
            ]
        }
        with mock_get_orders(response=response):
            order_detail = get_user_orders(self.user)

        self.assertEqual(order_detail, [])

    def test_order_history_with_no_product(self):
        response = {
            'results': [
                factories.OrderFactory(
                    lines=[
                        factories.OrderLineFactory(
                            product=None
                        ),
                        factories.OrderLineFactory(
                            product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory(
                                name='certificate_type',
                                value='verified'
                            )])
                        )
                    ]
                )
            ]
        }
        with mock_get_orders(response=response):
            order_detail = get_user_orders(self.user)

        self.assertEqual(len(order_detail), 1)
