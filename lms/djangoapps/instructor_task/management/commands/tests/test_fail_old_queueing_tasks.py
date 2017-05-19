from datetime import datetime

import ddt
from celery.states import FAILURE
from django.core.management import call_command
from django.core.management.base import CommandError

from lms.djangoapps.instructor_task.models import InstructorTask, QUEUING
from lms.djangoapps.instructor_task.tests.factories import InstructorTaskFactory
from lms.djangoapps.instructor_task.tests.test_base import InstructorTaskTestCase


@ddt.ddt
class TestFailOldQueueingTasksCommand(InstructorTaskTestCase):
    """
    Tests for the `fail_old_queueing_tasks` management command
    """

    def setUp(self):
        super(TestFailOldQueueingTasksCommand, self).setUp()

        type_1_queueing = InstructorTaskFactory.create(
            task_state=QUEUING,
            task_type="type_1",
            task_key='',
            task_id=1,
        )
        type_1_non_queueing = InstructorTaskFactory.create(
            task_state='NOT QUEUEING',
            task_type="type_1",
            task_key='',
            task_id=2,
        )

        type_2_queueing = InstructorTaskFactory.create(
            task_state=QUEUING,
            task_type="type_2",
            task_key='',
            task_id=3,
        )
        self.tasks = [type_1_queueing, type_1_non_queueing, type_2_queueing]

    def update_task_created(self, created_date):
        """
        Override each task's "created" date
        """
        for task in self.tasks:
            task.created = datetime.strptime(created_date, "%Y-%m-%d")
            task.save()

    def get_tasks(self):
        """
        After the command is run, this queries again for the tasks we created
        in `setUp`.
        """
        type_1_queueing = InstructorTask.objects.get(task_id=1)
        type_1_non_queueing = InstructorTask.objects.get(task_id=2)
        type_2_queueing = InstructorTask.objects.get(task_id=3)
        return type_1_queueing, type_1_non_queueing, type_2_queueing

    @ddt.data(
        ('2015-05-05', '2015-05-07', '2015-05-06'),
        ('2015-05-05', '2015-05-07', '2015-05-08'),
        ('2015-05-05', '2015-05-07', '2015-05-04'),
    )
    @ddt.unpack
    def test_dry_run(self, after, before, created):
        """
        Tests that nothing is updated when run with the `dry_run` option
        """
        self.update_task_created(created)
        call_command(
            'fail_old_queueing_tasks',
            dry_run=True,
            before=before,
            after=after,
        )

        type_1_queueing, type_1_non_queueing, type_2_queueing = self.get_tasks()
        self.assertEqual(type_1_queueing.task_state, QUEUING)
        self.assertEqual(type_2_queueing.task_state, QUEUING)
        self.assertEqual(type_1_non_queueing.task_state, 'NOT QUEUEING')

    @ddt.data(
        ('2015-05-05', '2015-05-07', '2015-05-06', FAILURE),
        ('2015-05-05', '2015-05-07', '2015-05-08', QUEUING),
        ('2015-05-05', '2015-05-07', '2015-05-04', QUEUING),
    )
    @ddt.unpack
    def test_tasks_updated(self, after, before, created, expected_state):
        """
        Test that tasks created outside the window of dates don't get changed,
        while tasks created in the window do get changed.
        Verifies that non-queueing tasks never get changed.
        """
        self.update_task_created(created)

        call_command('fail_old_queueing_tasks', before=before, after=after)

        type_1_queueing, type_1_non_queueing, type_2_queueing = self.get_tasks()
        self.assertEqual(type_1_queueing.task_state, expected_state)
        self.assertEqual(type_2_queueing.task_state, expected_state)
        self.assertEqual(type_1_non_queueing.task_state, 'NOT QUEUEING')

    def test_filter_by_task_type(self):
        """
        Test that if we specify which task types to update, only tasks with
        those types are updated
        """
        self.update_task_created('2015-05-06')
        call_command(
            'fail_old_queueing_tasks',
            before='2015-05-07',
            after='2015-05-05',
            task_type="type_1",
        )
        type_1_queueing, type_1_non_queueing, type_2_queueing = self.get_tasks()
        self.assertEqual(type_1_queueing.task_state, FAILURE)
        # the other type of task shouldn't be updated
        self.assertEqual(type_2_queueing.task_state, QUEUING)
        self.assertEqual(type_1_non_queueing.task_state, 'NOT QUEUEING')

    @ddt.data(
        ('2015-05-05', None),
        (None, '2015-05-05'),
    )
    @ddt.unpack
    def test_date_errors(self, after, before):
        """
        Test that we get a CommandError when we don't supply before and after
        dates.
        """
        with self.assertRaises(CommandError):
            call_command('fail_old_queueing_tasks', before=before, after=after)
