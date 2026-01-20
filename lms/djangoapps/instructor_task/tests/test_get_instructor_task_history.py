"""
Tests for get_instructor_task_history in bulk email.
"""
import json
from celery.states import SUCCESS, FAILURE, REVOKED

from lms.djangoapps.instructor_task.api import get_instructor_task_history
from lms.djangoapps.instructor_task.tests.test_base import InstructorTaskCourseTestCase
from lms.djangoapps.instructor_task.tests.factories import InstructorTaskFactory


class TestGetInstructorTaskHistory(InstructorTaskCourseTestCase):
    """
    Tests for updated filtering logic in get_instructor_task_history

    Rules:
    - SUCCESS tasks must contain succeeded > 0 in task_output
    - SCHEDULED tasks must be included even if task_output is empty
    - SUCCESS tasks with succeeded = 0 must be excluded
    - FAILED / REVOKED tasks must be excluded
    """

    def setUp(self):
        super().setUp()
        self.initialize_course()
        self.instructor = self.create_instructor('instructor')

    def test_includes_successful_bulk_email_task(self):
        """
        SUCCESS + succeeded > 0 → INCLUDED
        """
        task_output = json.dumps({
            "attempted": 10,
            "succeeded": 10,
            "failed": 0
        })

        success_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_success",
            task_input='{}',
            task_state=SUCCESS,
            task_output=task_output,
            task_key='bulk_email_success',
            requester=self.instructor
        )

        tasks = list(get_instructor_task_history(
            self.course.id,
            task_type="bulk_course_email"
        ))

        assert success_task in tasks

    def test_includes_scheduled_task_with_empty_output(self):
        """
        SCHEDULED (even with empty {}) → INCLUDED
        """
        scheduled_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_scheduled",
            task_input='{}',
            task_state="SCHEDULED",
            task_output="{}",
            task_key='bulk_email_scheduled',
            requester=self.instructor
        )

        tasks = list(get_instructor_task_history(
            self.course.id,
            task_type="bulk_course_email"
        ))

        assert scheduled_task in tasks

    def test_excludes_zero_success_tasks(self):
        """
        SUCCESS + succeeded = 0 → EXCLUDED
        """
        zero_success_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_zero",
            task_state=SUCCESS,
            task_output=json.dumps({
                "attempted": 10,
                "succeeded": 0,
                "failed": 10
            }),
            task_key='bulk_email_zero',
            requester=self.instructor
        )

        tasks = list(get_instructor_task_history(
            self.course.id,
            task_type="bulk_course_email"
        ))

        assert zero_success_task not in tasks

    def test_excludes_failed_tasks(self):
        """
        FAILURE → EXCLUDED
        """
        failed_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_failed",
            task_state=FAILURE,
            task_output=json.dumps({
                "attempted": 5,
                "succeeded": 0,
                "failed": 5
            }),
            task_key='bulk_email_failed',
            requester=self.instructor
        )

        tasks = list(get_instructor_task_history(
            self.course.id,
            task_type="bulk_course_email"
        ))

        assert failed_task not in tasks

    def test_excludes_revoked_tasks(self):
        """
        REVOKED → EXCLUDED
        """
        revoked_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_revoked",
            task_state=REVOKED,
            task_output='{"message": "Task revoked"}',
            task_key='bulk_email_revoked',
            requester=self.instructor
        )

        tasks = list(get_instructor_task_history(
            self.course.id,
            task_type="bulk_course_email"
        ))

        assert revoked_task not in tasks

    def test_only_valid_tasks_returned(self):
        """
        Only the following should be returned:
        - SUCCESS with succeeded > 0
        - SCHEDULED

        Everything else must be excluded.
        """
        valid_success = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_valid",
            task_state=SUCCESS,
            task_output=json.dumps({
                "attempted": 8,
                "succeeded": 5,
                "failed": 3
            }),
            task_key='bulk_email_valid',
            requester=self.instructor
        )

        scheduled = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_scheduled_2",
            task_state="SCHEDULED",
            task_output="{}",
            task_key='bulk_email_scheduled_2',
            requester=self.instructor
        )

        zero_task = InstructorTaskFactory.create(
            course_id=self.course.id,
            task_type="bulk_course_email",
            task_id="bulk_email_zero_2",
            task_state=SUCCESS,
            task_output=json.dumps({
                "attempted": 5,
                "succeeded": 0,
                "failed": 5
            }),
            task_key='bulk_email_zero_2',
            requester=self.instructor
        )

        tasks = list(get_instructor_task_history(
            self.course.id,
            task_type="bulk_course_email"
        ))

        assert valid_success in tasks
        assert scheduled in tasks
        assert zero_task not in tasks
        assert len(tasks) == 2
