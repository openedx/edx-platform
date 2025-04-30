"""
Tests for Celery tasks used by the `course_home_api` app.
"""

from unittest.mock import patch

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.course_home_api.tasks import (
    COURSE_COMPLETION_FOR_USER_EVENT_NAME,
    collect_progress_for_user_in_course
)
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory, CourseRunFactory


class CalculateCompletionTaskTests(ModuleStoreTestCase):
    """
    Tests for the `emit_course_completion_analytics_for_user` Celery task.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course_run = CourseRunFactory()
        self.course_run_key_string = self.course_run['key']
        self.course = CourseFactory(key=self.course_run_key_string, course_runs=[self.course_run])
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course_run_key_string,
            mode="verified"
        )

    @patch("lms.djangoapps.course_home_api.tasks.calculate_progress_for_learner_in_course")
    @patch("lms.djangoapps.course_home_api.tasks.tracker.emit")
    def test_successful_event_emission(self, mock_tracker, mock_progress):
        """
        Test to ensure a tracker event is emit by the task with the expected completion information.
        """
        mock_progress.return_value = {
            "complete_count": 5,
            "incomplete_count": 2,
            "locked_count": 1,
            "total_count": 8,
            "complete_percentage": 0.62,
            "locked_percentage": 0.12,
            "incomplete_percentage": 0.26,
        }

        expected_data = {
            "user_id": self.user.id,
            "course_id": self.course_run_key_string,
            "enrollment_mode": self.enrollment.mode,
            "complete_count": 5,
            "incomplete_count": 2,
            "locked_count": 1,
            "total_count": 8,
            "complete_percentage": 0.62,
            "locked_percentage": 0.12,
            "incomplete_percentage": 0.26,
        }

        collect_progress_for_user_in_course(self.course_run_key_string, self.user.id)
        mock_progress.assert_called_once_with(CourseKey.from_string(self.course_run_key_string), self.user)
        mock_tracker.assert_called_once_with(
            COURSE_COMPLETION_FOR_USER_EVENT_NAME,
            expected_data,
        )

    @patch("lms.djangoapps.course_home_api.tasks.calculate_progress_for_learner_in_course")
    @patch("lms.djangoapps.course_home_api.tasks.tracker.emit")
    def test_aborted_task_user_dne(self, mock_tracker, mock_progress):
        """
        Test to ensure the task is aborted if we cannot find the user for some reason.
        """
        collect_progress_for_user_in_course(self.course_run_key_string, 8675309)
        mock_progress.assert_not_called()
        mock_tracker.assert_not_called()

    @patch("lms.djangoapps.course_home_api.tasks.calculate_progress_for_learner_in_course")
    @patch("lms.djangoapps.course_home_api.tasks.tracker.emit")
    def test_aborted_task_bad_course_id(self, mock_tracker, mock_progress):
        """
        Test to ensure the task is aborted if the course key provided is no good.
        """
        collect_progress_for_user_in_course("nonsense", self.user.id)
        mock_progress.assert_not_called()
        mock_tracker.assert_not_called()
