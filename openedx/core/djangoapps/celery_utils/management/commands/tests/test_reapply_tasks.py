"""
Test management command to reapply failed tasks.
"""
from collections import Counter
from datetime import datetime

import celery
from django.test import TestCase
from django.core.management import call_command
import mock

from openedx.core.djangolib.testing.utils import skip_unless_lms

from .... import models, persist_on_failure


@skip_unless_lms
class TestReapplyTaskCommand(TestCase):
    """
    Test reapply_task management command.
    """

    fallible_task_name = (
        u'openedx.core.djangoapps.celery_utils.management.commands.tests.test_reapply_tasks.fallible_task'
    )
    passing_task_name = u'openedx.core.djangoapps.celery_utils.management.commands.tests.test_reapply_tasks.other_task'

    @classmethod
    def setUpClass(cls):
        @celery.task(base=persist_on_failure.PersistOnFailureTask, name=cls.fallible_task_name)
        def fallible_task(error_message=None):
            """
            Simple task to let us test retry functionality.
            """
            if error_message:
                raise ValueError(error_message)

        cls.fallible_task = fallible_task

        @celery.task(base=persist_on_failure.PersistOnFailureTask, name=cls.passing_task_name)
        def passing_task():
            """
            This task always passes
            """
            return 5
        cls.passing_task = passing_task
        super(TestReapplyTaskCommand, cls).setUpClass()

    def setUp(self):
        self.failed_tasks = [
            models.FailedTask.objects.create(
                task_name=self.fallible_task_name,
                task_id=u'fail_again',
                args=[],
                kwargs={"error_message": "Err, yo!"},
                exc=u'UhOhError().',
            ),
            models.FailedTask.objects.create(
                task_name=self.fallible_task_name,
                task_id=u'will_succeed',
                args=[],
                kwargs={},
                exc=u'NetworkErrorMaybe?()',
            ),
            models.FailedTask.objects.create(
                task_name=self.passing_task_name,
                task_id=u'other_task',
                args=[],
                kwargs={},
                exc=u'RaceCondition()',
            ),
        ]
        super(TestReapplyTaskCommand, self).setUp()

    def _assert_resolved(self, task_object):
        """
        Raises an assertion error if the task failed to complete successfully
        and record its resolution in the failedtask record.
        """
        self.assertIsInstance(task_object.datetime_resolved, datetime)

    def _assert_unresolved(self, task_object):
        """
        Raises an assertion error if the task completed successfully.
        The resolved_datetime will still be None.
        """
        self.assertIsNone(task_object.datetime_resolved)

    def test_call_command(self):
        call_command(u'reapply_tasks')
        self._assert_unresolved(models.FailedTask.objects.get(task_id=u'fail_again'))
        self._assert_resolved(models.FailedTask.objects.get(task_id=u'will_succeed'))
        self._assert_resolved(models.FailedTask.objects.get(task_id=u'other_task'))

    def test_call_command_with_specified_task(self):
        call_command(u'reapply_tasks', u'--task-name={}'.format(self.fallible_task_name))
        self._assert_unresolved(models.FailedTask.objects.get(task_id=u'fail_again'))
        self._assert_resolved(models.FailedTask.objects.get(task_id=u'will_succeed'))
        self._assert_unresolved(models.FailedTask.objects.get(task_id=u'other_task'))

    def test_duplicate_tasks(self):
        models.FailedTask.objects.create(
            task_name=self.fallible_task_name,
            task_id=u'will_succeed',
            args=[],
            kwargs={},
            exc=u'AlsoThisOtherError()',
        )
        # Verify that only one task got run for this task_id.
        with mock.patch.object(self.fallible_task, u'apply_async', wraps=self.fallible_task.apply_async) as mock_apply:
            call_command(u'reapply_tasks')
            task_id_counts = Counter(call[2][u'task_id'] for call in mock_apply.mock_calls)
            self.assertEqual(task_id_counts[u'will_succeed'], 1)
        # Verify that both tasks matching that task_id are resolved.
        will_succeed_tasks = models.FailedTask.objects.filter(task_id=u'will_succeed').all()
        self.assertEqual(len(will_succeed_tasks), 2)
        for task_object in will_succeed_tasks:
            self._assert_resolved(task_object)
