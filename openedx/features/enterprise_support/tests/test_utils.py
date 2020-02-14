"""
Test the enterprise support utils.
"""


import mock
import ddt

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED
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
        (reverse('dashboard'), 1),
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
