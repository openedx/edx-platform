"""
Integration Tests for LMS instructor-initiated background tasks.

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
import logging
import json
from mock import patch
import textwrap

from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from capa.tests.response_xml_factory import (CodeResponseXMLFactory,
                                             CustomResponseXMLFactory)
from xmodule.modulestore.tests.factories import ItemFactory

from courseware.model_data import StudentModule

from instructor_task.api import (submit_rescore_problem_for_all_students,
                                 submit_rescore_problem_for_student,
                                 submit_reset_problem_attempts_for_all_students,
                                 submit_delete_problem_state_for_all_students)
from instructor_task.models import InstructorTask
from instructor_task.tests.test_base import (InstructorTaskModuleTestCase, TEST_COURSE_ORG, TEST_COURSE_NUMBER,
                                             OPTION_1, OPTION_2)
from capa.responsetypes import StudentInputError


log = logging.getLogger(__name__)


class TestIntegrationTask(InstructorTaskModuleTestCase):
    """
    Base class to provide general methods used for "integration" testing of particular tasks.
    """

    def submit_student_answer(self, username, problem_url_name, responses):
        """
        Use ajax interface to submit a student answer.

        Assumes the input list of responses has two values.
        """
        def get_input_id(response_id):
            """Creates input id using information about the test course and the current problem."""
            # Note that this is a capa-specific convention.  The form is a version of the problem's
            # URL, modified so that it can be easily stored in html, prepended with "input-" and
            # appended with a sequence identifier for the particular response the input goes to.
            return 'input_i4x-{0}-{1}-problem-{2}_{3}'.format(TEST_COURSE_ORG.lower(),
                                                              TEST_COURSE_NUMBER.replace('.', '_'),
                                                              problem_url_name, response_id)

        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        self.login_username(username)
        # make ajax call:
        modx_url = reverse('modx_dispatch',
                           kwargs={'course_id': self.course.id,
                                   'location': InstructorTaskModuleTestCase.problem_location(problem_url_name),
                                   'dispatch': 'problem_check', })

        # we assume we have two responses, so assign them the correct identifiers.
        resp = self.client.post(modx_url, {
            get_input_id('2_1'): responses[0],
            get_input_id('3_1'): responses[1],
        })
        return resp

    def _assert_task_failure(self, entry_id, task_type, problem_url_name, expected_message):
        """Confirm that expected values are stored in InstructorTask on task failure."""
        instructor_task = InstructorTask.objects.get(id=entry_id)
        self.assertEqual(instructor_task.task_state, FAILURE)
        self.assertEqual(instructor_task.requester.username, 'instructor')
        self.assertEqual(instructor_task.task_type, task_type)
        task_input = json.loads(instructor_task.task_input)
        self.assertFalse('student' in task_input)
        self.assertEqual(task_input['problem_url'], InstructorTaskModuleTestCase.problem_location(problem_url_name))
        status = json.loads(instructor_task.task_output)
        self.assertEqual(status['exception'], 'ZeroDivisionError')
        self.assertEqual(status['message'], expected_message)
        # check status returned:
        status = InstructorTaskModuleTestCase.get_task_status(instructor_task.task_id)
        self.assertEqual(status['message'], expected_message)


class TestRescoringTask(TestIntegrationTask):
    """
    Integration-style tests for rescoring problems in a background task.

    Exercises real problems with a minimum of patching.
    """

    def setUp(self):
        self.initialize_course()
        self.create_instructor('instructor')
        self.create_student('u1')
        self.create_student('u2')
        self.create_student('u3')
        self.create_student('u4')
        self.logout()

    def render_problem(self, username, problem_url_name):
        """
        Use ajax interface to request html for a problem.
        """
        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        self.login_username(username)
        # make ajax call:
        modx_url = reverse('modx_dispatch',
                           kwargs={'course_id': self.course.id,
                                   'location': InstructorTaskModuleTestCase.problem_location(problem_url_name),
                                   'dispatch': 'problem_get', })
        resp = self.client.post(modx_url, {})
        return resp

    def check_state(self, username, descriptor, expected_score, expected_max_score, expected_attempts):
        """
        Check that the StudentModule state contains the expected values.

        The student module is found for the test course, given the `username` and problem `descriptor`.

        Values checked include the number of attempts, the score, and the max score for a problem.
        """
        module = self.get_student_module(username, descriptor)
        self.assertEqual(module.grade, expected_score)
        self.assertEqual(module.max_grade, expected_max_score)
        state = json.loads(module.state)
        attempts = state['attempts']
        self.assertEqual(attempts, expected_attempts)
        if attempts > 0:
            self.assertTrue('correct_map' in state)
            self.assertTrue('student_answers' in state)
            self.assertGreater(len(state['correct_map']), 0)
            self.assertGreater(len(state['student_answers']), 0)

    def submit_rescore_all_student_answers(self, instructor, problem_url_name):
        """Submits the particular problem for rescoring"""
        return submit_rescore_problem_for_all_students(self.create_task_request(instructor), self.course.id,
                                                       InstructorTaskModuleTestCase.problem_location(problem_url_name))

    def submit_rescore_one_student_answer(self, instructor, problem_url_name, student):
        """Submits the particular problem for rescoring for a particular student"""
        return submit_rescore_problem_for_student(self.create_task_request(instructor), self.course.id,
                                                  InstructorTaskModuleTestCase.problem_location(problem_url_name),
                                                  student)

    def test_rescoring_option_problem(self):
        """Run rescore scenario on option problem"""
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_instance(self.course.id, location)

        # first store answers for each of the separate users:
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])
        self.submit_student_answer('u2', problem_url_name, [OPTION_1, OPTION_2])
        self.submit_student_answer('u3', problem_url_name, [OPTION_2, OPTION_1])
        self.submit_student_answer('u4', problem_url_name, [OPTION_2, OPTION_2])

        self.check_state('u1', descriptor, 2, 2, 1)
        self.check_state('u2', descriptor, 1, 2, 1)
        self.check_state('u3', descriptor, 1, 2, 1)
        self.check_state('u4', descriptor, 0, 2, 1)

        # update the data in the problem definition
        self.redefine_option_problem(problem_url_name)
        # confirm that simply rendering the problem again does not result in a change
        # in the grade:
        self.render_problem('u1', problem_url_name)
        self.check_state('u1', descriptor, 2, 2, 1)

        # rescore the problem for only one student -- only that student's grade should change:
        self.submit_rescore_one_student_answer('instructor', problem_url_name, User.objects.get(username='u1'))
        self.check_state('u1', descriptor, 0, 2, 1)
        self.check_state('u2', descriptor, 1, 2, 1)
        self.check_state('u3', descriptor, 1, 2, 1)
        self.check_state('u4', descriptor, 0, 2, 1)

        # rescore the problem for all students
        self.submit_rescore_all_student_answers('instructor', problem_url_name)
        self.check_state('u1', descriptor, 0, 2, 1)
        self.check_state('u2', descriptor, 1, 2, 1)
        self.check_state('u3', descriptor, 1, 2, 1)
        self.check_state('u4', descriptor, 2, 2, 1)

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
        self.assertFalse('student' in task_input)
        self.assertEqual(task_input['problem_url'], InstructorTaskModuleTestCase.problem_location(problem_url_name))
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
        self.assertEqual(status['message'], "Problem's definition does not support rescoring")

        status = InstructorTaskModuleTestCase.get_task_status(instructor_task.task_id)
        self.assertEqual(status['message'], "Problem's definition does not support rescoring")

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
            self.module_store.update_item(InstructorTaskModuleTestCase.problem_location(problem_url_name), problem_xml)
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
        descriptor = self.module_store.get_instance(self.course.id, location)
        # run with more than one user
        userlist = ['u1', 'u2', 'u3', 'u4']
        for username in userlist:
            # first render the problem, so that a seed will be created for this user
            self.render_problem(username, problem_url_name)
            # submit a bogus answer, in order to get the problem to tell us its real answer
            dummy_answer = "1000"
            self.submit_student_answer(username, problem_url_name, [dummy_answer, dummy_answer])
            # we should have gotten the problem wrong, since we're way out of range:
            self.check_state(username, descriptor, 0, 1, 1)
            # dig the correct answer out of the problem's message
            module = self.get_student_module(username, descriptor)
            state = json.loads(module.state)
            correct_map = state['correct_map']
            log.info("Correct Map: %s", correct_map)
            # only one response, so pull it out:
            answer = correct_map.values()[0]['msg']
            self.submit_student_answer(username, problem_url_name, [answer, answer])
            # we should now get the problem right, with a second attempt:
            self.check_state(username, descriptor, 1, 1, 2)

        # redefine the problem (as stored in Mongo) so that the definition of correct changes
        self.define_randomized_custom_response_problem(problem_url_name, redefine=True)
        # confirm that simply rendering the problem again does not result in a change
        # in the grade (or the attempts):
        self.render_problem('u1', problem_url_name)
        self.check_state('u1', descriptor, 1, 1, 2)

        # rescore the problem for only one student -- only that student's grade should change
        # (and none of the attempts):
        self.submit_rescore_one_student_answer('instructor', problem_url_name, User.objects.get(username='u1'))
        for username in userlist:
            self.check_state(username, descriptor, 0 if username == 'u1' else 1, 1, 2)

        # rescore the problem for all students
        self.submit_rescore_all_student_answers('instructor', problem_url_name)

        # all grades should change to being wrong (with no change in attempts)
        for username in userlist:
            self.check_state(username, descriptor, 0, 1, 2)


class TestResetAttemptsTask(TestIntegrationTask):
    """
    Integration-style tests for resetting problem attempts in a background task.

    Exercises real problems with a minimum of patching.
    """
    userlist = ['u1', 'u2', 'u3', 'u4']

    def setUp(self):
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

    def reset_problem_attempts(self, instructor, problem_url_name):
        """Submits the current problem for resetting"""
        return submit_reset_problem_attempts_for_all_students(self.create_task_request(instructor), self.course.id,
                                                              InstructorTaskModuleTestCase.problem_location(problem_url_name))

    def test_reset_attempts_on_problem(self):
        """Run reset-attempts scenario on option problem"""
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_instance(self.course.id, location)
        num_attempts = 3
        # first store answers for each of the separate users:
        for _ in range(num_attempts):
            for username in self.userlist:
                self.submit_student_answer(username, problem_url_name, [OPTION_1, OPTION_1])

        for username in self.userlist:
            self.assertEquals(self.get_num_attempts(username, descriptor), num_attempts)

        self.reset_problem_attempts('instructor', problem_url_name)

        for username in self.userlist:
            self.assertEquals(self.get_num_attempts(username, descriptor), 0)

    def test_reset_failure(self):
        """Simulate a failure in resetting attempts on a problem"""
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])

        expected_message = "bad things happened"
        with patch('courseware.models.StudentModule.save') as mock_save:
            mock_save.side_effect = ZeroDivisionError(expected_message)
            instructor_task = self.reset_problem_attempts('instructor', problem_url_name)
        self._assert_task_failure(instructor_task.id, 'reset_problem_attempts', problem_url_name, expected_message)

    def test_reset_non_problem(self):
        """confirm that a non-problem can still be successfully reset"""
        problem_url_name = self.problem_section.location.url()
        instructor_task = self.reset_problem_attempts('instructor', problem_url_name)
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        self.assertEqual(instructor_task.task_state, SUCCESS)


class TestDeleteProblemTask(TestIntegrationTask):
    """
    Integration-style tests for deleting problem state in a background task.

    Exercises real problems with a minimum of patching.
    """
    userlist = ['u1', 'u2', 'u3', 'u4']

    def setUp(self):
        self.initialize_course()
        self.create_instructor('instructor')
        for username in self.userlist:
            self.create_student(username)
        self.logout()

    def delete_problem_state(self, instructor, problem_url_name):
        """Submits the current problem for deletion"""
        return submit_delete_problem_state_for_all_students(self.create_task_request(instructor), self.course.id,
                                                            InstructorTaskModuleTestCase.problem_location(problem_url_name))

    def test_delete_problem_state(self):
        """Run delete-state scenario on option problem"""
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        descriptor = self.module_store.get_instance(self.course.id, location)
        # first store answers for each of the separate users:
        for username in self.userlist:
            self.submit_student_answer(username, problem_url_name, [OPTION_1, OPTION_1])
        # confirm that state exists:
        for username in self.userlist:
            self.assertTrue(self.get_student_module(username, descriptor) is not None)
        # run delete task:
        self.delete_problem_state('instructor', problem_url_name)
        # confirm that no state can be found:
        for username in self.userlist:
            with self.assertRaises(StudentModule.DoesNotExist):
                self.get_student_module(username, descriptor)

    def test_delete_failure(self):
        """Simulate a failure in deleting state of a problem"""
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, [OPTION_1, OPTION_1])

        expected_message = "bad things happened"
        with patch('courseware.models.StudentModule.delete') as mock_delete:
            mock_delete.side_effect = ZeroDivisionError(expected_message)
            instructor_task = self.delete_problem_state('instructor', problem_url_name)
        self._assert_task_failure(instructor_task.id, 'delete_problem_state', problem_url_name, expected_message)

    def test_delete_non_problem(self):
        """confirm that a non-problem can still be successfully deleted"""
        problem_url_name = self.problem_section.location.url()
        instructor_task = self.delete_problem_state('instructor', problem_url_name)
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        self.assertEqual(instructor_task.task_state, SUCCESS)
