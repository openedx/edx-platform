"""
Unit tests for instructor_task subtasks.
"""
from uuid import uuid4

from mock import Mock, patch
from django.test.utils import override_settings
from django.conf import settings

from student.models import CourseEnrollment

from instructor_task.subtasks import (
    queue_subtasks_for_query,
    generate_lists_from_queryset,
    get_number_of_subtasks_for_queryset
)
from instructor_task.tests.factories import InstructorTaskFactory
from instructor_task.tests.test_base import InstructorTaskCourseTestCase


class TestSubtasks(InstructorTaskCourseTestCase):
    """Tests for subtasks."""

    def setUp(self):
        super(TestSubtasks, self).setUp()
        self.initialize_course()

    def _enroll_students_in_course(self, course_id, num_students):
        """Create and enroll some students in the course."""

        for _ in range(num_students):
            random_id = uuid4().hex[:8]
            self.create_student(username='student{0}'.format(random_id))

    def item_list_generator(self, queryset, items_per_query, ordering_key, all_item_fields):
        for item_list in generate_lists_from_queryset(queryset, items_per_query, ordering_key, all_item_fields):
            for item in item_list:
                yield item

    def _queue_subtasks(self, create_subtask_fcn, items_per_query, items_per_task, initial_count, extra_count):
        """Queue subtasks while enrolling more students into course in the middle of the process."""

        task_id = str(uuid4())
        instructor_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_id=task_id,
            task_key='dummy_task_key',
            task_type='bulk_course_email',
        )

        self._enroll_students_in_course(self.course.id, initial_count)
        task_queryset = CourseEnrollment.objects.filter(course_id=self.course.id)

        item_generator = self.item_list_generator(task_queryset, items_per_query, 'pk', ['pk'])
        total_num_items=task_queryset.count()
        total_num_subtasks=get_number_of_subtasks_for_queryset(total_num_items, items_per_query, items_per_task)

        def initialize_subtask_info(*args):  # pylint: disable=unused-argument
            """Instead of initializing subtask info enroll some more students into course."""
            self._enroll_students_in_course(self.course.id, extra_count)
            return {}

        with patch('instructor_task.subtasks.initialize_subtask_info') as mock_initialize_subtask_info:
            mock_initialize_subtask_info.side_effect = initialize_subtask_info
            queue_subtasks_for_query(
                entry=instructor_task,
                action_name='action_name',
                create_subtask_fcn=create_subtask_fcn,
                item_generator=item_generator,
                item_fields=[],
                items_per_query=items_per_query,
                items_per_task=items_per_task,
                total_num_items=total_num_items,
                total_num_subtasks=total_num_subtasks,
            )

    def test_queue_subtasks_for_query1(self):
        """Test queue_subtasks_for_query() if in last query the subtasks only need to accommodate < items_per_tasks items."""

        mock_create_subtask_fcn = Mock()
        self._queue_subtasks(mock_create_subtask_fcn, 6, 3, 8, 1)

        # Check number of items for each subtask
        mock_create_subtask_fcn_args = mock_create_subtask_fcn.call_args_list
        self.assertEqual(len(mock_create_subtask_fcn_args[0][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[1][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[2][0][0]), 3)

    def test_queue_subtasks_for_query2(self):
        """Test queue_subtasks_for_query() if in last query the subtasks need to accommodate > items_per_task items."""

        mock_create_subtask_fcn = Mock()
        self._queue_subtasks(mock_create_subtask_fcn, 6, 3, 8, 3)

        # Check number of items for each subtask
        mock_create_subtask_fcn_args = mock_create_subtask_fcn.call_args_list
        self.assertEqual(len(mock_create_subtask_fcn_args[0][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[1][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[2][0][0]), 5)

    def test_queue_subtasks_for_query3(self):
        """Test queue_subtasks_for_query() if in last query the number of items available > items_per_query."""

        mock_create_subtask_fcn = Mock()
        self._queue_subtasks(mock_create_subtask_fcn, 6, 3, 11, 3)

        # Check number of items for each subtask
        mock_create_subtask_fcn_args = mock_create_subtask_fcn.call_args_list
        self.assertEqual(len(mock_create_subtask_fcn_args[0][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[1][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[2][0][0]), 3)
        self.assertEqual(len(mock_create_subtask_fcn_args[3][0][0]), 5)


    def _test_number_queries(self, students, number_of_queries):
        """
        `generate_lists_from_queryset` does the following queries:
        1) counts how many items are in the queryset
        2) initializes the `last_key` value
        3) generates 2n + 1 queries, where n is the amount of iterations
        of the while loop (note the +1 comes from the fact that
        the loop's condition does a query)
        3) Then, it does a query to see if there are any 'left over' items
        4) If so, it executes that query

        So if there are 50 people in a course, and we do 7 emails per task,
        we'll have the following queries at each step:
        1) 1
        2) 1
        3) 2 * (50 / 7) + 1 = 15
        4) 1
        5) 1 if 50 % 7 != 0 else 0
        = 19
        """
        self._enroll_students_in_course(self.course.id, 50)
        queryset = CourseEnrollment.objects.filter(course_id=self.course.id)
        item_generator = self.item_list_generator(
            queryset, settings.BULK_EMAIL_EMAILS_PER_QUERY, 'pk', ['pk']
        )

        with self.assertNumQueries(19):
            for item in item_generator:
                pass

    @override_settings(BULK_EMAIL_EMAILS_PER_TASK=3, BULK_EMAIL_EMAILS_PER_QUERY=7)
    def test_number_queries_1(self):
        self._test_number_queries(50, 19)

    @override_settings(BULK_EMAIL_EMAILS_PER_TASK=3, BULK_EMAIL_EMAILS_PER_QUERY=7)
    def test_number_queries_2(self):
        self._test_number_queries(49, 18)
