""" Tests for views related to account settings. """


from unittest import mock
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from requests import exceptions

from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.tests import factories
from lms.djangoapps.commerce.tests.mocks import mock_get_orders
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref.tests.test_api import EN, LT_LT
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from openedx.core.djangoapps.user_api.accounts.settings_views import account_settings_context, get_user_orders
from openedx.core.djangoapps.user_api.accounts.toggles import REDIRECT_TO_ACCOUNT_MICROFRONTEND
from openedx.core.djangoapps.user_api.tests.factories import UserPreferenceFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.utils import get_enterprise_readonly_account_fields
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.third_party_auth.tests.testutil import ThirdPartyAuthTestMixin


@skip_unless_lms
class AccountSettingsViewTest(ThirdPartyAuthTestMixin, SiteMixin, ProgramsApiConfigMixin, TestCase):
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
        super().setUp()
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
        MessageMiddleware(get_response=lambda request: None).process_request(self.request)
        messages.error(self.request, 'Facebook is already in use.', extra_tags='Auth facebook')

    @mock.patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    def test_context(self, mock_enterprise_customer_for_request):
        self.request.site = SiteFactory.create()
        UserPreferenceFactory(user=self.user, key='pref-lang', value='lt-lt')
        DarkLangConfig(
            released_languages='en',
            changed_by=self.user,
            enabled=True,
            beta_languages='lt-lt',
            enable_beta_languages=True
        ).save()
        mock_enterprise_customer_for_request.return_value = {}

        with override_settings(LANGUAGES=[EN, LT_LT], LANGUAGE_CODE='en'):
            context = account_settings_context(self.request)

            user_accounts_api_url = reverse("accounts_api", kwargs={'username': self.user.username})
            assert context['user_accounts_api_url'] == user_accounts_api_url

            user_preferences_api_url = reverse('preferences_api', kwargs={'username': self.user.username})
            assert context['user_preferences_api_url'] == user_preferences_api_url

            for attribute in self.FIELDS:
                assert attribute in context['fields']

            assert context['user_accounts_api_url'] == reverse('accounts_api', kwargs={'username': self.user.username})
            assert context['user_preferences_api_url'] ==\
                   reverse('preferences_api', kwargs={'username': self.user.username})

            assert context['duplicate_provider'] == 'facebook'
            assert context['auth']['providers'][0]['name'] == 'Facebook'
            assert context['auth']['providers'][1]['name'] == 'Google'

            assert context['sync_learner_profile_data'] is False
            assert context['edx_support_url'] == settings.SUPPORT_SITE_LINK
            assert context['enterprise_name'] is None
            assert context['enterprise_readonly_account_fields'] ==\
                   {'fields': list(get_enterprise_readonly_account_fields(self.user))}

            expected_beta_language = {'code': 'lt-lt', 'name': settings.LANGUAGE_DICT.get('lt-lt')}
            assert context['beta_language'] == expected_beta_language

    @with_site_configuration(
        configuration={
            'extended_profile_fields': ['work_experience']
        }
    )
    def test_context_extended_profile(self):
        """
        Test that if the field is available in extended_profile configuration then the field
        will be sent in response.
        """
        context = account_settings_context(self.request)
        extended_pofile_field = context['extended_profile_fields'][0]
        assert extended_pofile_field['field_name'] == 'work_experience'
        assert extended_pofile_field['field_label'] == 'Work experience'

    @mock.patch('openedx.core.djangoapps.user_api.accounts.settings_views.enterprise_customer_for_request')
    @mock.patch('openedx.features.enterprise_support.utils.third_party_auth.provider.Registry.get')
    def test_context_for_enterprise_learner(
            self, mock_get_auth_provider, mock_enterprise_customer_for_request
    ):
        dummy_enterprise_customer = {
            'uuid': 'real-ent-uuid',
            'name': 'Dummy Enterprise',
            'identity_provider': 'saml-ubc'
        }
        mock_enterprise_customer_for_request.return_value = dummy_enterprise_customer
        self.request.site = SiteFactory.create()
        mock_get_auth_provider.return_value.sync_learner_profile_data = True
        context = account_settings_context(self.request)

        user_accounts_api_url = reverse("accounts_api", kwargs={'username': self.user.username})
        assert context['user_accounts_api_url'] == user_accounts_api_url

        user_preferences_api_url = reverse('preferences_api', kwargs={'username': self.user.username})
        assert context['user_preferences_api_url'] == user_preferences_api_url

        for attribute in self.FIELDS:
            assert attribute in context['fields']

        assert context['user_accounts_api_url'] == reverse('accounts_api', kwargs={'username': self.user.username})
        assert context['user_preferences_api_url'] ==\
               reverse('preferences_api', kwargs={'username': self.user.username})

        assert context['duplicate_provider'] == 'facebook'
        assert context['auth']['providers'][0]['name'] == 'Facebook'
        assert context['auth']['providers'][1]['name'] == 'Google'

        assert context['sync_learner_profile_data'] == mock_get_auth_provider.return_value.sync_learner_profile_data
        assert context['edx_support_url'] == settings.SUPPORT_SITE_LINK
        assert context['enterprise_name'] == dummy_enterprise_customer['name']
        assert context['enterprise_readonly_account_fields'] ==\
               {'fields': list(get_enterprise_readonly_account_fields(self.user))}

    def test_view(self):
        """
        Test that all fields are visible
        """
        view_path = reverse('account_settings')
        response = self.client.get(path=view_path)

        for attribute in self.FIELDS:
            self.assertContains(response, attribute)

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
            assert order_detail[i] == expected

    def test_commerce_order_detail_exception(self):
        with mock_get_orders(exception=exceptions.HTTPError):
            order_detail = get_user_orders(self.user)

        assert not order_detail

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

        assert not order_detail

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

        assert len(order_detail) == 1

    def test_redirect_view(self):
        old_url_path = reverse('account_settings')
        with override_waffle_flag(REDIRECT_TO_ACCOUNT_MICROFRONTEND, active=True):
            # Test with waffle flag active and none site setting, redirects to microfrontend
            response = self.client.get(path=old_url_path)
            self.assertRedirects(response, settings.ACCOUNT_MICROFRONTEND_URL, fetch_redirect_response=False)

        # Test with waffle flag disabled and site setting disabled, does not redirect
        response = self.client.get(path=old_url_path)
        for attribute in self.FIELDS:
            self.assertContains(response, attribute)

        # Test with site setting disabled, does not redirect
        site_domain = 'othersite.example.com'
        site = self.set_up_site(site_domain, {
            'SITE_NAME': site_domain,
            'ENABLE_ACCOUNT_MICROFRONTEND': False
        })
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        response = self.client.get(path=old_url_path)
        for attribute in self.FIELDS:
            self.assertContains(response, attribute)

        # Test with site setting enabled, redirects to microfrontend
        site.configuration.site_values['ENABLE_ACCOUNT_MICROFRONTEND'] = True
        site.configuration.save()
        site.__class__.objects.clear_cache()
        response = self.client.get(path=old_url_path)
        self.assertRedirects(response, settings.ACCOUNT_MICROFRONTEND_URL, fetch_redirect_response=False)
