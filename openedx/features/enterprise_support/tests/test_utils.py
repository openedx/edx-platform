"""
Test the enterprise support utils.
"""

import json

import ddt
import mock
from django.test import TestCase
from django.test.utils import override_settings

from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCustomerBrandingConfigurationFactory,
    EnterpriseCustomerUserFactory
)
from openedx.features.enterprise_support.utils import ENTERPRISE_HEADER_LINKS, get_enterprise_learner_portal
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
@override_settings(FEATURES=FEATURES_WITH_ENTERPRISE_ENABLED)
@skip_unless_lms
class TestEnterpriseUtils(TestCase):
    """
    Test enterprise support utils.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(password='password')
        super(TestEnterpriseUtils, cls).setUpTestData()

    @ddt.data(
        ('notfoundpage', 0),
    )
    @ddt.unpack
    def test_enterprise_customer_for_request_called_on_404(self, resource, expected_calls):
        """
        Test enterprise customer API is not called from 404 page
        """
        self.client.login(username=self.user.username, password='password')

        with mock.patch(
            'openedx.features.enterprise_support.api.enterprise_customer_for_request'
        ) as mock_customer_request:
            self.client.get(resource)
            self.assertEqual(mock_customer_request.call_count, expected_calls)

    @override_waffle_flag(ENTERPRISE_HEADER_LINKS, True)
    def test_get_enterprise_learner_portal_uncached(self):
        """
        Test that only an enabled enterprise portal is returned,
        and that it matches the customer UUID provided in the request.
        """
        enterprise_customer_user = EnterpriseCustomerUserFactory(active=True, user_id=self.user.id)
        EnterpriseCustomerBrandingConfigurationFactory(
            enterprise_customer=enterprise_customer_user.enterprise_customer,
        )
        enterprise_customer_user.enterprise_customer.enable_learner_portal = True
        enterprise_customer_user.enterprise_customer.save()

        request = mock.MagicMock(session={}, user=self.user)
        # Indicate the "preferred" customer in the request
        request.GET = {'enterprise_customer': enterprise_customer_user.enterprise_customer.uuid}

        # Create another enterprise customer association for the same user.
        # There should be no data returned for this customer's portal,
        # because we filter for only the enterprise customer uuid found in the request.
        other_enterprise_customer_user = EnterpriseCustomerUserFactory(active=True, user_id=self.user.id)
        other_enterprise_customer_user.enable_learner_portal = True
        other_enterprise_customer_user.save()

        portal = get_enterprise_learner_portal(request)
        self.assertDictEqual(portal, {
            'name': enterprise_customer_user.enterprise_customer.name,
            'slug': enterprise_customer_user.enterprise_customer.slug,
            'logo': enterprise_customer_user.enterprise_customer.safe_branding_configuration.safe_logo_url,
        })

    @override_waffle_flag(ENTERPRISE_HEADER_LINKS, True)
    def test_get_enterprise_learner_portal_no_branding_config(self):
        """
        Test that only an enabled enterprise portal is returned,
        and that it matches the customer UUID provided in the request,
        even if no branding config is associated with the customer.
        """
        enterprise_customer_user = EnterpriseCustomerUserFactory.create(active=True, user_id=self.user.id)
        enterprise_customer_user.enterprise_customer.enable_learner_portal = True
        enterprise_customer_user.enterprise_customer.save()

        request = mock.MagicMock(session={}, user=self.user)
        # Indicate the "preferred" customer in the request
        request.GET = {'enterprise_customer': enterprise_customer_user.enterprise_customer.uuid}

        portal = get_enterprise_learner_portal(request)
        self.assertDictEqual(portal, {
            'name': enterprise_customer_user.enterprise_customer.name,
            'slug': enterprise_customer_user.enterprise_customer.slug,
            'logo': enterprise_customer_user.enterprise_customer.safe_branding_configuration.safe_logo_url,
        })

    @override_waffle_flag(ENTERPRISE_HEADER_LINKS, True)
    def test_get_enterprise_learner_portal_no_customer_from_request(self):
        """
        Test that only one enabled enterprise portal is returned,
        even if enterprise_customer_uuid_from_request() returns None.
        """
        # Create another enterprise customer association for the same user.
        # There should be no data returned for this customer's portal,
        # because another customer is later created with a more recent active/modified time.
        other_enterprise_customer_user = EnterpriseCustomerUserFactory(active=True, user_id=self.user.id)
        other_enterprise_customer_user.enable_learner_portal = True
        other_enterprise_customer_user.save()

        enterprise_customer_user = EnterpriseCustomerUserFactory(active=True, user_id=self.user.id)
        EnterpriseCustomerBrandingConfigurationFactory(
            enterprise_customer=enterprise_customer_user.enterprise_customer,
        )
        enterprise_customer_user.enterprise_customer.enable_learner_portal = True
        enterprise_customer_user.enterprise_customer.save()

        request = mock.MagicMock(session={}, user=self.user)

        with mock.patch(
                'openedx.features.enterprise_support.api.enterprise_customer_uuid_for_request',
                return_value=None,
        ):
            portal = get_enterprise_learner_portal(request)

        self.assertDictEqual(portal, {
            'name': enterprise_customer_user.enterprise_customer.name,
            'slug': enterprise_customer_user.enterprise_customer.slug,
            'logo': enterprise_customer_user.enterprise_customer.safe_branding_configuration.safe_logo_url,
        })

    @override_waffle_flag(ENTERPRISE_HEADER_LINKS, True)
    def test_get_enterprise_learner_portal_cached(self):
        enterprise_customer_data = {
            'name': 'Enabled Customer',
            'slug': 'enabled_customer',
            'logo': 'https://logo.url',
        }
        request = mock.MagicMock(session={
            'enterprise_learner_portal': json.dumps(enterprise_customer_data)
        }, user=self.user)
        portal = get_enterprise_learner_portal(request)
        self.assertDictEqual(portal, enterprise_customer_data)
