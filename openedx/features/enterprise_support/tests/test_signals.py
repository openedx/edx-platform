"""Tests of email marketing signal handlers."""
import logging
import ddt
from django.test import TestCase
from mock import patch

from student.tests.factories import UserFactory
from openedx.features.enterprise_support.tests.factories import EnterpriseCustomerFactory, EnterpriseCustomerUserFactory

log = logging.getLogger(__name__)

LOGGER_NAME = "enterprise_support.signals"

TEST_EMAIL = "test@edx.org"


@ddt.ddt
class EnterpriseSupportSignals(TestCase):
    """
    Tests for the enterprise support signals.
    """

    def setUp(self):
        self.user = UserFactory.create(username='test', email=TEST_EMAIL)
        super(EnterpriseSupportSignals, self).setUp()

    @patch('openedx.features.enterprise_support.signals.update_user.delay')
    def test_register_user(self, mock_update_user):
        """
        make sure marketing enterprise user call invokes update_user
        """
        enterprise_customer = EnterpriseCustomerFactory()
        EnterpriseCustomerUserFactory(
            user_id=self.user.id,
            enterprise_customer=enterprise_customer
        )
        mock_update_user.assert_called_with(
            sailthru_vars={
                'is_enterprise_learner': True,
                'enterprise_name': enterprise_customer.name,
            },
            email=self.user.email
        )
