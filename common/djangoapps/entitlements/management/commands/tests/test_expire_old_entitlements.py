"""Test Entitlements models"""


from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from common.djangoapps.entitlements.tests.factories import CourseEntitlementFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
@mock.patch('common.djangoapps.entitlements.tasks.expire_old_entitlements.delay')
class TestExpireOldEntitlementsCommand(TestCase):
    """
    Test expire_old_entitlement management command.
    """

    def test_no_commit(self, mock_task):
        """
        Verify that relevant tasks are only enqueued when the commit option is passed.
        """
        CourseEntitlementFactory.create()

        call_command('expire_old_entitlements')
        assert mock_task.call_count == 0

        call_command('expire_old_entitlements', commit=True)
        assert mock_task.call_count == 1

    def test_no_tasks_if_no_work(self, mock_task):
        """
        Verify that we never try to spin off a task if there are no database rows.
        """
        call_command('expire_old_entitlements', commit=True)
        assert mock_task.call_count == 0

        # Now confirm that the above test wasn't a fluke and we will create a task if there is work
        CourseEntitlementFactory.create()
        call_command('expire_old_entitlements', commit=True)
        assert mock_task.call_count == 1

    def test_pagination(self, mock_task):
        """
        Verify that we chunk up our requests to celery.
        """
        for _ in range(5):
            CourseEntitlementFactory.create()

        call_command('expire_old_entitlements', commit=True, batch_size=2)

        args_list = mock_task.call_args_list
        assert len(args_list) == 3
        assert args_list[0][0] == (1, 3)
        assert args_list[1][0] == (3, 5)
        assert args_list[2][0] == (5, 6)
