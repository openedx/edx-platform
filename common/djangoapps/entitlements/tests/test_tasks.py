"""
Test entitlements tasks
"""

from datetime import datetime, timedelta
import mock
import pytz

from django.test import TestCase

from entitlements import tasks
from entitlements.models import CourseEntitlementPolicy
from entitlements.tests.factories import CourseEntitlementFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


def make_entitlement(expired=False):
    age = CourseEntitlementPolicy.DEFAULT_EXPIRATION_PERIOD_DAYS
    past_datetime = datetime.now(tz=pytz.UTC) - timedelta(days=age)
    expired_at = past_datetime if expired else None
    entitlement = CourseEntitlementFactory.create(created=past_datetime, expired_at=expired_at)
    return entitlement


def boom():
    raise Exception('boom')


@skip_unless_lms
@mock.patch('entitlements.models.CourseEntitlement.expired_at_datetime', new_callable=mock.PropertyMock)
class TestExpireOldEntitlementsTask(TestCase):
    """
    Tests for the 'expire_old_entitlements' method.
    """
    def test_checks_expiration(self, mock_datetime):
        """
        Test that we actually do check expiration on each entitlement (happy path)
        """
        make_entitlement()
        make_entitlement()

        tasks.expire_old_entitlements.delay(1, 3).get()

        self.assertEqual(mock_datetime.call_count, 2)

    def test_only_unexpired(self, mock_datetime):
        """
        Verify that only unexpired entitlements are included
        """
        # Create an old expired and an old unexpired entitlement
        make_entitlement(expired=True)
        make_entitlement()

        # Run expiration
        tasks.expire_old_entitlements.delay(1, 3).get()

        # Make sure only the unexpired one gets used
        self.assertEqual(mock_datetime.call_count, 1)

    def test_retry(self, mock_datetime):
        """
        Test that we retry when an exception occurs while checking old
        entitlements.
        """
        mock_datetime.side_effect = boom

        make_entitlement()
        task = tasks.expire_old_entitlements.delay(1, 2)

        self.assertRaises(Exception, task.get)
        self.assertEqual(mock_datetime.call_count, tasks.MAX_RETRIES + 1)


@skip_unless_lms
class TestExpireOldEntitlementsTaskIntegration(TestCase):
    """
    Tests for the 'expire_old_entitlements' method without mocking.
    """
    def test_actually_expired(self):
        """
        Integration test with CourseEntitlement to make sure we are calling the
        correct API.
        """
        entitlement = make_entitlement()

        # Sanity check
        self.assertIsNone(entitlement.expired_at)

        # Run enforcement
        tasks.expire_old_entitlements.delay(1, 2).get()
        entitlement.refresh_from_db()

        self.assertIsNotNone(entitlement.expired_at)
