"""
Test the enterprise support utils.
"""

import json
import mock
import ddt

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.utils import get_enterprise_learner_portals
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCustomerBrandingConfigurationFactory, EnterpriseCustomerUserFactory,
)
from student.tests.factories import UserFactory


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

    def test_get_enterprise_learner_portals_uncached(self):
        """
        Test that only enabled enterprise portals are returned
        """
        enterprise_customer_user = EnterpriseCustomerUserFactory(active=True, user_id=self.user.id)
        EnterpriseCustomerBrandingConfigurationFactory(
            enterprise_customer=enterprise_customer_user.enterprise_customer,
        )
        enterprise_customer_user.enterprise_customer.enable_learner_portal = True
        enterprise_customer_user.enterprise_customer.save()

        request = mock.MagicMock(session={}, user=self.user)
        portals = get_enterprise_learner_portals(request)
        self.assertEqual(len(portals), 1)
        self.assertDictEqual(portals[0], {
            'name': enterprise_customer_user.enterprise_customer.name,
            'slug': enterprise_customer_user.enterprise_customer.slug,
            'logo': enterprise_customer_user.enterprise_customer.branding_configuration.logo.url,
        })

    def test_get_enterprise_learner_portals_cached(self):
        enterprise_customer_data = {
            'name': 'Enabled Customer',
            'slug': 'enabled_customer',
            'logo': 'https://logo.url',
        }
        request = mock.MagicMock(session={
            'enterprise_learner_portals': json.dumps([enterprise_customer_data])
        }, user=self.user)
        portals = get_enterprise_learner_portals(request)
        self.assertEqual(len(portals), 1)
        self.assertDictEqual(portals[0], enterprise_customer_data)
