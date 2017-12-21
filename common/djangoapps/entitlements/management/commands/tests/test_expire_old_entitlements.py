"""Test Entitlements models"""

from datetime import datetime, timedelta
import mock
import pytz

from django.core.management import call_command
from django.test import TestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from entitlements.models import CourseEntitlementPolicy
from entitlements.tests.factories import CourseEntitlementFactory


def make_entitlement(expired=False):
    age = CourseEntitlementPolicy.DEFAULT_EXPIRATION_PERIOD_DAYS
    past_datetime = datetime.now(tz=pytz.UTC) - timedelta(days=age)
    expired_at = past_datetime if expired else None
    return CourseEntitlementFactory.create(created=past_datetime, expired_at=expired_at)


@skip_unless_lms
@mock.patch('entitlements.tasks.v1.tasks.expire_old_entitlements.delay')
class TestExpireOldEntitlementsCommand(TestCase):
    """
    Test expire_old_entitlement management command.
    """

    def test_no_commit(self, mock_task):
        """
        Verify that relevant tasks are only enqueued when the commit option is passed.
        """
        make_entitlement()

        call_command('expire_old_entitlements')
        self.assertEqual(mock_task.call_count, 0)

        call_command('expire_old_entitlements', commit=True)
        self.assertEqual(mock_task.call_count, 1)

    def test_no_tasks_if_no_work(self, mock_task):
        """
        Verify that we never try to spin off a task if there are no matching database rows.
        """
        call_command('expire_old_entitlements', commit=True)
        self.assertEqual(mock_task.call_count, 0)

        # Now confirm that the above test wasn't a fluke and we will create a task if there is work
        make_entitlement()
        call_command('expire_old_entitlements', commit=True)
        self.assertEqual(mock_task.call_count, 1)

    def test_only_unexpired(self, mock_task):
        """
        Verify that only unexpired entitlements are included
        """
        # Create an old expired and an old unexpired entitlement
        entitlement1 = make_entitlement(expired=True)
        entitlement2 = make_entitlement()

        # Sanity check
        self.assertIsNotNone(entitlement1.expired_at)
        self.assertIsNone(entitlement2.expired_at)

        # Run expiration
        call_command('expire_old_entitlements', commit=True)

        # Make sure only the unexpired one gets used
        self.assertEqual(mock_task.call_count, 1)
        self.assertEqual(list(mock_task.call_args[0][0].object_list), [entitlement2])

    def test_pagination(self, mock_task):
        """
        Verify that we chunk up our requests to celery.
        """
        for _ in range(5):
            make_entitlement()

        call_command('expire_old_entitlements', commit=True, batch_size=2)

        args_list = mock_task.call_args_list
        self.assertEqual(len(args_list), 3)
        self.assertEqual(len(args_list[0][0][0].object_list), 2)
        self.assertEqual(len(args_list[1][0][0].object_list), 2)
        self.assertEqual(len(args_list[2][0][0].object_list), 1)
