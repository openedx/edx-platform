"""
Tests for Enterprise middleware.
"""

import mock

from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests import (
    FAKE_ENTERPRISE_CUSTOMER, FEATURES_WITH_ENTERPRISE_ENABLED,
    factories
)
from student.tests.factories import UserFactory


@override_settings(FEATURES=FEATURES_WITH_ENTERPRISE_ENABLED)
@skip_unless_lms
class EnterpriseMiddlewareTest(TestCase):
    """
    Test for `EnterpriseMiddleware`.
    """

    def setUp(self):
        """Initiate commonly needed objects."""
        super(EnterpriseMiddlewareTest, self).setUp()

        # Customer & Learner details.
        self.user = UserFactory.create(username='username', password='password')
        self.enterprise_customer = FAKE_ENTERPRISE_CUSTOMER
        self.enterprise_learner = factories.EnterpriseCustomerUserFactory(user_id=self.user.id)

        # Request details.
        self.client.login(username='username', password='password')
        self.dashboard = reverse('dashboard')

        # Mocks.
        patcher = mock.patch('openedx.features.enterprise_support.api.enterprise_customer_from_api')
        self.mock_enterprise_customer_from_api = patcher.start()
        self.mock_enterprise_customer_from_api.return_value = self.enterprise_customer
        self.addCleanup(patcher.stop)

    def test_anonymous_user(self):
        """The `enterprise_customer` is not set in the session if the user is anonymous."""
        self.client.logout()
        self.client.get(self.dashboard)
        assert self.client.session.get('enterprise_customer') is None

    def test_enterprise_customer(self):
        """The `enterprise_customer` gets set in the session."""
        self.client.get(self.dashboard)
        assert self.client.session.get('enterprise_customer') == self.enterprise_customer

    def test_enterprise_customer_cached(self):
        """The middleware doesn't attempt to refill `enterprise_customer` if it already exists in the session."""
        assert not self.mock_enterprise_customer_from_api.called

        # First call populates the session by calling the API.
        self.client.get(self.dashboard)
        assert self.mock_enterprise_customer_from_api.call_count == 1

        # Second same call has no need to call the API because the session already contains the data.
        self.client.get(self.dashboard)
        assert self.mock_enterprise_customer_from_api.call_count == 1
