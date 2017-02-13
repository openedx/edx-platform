"""
Integration Tests for LMS instructor-initiated background tasks.

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
from collections import namedtuple
import ddt
import json
import logging
from mock import patch
from nose.plugins.attrib import attr
import textwrap

from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from openedx.core.djangoapps.util.testing import TestConditionalContent
from capa.tests.response_xml_factory import (CodeResponseXMLFactory,
                                             CustomResponseXMLFactory)
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.modulestore import ModuleStoreEnum

from courseware.model_data import StudentModule

from lms.djangoapps.instructor_task.api import (
    submit_rescore_problem_for_all_students,
    submit_rescore_problem_for_student,
    submit_reset_problem_attempts_for_all_students,
    submit_delete_problem_state_for_all_students
)
from lms.djangoapps.instructor_task.models import InstructorTask
from lms.djangoapps.instructor_task.tasks_helper import upload_grades_csv
from lms.djangoapps.instructor_task.tests.test_base import (
    InstructorTaskModuleTestCase,
    TestReportMixin,
    OPTION_1,
    OPTION_2,
)
from capa.responsetypes import StudentInputError
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from openedx.core.lib.url_utils import quote_slashes


log = logging.getLogger(__name__)


class TestIntegrationTask(InstructorTaskModuleTestCase):
    """
    Base class to provide general methods used for "integration" testing of particular tasks.
    """

    def _assert_task_failure(self, entry_id, task_type, problem_url_name, expected_message):
        """Confirm that expected values are stored in InstructorTask on task failure."""
        instructor_task = InstructorTask.objects.get(id=entry_id)
        self.assertEqual(instructor_task.task_state, FAILURE)
        self.assertEqual(instructor_task.requester.username, 'instructor')
        self.assertEqual(instructor_task.task_type, task_type)
        task_input = json.loads(instructor_task.task_input)
        self.assertNotIn('student', task_input)
        self.assertEqual(task_input['problem_url'], InstructorTaskModuleTestCase.problem_location(problem_url_name).to_deprecated_string())
        status = json.loads(instructor_task.task_output)
        self.assertEqual(status['exception'], 'ZeroDivisionError')
        self.assertEqual(status['message'], expected_message)
        # check status returned:
        status = InstructorTaskModuleTestCase.get_task_status(instructor_task.task_id)
        self.assertEqual(status['message'], expected_message)


@attr(shard=3)
@ddt.ddt
class TestRescoringTask(TestIntegrationTask):
    """
    Integration-style tests for rescoring problems in a background task.

    Exercises real problems with a minimum of patching.
    """

    def setUp(self):
        super(TestRescoringTask, self).setUp()

        self.initialize_course()
        self.create_instructor('instructor')
        self.user1 = self.create_student('u1')
        self.user2 = self.create_student('u2')
        self.user3 = self.create_student('u3')
        self.user4 = self.create_student('u4')
        self.users = [self.user1, self.user2, self.user3, self.user4]
        self.logout()

        # set up test user for performing test operations
        self.setup_user()

    def render_problem(self, username, problem_url_name):
        """
        Use ajax interface to request html for a problem.
        """
        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        self.login_username(username)
        # make ajax call:
        modx_url = reverse('xblock_handler', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'usage_id': quote_slashes(InstructorTaskModuleTestCase.problem_location(problem_url_name).to_deprecated_string()),
            'handler': 'xmodule_handler',
            'suffix': 'problem_get',
        })
        resp = self.client.post(modx_url, {})
        return resp

    def check_state(self, user, descriptor, expected_score, expected_max_score, expected_attempts=1):
        """
        Check that the StudentModule state contains the expected values.

        The student module is found for the test course, given the `username` and problem `descriptor`.

        Values checked include the number of attempts, the score, and the max score for a problem.
        """
        module = self.get_student_module(user.username, descriptor)
        self.assertEqual(module.grade, expected_score)
        self.assertEqual(module.max_grade, expected_max_score)
        state = json.loads(module.state)
        attempts = state['attempts']
        self.assertEqual(attempts, expected_attempts)
        if attempts > 0:
            self.assertIn('correct_map', state)
            self.assertIn('student_answers', state)
            self.assertGreater(len(state['correct_map']), 0)
            self.assertGreater(len(state['student_answers']), 0)

        # assume only one problem in the subsection and the grades
        # are in sync.
        expected_subsection_grade = expected_score

        course_grade = CourseGradeFactory().create(user, self.course)
        self.assertEquals(
            course_grade.graded_subsections_by_format['Homework'][self.problem_section.location].graded_total.earned,
            expected_subsection_grade,
        )

    def submit_rescore_all_student_answers(self, instructor, problem_url_name, only_if_higher=False):
        """Submits the particular problem for rescoring"""
        return submit_rescore_problem_for_all_students(
            self.create_task_request(instructor),
            InstructorTaskModuleTestCase.problem_location(problem_url_name),
            only_if_higher,
        )

    def submit_rescore_one_student_answer(self, instructor, problem_url_name, student, only_if_higher=False):
        """Submits the particular problem for rescoring for a particular student"""
        return submit_rescore_problem_for_student(
            self.create_task_request(instructor),
            InstructorTaskModuleTestCase.problem_location(problem_url_name),
            student,
            only_if_higher,
        )

    def verify_rescore_results(self, problem_edit, new_expected_scores, new_expected_max, rescore_if_higher):
        """
        Common helper to verify the results of rescoring for a single
        student and all students are as expected.
        """
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_item(location)

        # first store answers for each of the separate users:
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])
        self.submit_student_answer('u2', problem_url_name, [OPTION_1, OPTION_2])
        self.submit_student_answer('u3', problem_url_name, [OPTION_2, OPTION_1])
        self.submit_student_answer('u4', problem_url_name, [OPTION_2, OPTION_2])

        # verify each user's grade
        expected_original_scores = (2, 1, 1, 0)
        expected_original_max = 2
        for i, user in enumerate(self.users):
            self.check_state(user, descriptor, expected_original_scores[i], expected_original_max)

        # update the data in the problem definition so the answer changes.
        self.redefine_option_problem(problem_url_name, **problem_edit)

        # confirm that simply rendering the problem again does not change the grade
        self.render_problem('u1', problem_url_name)
        self.check_state(self.user1, descriptor, expected_original_scores[0], expected_original_max)

        # rescore the problem for only one student -- only that student's grade should change:
        self.submit_rescore_one_student_answer('instructor', problem_url_name, self.user1, rescore_if_higher)
        self.check_state(self.user1, descriptor, new_expected_scores[0], new_expected_max)
        for i, user in enumerate(self.users[1:], start=1):  # everyone other than user1
            self.check_state(user, descriptor, expected_original_scores[i], expected_original_max)

        # rescore the problem for all students
        self.submit_rescore_all_student_answers('instructor', problem_url_name, rescore_if_higher)
        for i, user in enumerate(self.users):
            self.check_state(user, descriptor, new_expected_scores[i], new_expected_max)

    RescoreTestData = namedtuple('RescoreTestData', 'edit, new_expected_scores, new_expected_max')

    @ddt.data(
        RescoreTestData(edit=dict(correct_answer=OPTION_2), new_expected_scores=(0, 1, 1, 2), new_expected_max=2),
        RescoreTestData(edit=dict(num_inputs=2), new_expected_scores=(2, 1, 1, 0), new_expected_max=4),
        RescoreTestData(edit=dict(num_inputs=4), new_expected_scores=(2, 1, 1, 0), new_expected_max=8),
        RescoreTestData(edit=dict(num_responses=4), new_expected_scores=(2, 1, 1, 0), new_expected_max=4),
        RescoreTestData(edit=dict(num_inputs=2, num_responses=4), new_expected_scores=(2, 1, 1, 0), new_expected_max=8),
    )
    @ddt.unpack
    def test_rescoring_option_problem(self, problem_edit, new_expected_scores, new_expected_max):
        """
        Run rescore scenario on option problem.
        Verify rescoring updates grade after content change.
        Original problem definition has:
            num_inputs = 1
            num_responses = 2
            correct_answer = OPTION_1
        """
        self.verify_rescore_results(
            problem_edit, new_expected_scores, new_expected_max, rescore_if_higher=False,
        )

    @ddt.data(
        RescoreTestData(edit=dict(), new_expected_scores=(2, 1, 1, 0), new_expected_max=2),
        RescoreTestData(edit=dict(correct_answer=OPTION_2), new_expected_scores=(2, 1, 1, 2), new_expected_max=2),
        RescoreTestData(edit=dict(num_inputs=2), new_expected_scores=(2, 1, 1, 0), new_expected_max=2),
    )
    @ddt.unpack
    def test_rescoring_if_higher(self, problem_edit, new_expected_scores, new_expected_max):
        self.verify_rescore_results(
            problem_edit, new_expected_scores, new_expected_max, rescore_if_higher=True,
        )

    def test_rescoring_failure(self):
        """Simulate a failure in rescoring a problem"""
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])

        expected_message = "bad things happened"
        with patch('capa.capa_problem.LoncapaProblem.rescore_existing_answers') as mock_rescore:
            mock_rescore.side_effect = ZeroDivisionError(expected_message)
            instructor_task = self.submit_rescore_all_student_answers('instructor', problem_url_name)
        self._assert_task_failure(instructor_task.id, 'rescore_problem', problem_url_name, expected_message)

    def test_rescoring_bad_unicode_input(self):
        """Generate a real failure in rescoring a problem, with an answer including unicode"""
        # At one point, the student answers that resulted in StudentInputErrors were being
        # persisted (even though they were not counted as an attempt).  That is not possible
        # now, so it's harder to generate a test for how such input is handled.
        problem_url_name = 'H1P1'
        # set up an option problem -- doesn't matter really what problem it is, but we need
        # it to have an answer.
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])

        # return an input error as if it were a numerical response, with an embedded unicode character:
        expected_message = u"Could not interpret '2/3\u03a9' as a number"
        with patch('capa.capa_problem.LoncapaProblem.rescore_existing_answers') as mock_rescore:
            mock_rescore.side_effect = StudentInputError(expected_message)
            instructor_task = self.submit_rescore_all_student_answers('instructor', problem_url_name)

        # check instructor_task returned
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        self.assertEqual(instructor_task.task_state, 'SUCCESS')
        self.assertEqual(instructor_task.requester.username, 'instructor')
        self.assertEqual(instructor_task.task_type, 'rescore_problem')
        task_input = json.loads(instructor_task.task_input)
        self.assertNotIn('student', task_input)
        self.assertEqual(task_input['problem_url'], InstructorTaskModuleTestCase.problem_location(problem_url_name).to_deprecated_string())
        status = json.loads(instructor_task.task_output)
        self.assertEqual(status['attempted'], 1)
        self.assertEqual(status['succeeded'], 0)
        self.assertEqual(status['total'], 1)

    def define_code_response_problem(self, problem_url_name):
        """
        Define an arbitrary code-response problem.

        We'll end up mocking its evaluation later.
        """
        factory = CodeResponseXMLFactory()
        grader_payload = json.dumps({"grader": "ps04/grade_square.py"})
        problem_xml = factory.build_xml(initial_display="def square(x):",
                                        answer_display="answer",
                                        grader_payload=grader_payload,
                                        num_responses=2)
        ItemFactory.create(parent_location=self.problem_section.location,
                           category="problem",
                           display_name=str(problem_url_name),
                           data=problem_xml)

    def test_rescoring_code_problem(self):
        """Run rescore scenario on problem with code submission"""
        problem_url_name = 'H1P2'
        self.define_code_response_problem(problem_url_name)
        # we fully create the CodeResponse problem, but just pretend that we're queuing it:
        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_send_to_queue:
            mock_send_to_queue.return_value = (0, "Successfully queued")
            self.submit_student_answer('u1', problem_url_name, ["answer1", "answer2"])

        instructor_task = self.submit_rescore_all_student_answers('instructor', problem_url_name)

        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        self.assertEqual(instructor_task.task_state, FAILURE)
        status = json.loads(instructor_task.task_output)
        self.assertEqual(status['exception'], 'NotImplementedError')
        self.assertEqual(status['message'], "Problem's definition does not support rescoring.")

        status = InstructorTaskModuleTestCase.get_task_status(instructor_task.task_id)
        self.assertEqual(status['message'], "Problem's definition does not support rescoring.")

    def define_randomized_custom_response_problem(self, problem_url_name, redefine=False):
        """
        Defines a custom response problem that uses a random value to determine correctness.

        Generated answer is also returned as the `msg`, so that the value can be used as a
        correct answer by a test.

        If the `redefine` flag is set, then change the definition of correctness (from equals
        to not-equals).
        """
        factory = CustomResponseXMLFactory()
        script = textwrap.dedent("""
                def check_func(expect, answer_given):
                    expected = str(random.randint(0, 100))
                    return {'ok': answer_given %s expected, 'msg': expected}
            """ % ('!=' if redefine else '=='))
        problem_xml = factory.build_xml(script=script, cfn="check_func", expect="42", num_responses=1)
        if redefine:
            descriptor = self.module_store.get_item(
                InstructorTaskModuleTestCase.problem_location(problem_url_name)
            )
            descriptor.data = problem_xml
            with self.module_store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, descriptor.location.course_key):
                self.module_store.update_item(descriptor, self.user.id)
                self.module_store.publish(descriptor.location, self.user.id)
        else:
            # Use "per-student" rerandomization so that check-problem can be called more than once.
            # Using "always" means we cannot check a problem twice, but we want to call once to get the
            # correct answer, and call a second time with that answer to confirm it's graded as correct.
            # Per-student rerandomization will at least generate different seeds for different users, so
            # we get a little more test coverage.
            ItemFactory.create(parent_location=self.problem_section.location,
                               category="problem",
                               display_name=str(problem_url_name),
                               data=problem_xml,
                               metadata={"rerandomize": "per_student"})

    def test_rescoring_randomized_problem(self):
        """Run rescore scenario on custom problem that uses randomize"""
        # First define the custom response problem:
        problem_url_name = 'H1P1'
        self.define_randomized_custom_response_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_item(location)
        # run with more than one user
        for user in self.users:
            # first render the problem, so that a seed will be created for this user
            self.render_problem(user.username, problem_url_name)
            # submit a bogus answer, in order to get the problem to tell us its real answer
            dummy_answer = "1000"
            self.submit_student_answer(user.username, problem_url_name, [dummy_answer, dummy_answer])
            # we should have gotten the problem wrong, since we're way out of range:
            self.check_state(user, descriptor, 0, 1, expected_attempts=1)
            # dig the correct answer out of the problem's message
            module = self.get_student_module(user.username, descriptor)
            state = json.loads(module.state)
            correct_map = state['correct_map']
            log.info("Correct Map: %s", correct_map)
            # only one response, so pull it out:
            answer = correct_map.values()[0]['msg']
            self.submit_student_answer(user.username, problem_url_name, [answer, answer])
            # we should now get the problem right, with a second attempt:
            self.check_state(user, descriptor, 1, 1, expected_attempts=2)

        # redefine the problem (as stored in Mongo) so that the definition of correct changes
        self.define_randomized_custom_response_problem(problem_url_name, redefine=True)
        # confirm that simply rendering the problem again does not result in a change
        # in the grade (or the attempts):
        self.render_problem('u1', problem_url_name)
        self.check_state(self.user1, descriptor, 1, 1, expected_attempts=2)

        # rescore the problem for only one student -- only that student's grade should change
        # (and none of the attempts):
        self.submit_rescore_one_student_answer('instructor', problem_url_name, User.objects.get(username='u1'))
        for user in self.users:
            expected_score = 0 if user.username == 'u1' else 1
            self.check_state(user, descriptor, expected_score, 1, expected_attempts=2)

        # rescore the problem for all students
        self.submit_rescore_all_student_answers('instructor', problem_url_name)

        # all grades should change to being wrong (with no change in attempts)
        for user in self.users:
            self.check_state(user, descriptor, 0, 1, expected_attempts=2)


class TestResetAttemptsTask(TestIntegrationTask):
    """
    Integration-style tests for resetting problem attempts in a background task.

    Exercises real problems with a minimum of patching.
    """
    userlist = ['u1', 'u2', 'u3', 'u4']

    def setUp(self):
        super(TestResetAttemptsTask, self).setUp()
        self.initialize_course()
        self.create_instructor('instructor')
        for username in self.userlist:
            self.create_student(username)
        self.logout()

    def get_num_attempts(self, username, descriptor):
        """returns number of attempts stored for `username` on problem `descriptor` for test course"""
        module = self.get_student_module(username, descriptor)
        state = json.loads(module.state)
        return state['attempts']

    def reset_problem_attempts(self, instructor, location):
        """Submits the current problem for resetting"""
        return submit_reset_problem_attempts_for_all_students(self.create_task_request(instructor),
                                                              location)

    def test_reset_attempts_on_problem(self):
        """Run reset-attempts scenario on option problem"""
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_item(location)
        num_attempts = 3
        # first store answers for each of the separate users:
        for _ in range(num_attempts):
            for username in self.userlist:
                self.submit_student_answer(username, problem_url_name, [OPTION_1, OPTION_1])

        for username in self.userlist:
            self.assertEquals(self.get_num_attempts(username, descriptor), num_attempts)

        self.reset_problem_attempts('instructor', location)

        for username in self.userlist:
            self.assertEquals(self.get_num_attempts(username, descriptor), 0)

    def test_reset_failure(self):
        """Simulate a failure in resetting attempts on a problem"""
        problem_url_name = 'H1P1'
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])

        expected_message = "bad things happened"
        with patch('courseware.models.StudentModule.save') as mock_save:
            mock_save.side_effect = ZeroDivisionError(expected_message)
            instructor_task = self.reset_problem_attempts('instructor', location)
        self._assert_task_failure(instructor_task.id, 'reset_problem_attempts', problem_url_name, expected_message)

    def test_reset_non_problem(self):
        """confirm that a non-problem can still be successfully reset"""
        location = self.problem_section.location
        instructor_task = self.reset_problem_attempts('instructor', location)
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        self.assertEqual(instructor_task.task_state, SUCCESS)


class TestDeleteProblemTask(TestIntegrationTask):
    """
    Integration-style tests for deleting problem state in a background task.

    Exercises real problems with a minimum of patching.
    """
    userlist = ['u1', 'u2', 'u3', 'u4']

    def setUp(self):
        super(TestDeleteProblemTask, self).setUp()

        self.initialize_course()
        self.create_instructor('instructor')
        for username in self.userlist:
            self.create_student(username)
        self.logout()

    def delete_problem_state(self, instructor, location):
        """Submits the current problem for deletion"""
        return submit_delete_problem_state_for_all_students(self.create_task_request(instructor), location)

    def test_delete_problem_state(self):
        """Run delete-state scenario on option problem"""
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_item(location)
        # first store answers for each of the separate users:
        for username in self.userlist:
            self.submit_student_answer(username, problem_url_name, [OPTION_1, OPTION_1])
        # confirm that state exists:
        for username in self.userlist:
            self.assertIsNotNone(self.get_student_module(username, descriptor))
        # run delete task:
        self.delete_problem_state('instructor', location)
        # confirm that no state can be found:
        for username in self.userlist:
            with self.assertRaises(StudentModule.DoesNotExist):
                self.get_student_module(username, descriptor)

    def test_delete_failure(self):
        """Simulate a failure in deleting state of a problem"""
        problem_url_name = 'H1P1'
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])

        expected_message = "bad things happened"
        with patch('courseware.models.StudentModule.delete') as mock_delete:
            mock_delete.side_effect = ZeroDivisionError(expected_message)
            instructor_task = self.delete_problem_state('instructor', location)
        self._assert_task_failure(instructor_task.id, 'delete_problem_state', problem_url_name, expected_message)

    def test_delete_non_problem(self):
        """confirm that a non-problem can still be successfully deleted"""
        location = self.problem_section.location
        instructor_task = self.delete_problem_state('instructor', location)
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        self.assertEqual(instructor_task.task_state, SUCCESS)


class TestGradeReportConditionalContent(TestReportMixin, TestConditionalContent, TestIntegrationTask):
    """
    Test grade report in cases where there are problems contained within split tests.
    """

    def verify_csv_task_success(self, task_result):
        """
        Verify that all students were successfully graded by
        `upload_grades_csv`.

        Arguments:
            task_result (dict): Return value of `upload_grades_csv`.
        """
        self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, task_result)

    def verify_grades_in_csv(self, students_grades, ignore_other_columns=False):
        """
        Verify that the grades CSV contains the expected grades data.

        Arguments:
            students_grades (iterable): An iterable of dictionaries,
                where each dict maps a student to another dict
                representing their grades we expect to see in the CSV.
                For example: [student_a: {'grade': 1.0, 'HW': 1.0}]
        """
        def merge_dicts(*dicts):
            """
            Return the union of dicts

            Arguments:
                dicts: tuple of dicts
            """
            return dict([item for d in dicts for item in d.items()])

        def user_partition_group(user):
            """Return a dict having single key with value equals to students group in partition"""
            group_config_hdr_tpl = 'Experiment Group ({})'
            return {
                group_config_hdr_tpl.format(self.partition.name): self.partition.scheme.get_group_for_user(
                    self.course.id, user, self.partition, track_function=None
                ).name
            }

        self.verify_rows_in_csv(
            [
                merge_dicts(
                    {'Student ID': str(student.id), 'Username': student.username, 'Email': student.email},
                    grades,
                    user_partition_group(student)
                )
                for student_grades in students_grades for student, grades in student_grades.iteritems()
            ],
            ignore_other_columns=ignore_other_columns,
        )

    def test_both_groups_problems(self):
        """
        Verify that grade export works when each user partition
        receives (different) problems.  Each user's grade on their
        particular problem should show up in the grade report.
        """
        problem_a_url = 'problem_a_url'
        problem_b_url = 'problem_b_url'
        self.define_option_problem(problem_a_url, parent=self.vertical_a)
        self.define_option_problem(problem_b_url, parent=self.vertical_b)
        # student A will get 100%, student B will get 50% because
        # OPTION_1 is the correct option, and OPTION_2 is the
        # incorrect option
        self.submit_student_answer(self.student_a.username, problem_a_url, [OPTION_1, OPTION_1])
        self.submit_student_answer(self.student_b.username, problem_b_url, [OPTION_1, OPTION_2])

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_grades_csv(None, None, self.course.id, None, 'graded')
            self.verify_csv_task_success(result)
            self.verify_grades_in_csv(
                [
                    {
                        self.student_a: {
                            u'Grade': '1.0',
                            u'Homework': '1.0',
                        }
                    },
                    {
                        self.student_b: {
                            u'Grade': '0.5',
                            u'Homework': '0.5',
                        }
                    },
                ],
                ignore_other_columns=True,
            )

    def test_one_group_problem(self):
        """
        Verify that grade export works when only the Group A user
        partition receives a problem.  We expect to see a column for
        the homework where student_a's entry includes their grade, and
        student b's entry shows a 0.
        """
        problem_a_url = 'problem_a_url'
        self.define_option_problem(problem_a_url, parent=self.vertical_a)

        self.submit_student_answer(self.student_a.username, problem_a_url, [OPTION_1, OPTION_1])

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_grades_csv(None, None, self.course.id, None, 'graded')
            self.verify_csv_task_success(result)
            self.verify_grades_in_csv(
                [
                    {
                        self.student_a: {
                            u'Grade': '1.0',
                            u'Homework': '1.0',
                        },
                    },
                    {
                        self.student_b: {
                            u'Grade': '0.0',
                            u'Homework': u'Not Available',
                        }
                    },
                ],
                ignore_other_columns=True
            )
