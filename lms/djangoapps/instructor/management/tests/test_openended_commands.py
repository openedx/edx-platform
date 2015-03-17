"""Test the openended_post management command."""

from datetime import datetime
import json
from mock import patch
from pytz import UTC

from django.conf import settings
from opaque_keys.edx.locations import Location

import capa.xqueue_interface as xqueue_interface
from courseware.courses import get_course_with_access
from courseware.tests.factories import StudentModuleFactory, UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from xmodule.tests.test_util_open_ended import (
    STATE_INITIAL, STATE_ACCESSING, STATE_POST_ASSESSMENT
)
from student.models import anonymous_id_for_user

from instructor.management.commands.openended_post import post_submission_for_student
from instructor.management.commands.openended_stats import calculate_task_statistics
from instructor.utils import get_module_for_student

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


class OpenEndedPostTest(ModuleStoreTestCase):
    """Test the openended_post management command."""

    def setUp(self):
        super(OpenEndedPostTest, self).setUp()
        self.user = UserFactory()
        store = modulestore()
        course_items = import_course_from_xml(store, self.user.id, TEST_DATA_DIR, ['open_ended'])  # pylint: disable=maybe-no-member
        self.course = course_items[0]
        self.course_id = self.course.id

        self.problem_location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestion")
        self.self_assessment_task_number = 0
        self.open_ended_task_number = 1

        self.student_on_initial = UserFactory()
        self.student_on_accessing = UserFactory()
        self.student_on_post_assessment = UserFactory()

        StudentModuleFactory.create(
            course_id=self.course_id,
            module_state_key=self.problem_location,
            student=self.student_on_initial,
            grade=0,
            max_grade=1,
            state=STATE_INITIAL
        )

        StudentModuleFactory.create(
            course_id=self.course_id,
            module_state_key=self.problem_location,
            student=self.student_on_accessing,
            grade=0,
            max_grade=1,
            state=STATE_ACCESSING
        )

        StudentModuleFactory.create(
            course_id=self.course_id,
            module_state_key=self.problem_location,
            student=self.student_on_post_assessment,
            grade=0,
            max_grade=1,
            state=STATE_POST_ASSESSMENT
        )

    def test_post_submission_for_student_on_initial(self):
        course = get_course_with_access(self.student_on_initial, 'load', self.course_id)

        dry_run_result = post_submission_for_student(self.student_on_initial, course, self.problem_location, self.open_ended_task_number, dry_run=True)
        self.assertFalse(dry_run_result)

        result = post_submission_for_student(self.student_on_initial, course, self.problem_location, self.open_ended_task_number, dry_run=False)
        self.assertFalse(result)

    def test_post_submission_for_student_on_accessing(self):
        course = get_course_with_access(self.student_on_accessing, 'load', self.course_id)

        dry_run_result = post_submission_for_student(self.student_on_accessing, course, self.problem_location, self.open_ended_task_number, dry_run=True)
        self.assertFalse(dry_run_result)

        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_send_to_queue:
            mock_send_to_queue.return_value = (0, "Successfully queued")

            module = get_module_for_student(self.student_on_accessing, self.problem_location)
            module.child_module.get_task_number(self.open_ended_task_number)

            student_response = "Here is an answer."
            student_anonymous_id = anonymous_id_for_user(self.student_on_accessing, None)
            submission_time = datetime.strftime(datetime.now(UTC), xqueue_interface.dateformat)

            result = post_submission_for_student(self.student_on_accessing, course, self.problem_location, self.open_ended_task_number, dry_run=False)

            self.assertTrue(result)
            mock_send_to_queue_body_arg = json.loads(mock_send_to_queue.call_args[1]['body'])
            self.assertEqual(mock_send_to_queue_body_arg['max_score'], 2)
            self.assertEqual(mock_send_to_queue_body_arg['student_response'], student_response)
            body_arg_student_info = json.loads(mock_send_to_queue_body_arg['student_info'])
            self.assertEqual(body_arg_student_info['anonymous_student_id'], student_anonymous_id)
            self.assertGreaterEqual(body_arg_student_info['submission_time'], submission_time)

    def test_post_submission_for_student_on_post_assessment(self):
        course = get_course_with_access(self.student_on_post_assessment, 'load', self.course_id)

        dry_run_result = post_submission_for_student(self.student_on_post_assessment, course, self.problem_location, self.open_ended_task_number, dry_run=True)
        self.assertFalse(dry_run_result)

        result = post_submission_for_student(self.student_on_post_assessment, course, self.problem_location, self.open_ended_task_number, dry_run=False)
        self.assertFalse(result)

    def test_post_submission_for_student_invalid_task(self):
        course = get_course_with_access(self.student_on_accessing, 'load', self.course_id)

        result = post_submission_for_student(self.student_on_accessing, course, self.problem_location, self.self_assessment_task_number, dry_run=False)
        self.assertFalse(result)

        out_of_bounds_task_number = 3
        result = post_submission_for_student(self.student_on_accessing, course, self.problem_location, out_of_bounds_task_number, dry_run=False)
        self.assertFalse(result)


class OpenEndedStatsTest(ModuleStoreTestCase):
    """Test the openended_stats management command."""

    def setUp(self):
        super(OpenEndedStatsTest, self).setUp()

        self.user = UserFactory()
        store = modulestore()
        course_items = import_course_from_xml(store, self.user.id, TEST_DATA_DIR, ['open_ended'])  # pylint: disable=maybe-no-member
        self.course = course_items[0]

        self.course_id = self.course.id
        self.problem_location = Location("edX", "open_ended", "2012_Fall", "combinedopenended", "SampleQuestion")
        self.task_number = 1
        self.invalid_task_number = 3

        self.student_on_initial = UserFactory()
        self.student_on_accessing = UserFactory()
        self.student_on_post_assessment = UserFactory()

        StudentModuleFactory.create(
            course_id=self.course_id,
            module_state_key=self.problem_location,
            student=self.student_on_initial,
            grade=0,
            max_grade=1,
            state=STATE_INITIAL
        )

        StudentModuleFactory.create(
            course_id=self.course_id,
            module_state_key=self.problem_location,
            student=self.student_on_accessing,
            grade=0,
            max_grade=1,
            state=STATE_ACCESSING
        )

        StudentModuleFactory.create(
            course_id=self.course_id,
            module_state_key=self.problem_location,
            student=self.student_on_post_assessment,
            grade=0,
            max_grade=1,
            state=STATE_POST_ASSESSMENT
        )

        self.students = [self.student_on_initial, self.student_on_accessing, self.student_on_post_assessment]

    def test_calculate_task_statistics(self):
        course = get_course_with_access(self.student_on_accessing, 'load', self.course_id)
        stats = calculate_task_statistics(self.students, course, self.problem_location, self.task_number, write_to_file=False)
        self.assertEqual(stats[OpenEndedChild.INITIAL], 1)
        self.assertEqual(stats[OpenEndedChild.ASSESSING], 1)
        self.assertEqual(stats[OpenEndedChild.POST_ASSESSMENT], 1)
        self.assertEqual(stats[OpenEndedChild.DONE], 0)

        stats = calculate_task_statistics(self.students, course, self.problem_location, self.invalid_task_number, write_to_file=False)
        self.assertEqual(stats[OpenEndedChild.INITIAL], 0)
        self.assertEqual(stats[OpenEndedChild.ASSESSING], 0)
        self.assertEqual(stats[OpenEndedChild.POST_ASSESSMENT], 0)
        self.assertEqual(stats[OpenEndedChild.DONE], 0)
