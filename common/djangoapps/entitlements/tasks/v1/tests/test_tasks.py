"""
Test entitlements tasks
"""

from datetime import datetime, timedelta
import mock
import pytz

from django.test import TestCase

from entitlements.models import CourseEntitlementPolicy
from entitlements.tasks.v1 import tasks
from entitlements.tests.factories import CourseEntitlementFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


def make_entitlement(**kwargs):
    m = mock.NonCallableMock()
    p = mock.PropertyMock(**kwargs)
    type(m).expired_at_datetime = p
    return m, p


def boom():
    raise Exception('boom')


@skip_unless_lms
class TestExpireOldEntitlementsTask(TestCase):
    """
    Tests for the 'expire_old_entitlements' method.
    """

    def test_checks_expiration(self):
        """
        Test that we actually do check expiration on each entitlement (happy path)
        """
        entitlement1, prop1 = make_entitlement(return_value=None)
        entitlement2, prop2 = make_entitlement(return_value='some date')
        tasks.expire_old_entitlements.delay([entitlement1, entitlement2]).get()

        # Test that the expired_at_datetime property was accessed
        self.assertEqual(prop1.call_count, 1)
        self.assertEqual(prop2.call_count, 1)

    def test_retry(self):
        """
        Test that we retry when an exception occurs while checking old
        entitlements.
        """
        entitlement, prop = make_entitlement(side_effect=boom)
        task = tasks.expire_old_entitlements.delay([entitlement])

        self.assertRaises(Exception, task.get)
        self.assertEqual(prop.call_count, tasks.MAX_RETRIES + 1)

    def test_actually_expired(self):
        """
        Integration test with CourseEntitlement to make sure we are calling the
        correct API.
        """
        # Create an actual old entitlement
        past_days = CourseEntitlementPolicy.DEFAULT_EXPIRATION_PERIOD_DAYS
        past_datetime = datetime.now(tz=pytz.UTC) - timedelta(days=past_days)
        entitlement = CourseEntitlementFactory.create(created=past_datetime)

        # Sanity check
        self.assertIsNone(entitlement.expired_at)

        # Run enforcement
        tasks.expire_old_entitlements.delay([entitlement]).get()
        entitlement.refresh_from_db()

        self.assertIsNotNone(entitlement.expired_at)
