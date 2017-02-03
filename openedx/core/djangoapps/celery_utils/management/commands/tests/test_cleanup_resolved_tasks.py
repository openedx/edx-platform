"""
Test management command to cleanup resolved tasks.
"""

from datetime import timedelta

import ddt
from django.test import TestCase
from django.core.management import call_command
from django.utils.timezone import now

from openedx.core.djangolib.testing.utils import skip_unless_lms

from .... import models

DAY = timedelta(days=1)
MONTH_AGO = now() - (30 * DAY)


@ddt.ddt
@skip_unless_lms
class TestCleanupResolvedTasksCommand(TestCase):
    """
    Test cleanup_resolved_tasks management command.
    """

    def setUp(self):
        self.failed_tasks = [
            models.FailedTask.objects.create(
                task_name=u'task',
                datetime_resolved=MONTH_AGO - DAY,
                task_id=u'old',
            ),
            models.FailedTask.objects.create(
                task_name=u'task',
                datetime_resolved=MONTH_AGO + DAY,
                task_id=u'new',
            ),
            models.FailedTask.objects.create(
                task_name=u'task',
                datetime_resolved=None,
                task_id=u'unresolved',
            ),
            models.FailedTask.objects.create(
                task_name=u'other',
                datetime_resolved=MONTH_AGO - DAY,
                task_id=u'other',
            ),
        ]
        super(TestCleanupResolvedTasksCommand, self).setUp()

    @ddt.data(
        ([], {u'new', u'unresolved'}),
        ([u'--task-name=task'], {u'new', u'unresolved', u'other'}),
        ([u'--age=0'], {u'unresolved'}),
        ([u'--age=0', u'--task-name=task'], {u'unresolved', u'other'}),
        ([u'--dry-run'], {u'old', u'new', u'unresolved', u'other'}),
    )
    @ddt.unpack
    def test_call_command(self, args, remaining_task_ids):
        call_command(u'cleanup_resolved_tasks', *args)
        results = set(models.FailedTask.objects.values_list('task_id', flat=True))
        self.assertEqual(remaining_task_ids, results)
