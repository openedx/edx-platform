"""
Unit tests for LMS instructor-initiated background tasks.

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
import json
from uuid import uuid4

from mock import Mock, MagicMock, patch
from nose.plugins.attrib import attr

from celery.states import SUCCESS, FAILURE
from django.utils.translation import ugettext_noop
from functools import partial

from xmodule.modulestore.exceptions import ItemNotFoundError
from opaque_keys.edx.locations import i4xEncoder

from courseware.models import StudentModule
from courseware.tests.factories import StudentModuleFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory

from lms.djangoapps.instructor_task.models import InstructorTask
from lms.djangoapps.instructor_task.tests.test_base import InstructorTaskModuleTestCase
from lms.djangoapps.instructor_task.tests.factories import InstructorTaskFactory
from lms.djangoapps.instructor_task.tasks import (
    rescore_problem,
    reset_problem_attempts,
    delete_problem_state,
    generate_certificates,
    export_ora2_data,
)
from lms.djangoapps.instructor_task.tasks_helper import (
    UpdateProblemModuleStateError,
    upload_ora2_data,
)

PROBLEM_URL_NAME = "test_urlname"


class TestTaskFailure(Exception):
    pass


class TestInstructorTasks(InstructorTaskModuleTestCase):

    def setUp(self):
        super(TestInstructorTasks, self).setUp()
        self.initialize_course()
        self.instructor = self.create_instructor('instructor')
        self.location = self.problem_location(PROBLEM_URL_NAME)

    def _create_input_entry(self, student_ident=None, use_problem_url=True, course_id=None):
        """Creates a InstructorTask entry for testing."""
        task_id = str(uuid4())
        task_input = {}
        if use_problem_url:
            task_input['problem_url'] = self.location
        if student_ident is not None:
            task_input['student'] = student_ident

        course_id = course_id or self.course.id
        instructor_task = InstructorTaskFactory.create(course_id=course_id,
                                                       requester=self.instructor,
                                                       task_input=json.dumps(task_input, cls=i4xEncoder),
                                                       task_key='dummy value',
                                                       task_id=task_id)
        return instructor_task

    def _get_xmodule_instance_args(self):
        """
        Calculate dummy values for parameters needed for instantiating xmodule instances.
        """
        return {'xqueue_callback_url_prefix': 'dummy_value',
                'request_info': {},
                }

    def _run_task_with_mock_celery(self, task_class, entry_id, task_id, expected_failure_message=None):
        """Submit a task and mock how celery provides a current_task."""
        self.current_task = Mock()
        self.current_task.request = Mock()
        self.current_task.request.id = task_id
        self.current_task.update_state = Mock()
        if expected_failure_message is not None:
            self.current_task.update_state.side_effect = TestTaskFailure(expected_failure_message)
        task_args = [entry_id, self._get_xmodule_instance_args()]

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_get_task:
            mock_get_task.return_value = self.current_task
            return task_class.apply(task_args, task_id=task_id).get()

    def _test_missing_current_task(self, task_class):
        """Check that a task_class fails when celery doesn't provide a current_task."""
        task_entry = self._create_input_entry()
        with self.assertRaises(ValueError):
            task_class(task_entry.id, self._get_xmodule_instance_args())

    def _test_undefined_course(self, task_class):
        """Run with celery, but with no course defined."""
        task_entry = self._create_input_entry(course_id="bogus/course/id")
        with self.assertRaises(ItemNotFoundError):
            self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id)

    def _test_undefined_problem(self, task_class):
        """Run with celery, but no problem defined."""
        task_entry = self._create_input_entry()
        with self.assertRaises(ItemNotFoundError):
            self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id)

    def _test_run_with_task(self, task_class, action_name, expected_num_succeeded,
                            expected_num_skipped=0, expected_attempted=0, expected_total=0):
        """Run a task and check the number of StudentModules processed."""
        task_entry = self._create_input_entry()
        status = self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id)
        expected_attempted = expected_attempted \
            if expected_attempted else expected_num_succeeded + expected_num_skipped
        expected_total = expected_total \
            if expected_total else expected_num_succeeded + expected_num_skipped
        # check return value
        self.assertEquals(status.get('attempted'), expected_attempted)
        self.assertEquals(status.get('succeeded'), expected_num_succeeded)
        self.assertEquals(status.get('skipped'), expected_num_skipped)
        self.assertEquals(status.get('total'), expected_total)
        self.assertEquals(status.get('action_name'), action_name)
        self.assertGreater(status.get('duration_ms'), 0)
        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(json.loads(entry.task_output), status)
        self.assertEquals(entry.task_state, SUCCESS)

    def _test_run_with_no_state(self, task_class, action_name):
        """Run with no StudentModules defined for the current problem."""
        self.define_option_problem(PROBLEM_URL_NAME)
        self._test_run_with_task(task_class, action_name, 0)

    def _create_students_with_state(self, num_students, state=None, grade=0, max_grade=1):
        """Create students, a problem, and StudentModule objects for testing"""
        self.define_option_problem(PROBLEM_URL_NAME)
        students = [
            UserFactory.create(username='robot%d' % i, email='robot+test+%d@edx.org' % i)
            for i in xrange(num_students)
        ]
        for student in students:
            CourseEnrollmentFactory.create(course_id=self.course.id, user=student)
            StudentModuleFactory.create(course_id=self.course.id,
                                        module_state_key=self.location,
                                        student=student,
                                        grade=grade,
                                        max_grade=max_grade,
                                        state=state)
        return students

    def _assert_num_attempts(self, students, num_attempts):
        """Check the number attempts for all students is the same"""
        for student in students:
            module = StudentModule.objects.get(course_id=self.course.id,
                                               student=student,
                                               module_state_key=self.location)
            state = json.loads(module.state)
            self.assertEquals(state['attempts'], num_attempts)

    def _test_run_with_failure(self, task_class, expected_message):
        """Run a task and trigger an artificial failure with the given message."""
        task_entry = self._create_input_entry()
        self.define_option_problem(PROBLEM_URL_NAME)
        with self.assertRaises(TestTaskFailure):
            self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id, expected_message)
        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(entry.task_state, FAILURE)
        output = json.loads(entry.task_output)
        self.assertEquals(output['exception'], 'TestTaskFailure')
        self.assertEquals(output['message'], expected_message)

    def _test_run_with_long_error_msg(self, task_class):
        """
        Run with an error message that is so long it will require
        truncation (as well as the jettisoning of the traceback).
        """
        task_entry = self._create_input_entry()
        self.define_option_problem(PROBLEM_URL_NAME)
        expected_message = "x" * 1500
        with self.assertRaises(TestTaskFailure):
            self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id, expected_message)
        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(entry.task_state, FAILURE)
        self.assertGreater(1023, len(entry.task_output))
        output = json.loads(entry.task_output)
        self.assertEquals(output['exception'], 'TestTaskFailure')
        self.assertEquals(output['message'], expected_message[:len(output['message']) - 3] + "...")
        self.assertNotIn('traceback', output)

    def _test_run_with_short_error_msg(self, task_class):
        """
        Run with an error message that is short enough to fit
        in the output, but long enough that the traceback won't.
        Confirm that the traceback is truncated.
        """
        task_entry = self._create_input_entry()
        self.define_option_problem(PROBLEM_URL_NAME)
        expected_message = "x" * 900
        with self.assertRaises(TestTaskFailure):
            self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id, expected_message)
        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(entry.task_state, FAILURE)
        self.assertGreater(1023, len(entry.task_output))
        output = json.loads(entry.task_output)
        self.assertEquals(output['exception'], 'TestTaskFailure')
        self.assertEquals(output['message'], expected_message)
        self.assertEquals(output['traceback'][-3:], "...")


@attr(shard=3)
class TestRescoreInstructorTask(TestInstructorTasks):
    """Tests problem-rescoring instructor task."""

    def test_rescore_missing_current_task(self):
        self._test_missing_current_task(rescore_problem)

    def test_rescore_undefined_course(self):
        self._test_undefined_course(rescore_problem)

    def test_rescore_undefined_problem(self):
        self._test_undefined_problem(rescore_problem)

    def test_rescore_with_no_state(self):
        self._test_run_with_no_state(rescore_problem, 'rescored')

    def test_rescore_with_failure(self):
        self._test_run_with_failure(rescore_problem, 'We expected this to fail')

    def test_rescore_with_long_error_msg(self):
        self._test_run_with_long_error_msg(rescore_problem)

    def test_rescore_with_short_error_msg(self):
        self._test_run_with_short_error_msg(rescore_problem)

    def test_rescoring_unrescorable(self):
        input_state = json.dumps({'done': True})
        num_students = 1
        self._create_students_with_state(num_students, input_state)
        task_entry = self._create_input_entry()
        mock_instance = MagicMock()
        del mock_instance.rescore_problem
        with patch('lms.djangoapps.instructor_task.tasks_helper.get_module_for_descriptor_internal') as mock_get_module:
            mock_get_module.return_value = mock_instance
            with self.assertRaises(UpdateProblemModuleStateError):
                self._run_task_with_mock_celery(rescore_problem, task_entry.id, task_entry.task_id)
        # check values stored in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        output = json.loads(entry.task_output)
        self.assertEquals(output['exception'], "UpdateProblemModuleStateError")
        self.assertEquals(output['message'], "Specified problem does not support rescoring.")
        self.assertGreater(len(output['traceback']), 0)

    def test_rescoring_success(self):
        input_state = json.dumps({'done': True})
        num_students = 10
        self._create_students_with_state(num_students, input_state)
        task_entry = self._create_input_entry()
        mock_instance = Mock()
        mock_instance.rescore_problem = Mock(return_value={'success': 'correct'})
        with patch('lms.djangoapps.instructor_task.tasks_helper.get_module_for_descriptor_internal') as mock_get_module:
            mock_get_module.return_value = mock_instance
            self._run_task_with_mock_celery(rescore_problem, task_entry.id, task_entry.task_id)
        # check return value
        entry = InstructorTask.objects.get(id=task_entry.id)
        output = json.loads(entry.task_output)
        self.assertEquals(output.get('attempted'), num_students)
        self.assertEquals(output.get('succeeded'), num_students)
        self.assertEquals(output.get('total'), num_students)
        self.assertEquals(output.get('action_name'), 'rescored')
        self.assertGreater(output.get('duration_ms'), 0)

    def test_rescoring_bad_result(self):
        # Confirm that rescoring does not succeed if "success" key is not an expected value.
        input_state = json.dumps({'done': True})
        num_students = 10
        self._create_students_with_state(num_students, input_state)
        task_entry = self._create_input_entry()
        mock_instance = Mock()
        mock_instance.rescore_problem = Mock(return_value={'success': 'bogus'})
        with patch('lms.djangoapps.instructor_task.tasks_helper.get_module_for_descriptor_internal') as mock_get_module:
            mock_get_module.return_value = mock_instance
            self._run_task_with_mock_celery(rescore_problem, task_entry.id, task_entry.task_id)
        # check return value
        entry = InstructorTask.objects.get(id=task_entry.id)
        output = json.loads(entry.task_output)
        self.assertEquals(output.get('attempted'), num_students)
        self.assertEquals(output.get('succeeded'), 0)
        self.assertEquals(output.get('total'), num_students)
        self.assertEquals(output.get('action_name'), 'rescored')
        self.assertGreater(output.get('duration_ms'), 0)

    def test_rescoring_missing_result(self):
        # Confirm that rescoring does not succeed if "success" key is not returned.
        input_state = json.dumps({'done': True})
        num_students = 10
        self._create_students_with_state(num_students, input_state)
        task_entry = self._create_input_entry()
        mock_instance = Mock()
        mock_instance.rescore_problem = Mock(return_value={'bogus': 'value'})
        with patch('lms.djangoapps.instructor_task.tasks_helper.get_module_for_descriptor_internal') as mock_get_module:
            mock_get_module.return_value = mock_instance
            self._run_task_with_mock_celery(rescore_problem, task_entry.id, task_entry.task_id)
        # check return value
        entry = InstructorTask.objects.get(id=task_entry.id)
        output = json.loads(entry.task_output)
        self.assertEquals(output.get('attempted'), num_students)
        self.assertEquals(output.get('succeeded'), 0)
        self.assertEquals(output.get('total'), num_students)
        self.assertEquals(output.get('action_name'), 'rescored')
        self.assertGreater(output.get('duration_ms'), 0)


@attr(shard=3)
class TestResetAttemptsInstructorTask(TestInstructorTasks):
    """Tests instructor task that resets problem attempts."""

    def test_reset_missing_current_task(self):
        self._test_missing_current_task(reset_problem_attempts)

    def test_reset_undefined_course(self):
        self._test_undefined_course(reset_problem_attempts)

    def test_reset_undefined_problem(self):
        self._test_undefined_problem(reset_problem_attempts)

    def test_reset_with_no_state(self):
        self._test_run_with_no_state(reset_problem_attempts, 'reset')

    def test_reset_with_failure(self):
        self._test_run_with_failure(reset_problem_attempts, 'We expected this to fail')

    def test_reset_with_long_error_msg(self):
        self._test_run_with_long_error_msg(reset_problem_attempts)

    def test_reset_with_short_error_msg(self):
        self._test_run_with_short_error_msg(reset_problem_attempts)

    def test_reset_with_some_state(self):
        initial_attempts = 3
        input_state = json.dumps({'attempts': initial_attempts})
        num_students = 10
        students = self._create_students_with_state(num_students, input_state)
        # check that entries were set correctly
        self._assert_num_attempts(students, initial_attempts)
        # run the task
        self._test_run_with_task(reset_problem_attempts, 'reset', num_students)
        # check that entries were reset
        self._assert_num_attempts(students, 0)

    def test_reset_with_zero_attempts(self):
        initial_attempts = 0
        input_state = json.dumps({'attempts': initial_attempts})
        num_students = 10
        students = self._create_students_with_state(num_students, input_state)
        # check that entries were set correctly
        self._assert_num_attempts(students, initial_attempts)
        # run the task
        self._test_run_with_task(reset_problem_attempts, 'reset', 0, expected_num_skipped=num_students)
        # check that entries were reset
        self._assert_num_attempts(students, 0)

    def _test_reset_with_student(self, use_email):
        """Run a reset task for one student, with several StudentModules for the problem defined."""
        num_students = 10
        initial_attempts = 3
        input_state = json.dumps({'attempts': initial_attempts})
        students = self._create_students_with_state(num_students, input_state)
        # check that entries were set correctly
        for student in students:
            module = StudentModule.objects.get(course_id=self.course.id,
                                               student=student,
                                               module_state_key=self.location)
            state = json.loads(module.state)
            self.assertEquals(state['attempts'], initial_attempts)

        if use_email:
            student_ident = students[3].email
        else:
            student_ident = students[3].username
        task_entry = self._create_input_entry(student_ident)

        status = self._run_task_with_mock_celery(reset_problem_attempts, task_entry.id, task_entry.task_id)
        # check return value
        self.assertEquals(status.get('attempted'), 1)
        self.assertEquals(status.get('succeeded'), 1)
        self.assertEquals(status.get('total'), 1)
        self.assertEquals(status.get('action_name'), 'reset')
        self.assertGreater(status.get('duration_ms'), 0)

        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(json.loads(entry.task_output), status)
        self.assertEquals(entry.task_state, SUCCESS)
        # check that the correct entry was reset
        for index, student in enumerate(students):
            module = StudentModule.objects.get(course_id=self.course.id,
                                               student=student,
                                               module_state_key=self.location)
            state = json.loads(module.state)
            if index == 3:
                self.assertEquals(state['attempts'], 0)
            else:
                self.assertEquals(state['attempts'], initial_attempts)

    def test_reset_with_student_username(self):
        self._test_reset_with_student(False)

    def test_reset_with_student_email(self):
        self._test_reset_with_student(True)


@attr(shard=3)
class TestDeleteStateInstructorTask(TestInstructorTasks):
    """Tests instructor task that deletes problem state."""

    def test_delete_missing_current_task(self):
        self._test_missing_current_task(delete_problem_state)

    def test_delete_undefined_course(self):
        self._test_undefined_course(delete_problem_state)

    def test_delete_undefined_problem(self):
        self._test_undefined_problem(delete_problem_state)

    def test_delete_with_no_state(self):
        self._test_run_with_no_state(delete_problem_state, 'deleted')

    def test_delete_with_failure(self):
        self._test_run_with_failure(delete_problem_state, 'We expected this to fail')

    def test_delete_with_long_error_msg(self):
        self._test_run_with_long_error_msg(delete_problem_state)

    def test_delete_with_short_error_msg(self):
        self._test_run_with_short_error_msg(delete_problem_state)

    def test_delete_with_some_state(self):
        # This will create StudentModule entries -- we don't have to worry about
        # the state inside them.
        num_students = 10
        students = self._create_students_with_state(num_students)
        # check that entries were created correctly
        for student in students:
            StudentModule.objects.get(course_id=self.course.id,
                                      student=student,
                                      module_state_key=self.location)
        self._test_run_with_task(delete_problem_state, 'deleted', num_students)
        # confirm that no state can be found anymore:
        for student in students:
            with self.assertRaises(StudentModule.DoesNotExist):
                StudentModule.objects.get(course_id=self.course.id,
                                          student=student,
                                          module_state_key=self.location)


class TestCertificateGenerationnstructorTask(TestInstructorTasks):
    """Tests instructor task that generates student certificates."""

    def test_generate_certificates_missing_current_task(self):
        """
        Test error is raised when certificate generation task run without current task
        """
        self._test_missing_current_task(generate_certificates)

    def test_generate_certificates_task_run(self):
        """
        Test certificate generation task run without any errors
        """
        self._test_run_with_task(
            generate_certificates,
            'certificates generated',
            0,
            0,
            expected_attempted=1,
            expected_total=1
        )


class TestOra2ResponsesInstructorTask(TestInstructorTasks):
    """Tests instructor task that fetches ora2 response data."""

    def test_ora2_missing_current_task(self):
        self._test_missing_current_task(export_ora2_data)

    def test_ora2_with_failure(self):
        self._test_run_with_failure(export_ora2_data, 'We expected this to fail')

    def test_ora2_with_long_error_msg(self):
        self._test_run_with_long_error_msg(export_ora2_data)

    def test_ora2_with_short_error_msg(self):
        self._test_run_with_short_error_msg(export_ora2_data)

    def test_ora2_runs_task(self):
        task_entry = self._create_input_entry()
        task_xmodule_args = self._get_xmodule_instance_args()

        with patch('lms.djangoapps.instructor_task.tasks.run_main_task') as mock_main_task:
            export_ora2_data(task_entry.id, task_xmodule_args)

            action_name = ugettext_noop('generated')
            task_fn = partial(upload_ora2_data, task_xmodule_args)

            mock_main_task.assert_called_once_with_args(task_entry.id, task_fn, action_name)
