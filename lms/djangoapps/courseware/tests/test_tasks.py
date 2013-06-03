"""
Test for LMS courseware background tasks
"""
import logging
import json
from mock import Mock, patch
import textwrap
from uuid import uuid4

from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from capa.tests.response_xml_factory import (OptionResponseXMLFactory,
                                             CodeResponseXMLFactory,
                                             CustomResponseXMLFactory)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.exceptions import ItemNotFoundError
from student.tests.factories import CourseEnrollmentFactory, UserFactory, AdminFactory

from courseware.model_data import StudentModule
from courseware.task_submit import (submit_rescore_problem_for_all_students,
                                    submit_rescore_problem_for_student,
                                    course_task_status,
                                    submit_reset_problem_attempts_for_all_students,
                                    submit_delete_problem_state_for_all_students)
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_MONGO_MODULESTORE
from courseware.tests.factories import CourseTaskFactory


log = logging.getLogger(__name__)


TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_COURSE_NUMBER = '1.23x'
TEST_SECTION_NAME = "Problem"


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestRescoringBase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Test that all students' answers to a problem can be rescored after the
    definition of the problem has been redefined.
    """
    course = None
    current_user = None

    def initialize_course(self):
        """Create a course in the store, with a chapter and section."""
        self.module_store = modulestore()

        # Create the course
        self.course = CourseFactory.create(org=TEST_COURSE_ORG,
                                           number=TEST_COURSE_NUMBER,
                                           display_name=TEST_COURSE_NAME)

        # Add a chapter to the course
        chapter = ItemFactory.create(parent_location=self.course.location,
                                     display_name=TEST_SECTION_NAME)

        # add a sequence to the course to which the problems can be added
        self.problem_section = ItemFactory.create(parent_location=chapter.location,
                                                  template='i4x://edx/templates/sequential/Empty',
                                                  display_name=TEST_SECTION_NAME)

    @staticmethod
    def get_user_email(username):
        """Generate email address based on username"""
        return '{0}@test.com'.format(username)

    def login_username(self, username):
        """Login the user, given the `username`."""
        self.login(TestRescoringBase.get_user_email(username), "test")
        self.current_user = username

    def _create_user(self, username, is_staff=False):
        """Creates a user and enrolls them in the test course."""
        email = TestRescoringBase.get_user_email(username)
        if (is_staff):
            AdminFactory.create(username=username, email=email)
        else:
            UserFactory.create(username=username, email=email)
        thisuser = User.objects.get(username=username)
        CourseEnrollmentFactory.create(user=thisuser, course_id=self.course.id)
        return thisuser

    def create_instructor(self, username):
        """Creates an instructor for the test course."""
        return self._create_user(username, is_staff=True)

    def create_student(self, username):
        """Creates a student for the test course."""
        return self._create_user(username, is_staff=False)

    @staticmethod
    def problem_location(problem_url_name):
        """
        Create an internal location for a test problem.
        """
        if "i4x:" in problem_url_name:
            return problem_url_name
        else:
            return "i4x://{org}/{number}/problem/{problem_url_name}".format(org=TEST_COURSE_ORG,
                                                                            number=TEST_COURSE_NUMBER,
                                                                            problem_url_name=problem_url_name)

    def define_option_problem(self, problem_url_name):
        """Create the problem definition so the answer is Option 1"""
        factory = OptionResponseXMLFactory()
        factory_args = {'question_text': 'The correct answer is Option 1',
                        'options': ['Option 1', 'Option 2'],
                        'correct_option': 'Option 1',
                        'num_responses': 2}
        problem_xml = factory.build_xml(**factory_args)
        ItemFactory.create(parent_location=self.problem_section.location,
                           template="i4x://edx/templates/problem/Blank_Common_Problem",
                           display_name=str(problem_url_name),
                           data=problem_xml)

    def redefine_option_problem(self, problem_url_name):
        """Change the problem definition so the answer is Option 2"""
        factory = OptionResponseXMLFactory()
        factory_args = {'question_text': 'The correct answer is Option 2',
                        'options': ['Option 1', 'Option 2'],
                        'correct_option': 'Option 2',
                        'num_responses': 2}
        problem_xml = factory.build_xml(**factory_args)
        location = TestRescoring.problem_location(problem_url_name)
        self.module_store.update_item(location, problem_xml)

    def render_problem(self, username, problem_url_name):
        """
        Use ajax interface to request html for a problem.
        """
        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        if self.current_user != username:
            self.login_username(username)
        # make ajax call:
        modx_url = reverse('modx_dispatch',
                           kwargs={'course_id': self.course.id,
                                   'location': TestRescoring.problem_location(problem_url_name),
                                   'dispatch': 'problem_get', })
        resp = self.client.post(modx_url, {})
        return resp

    def submit_student_answer(self, username, problem_url_name, responses):
        """
        Use ajax interface to submit a student answer.

        Assumes the input list of responses has two values.
        """
        def get_input_id(response_id):
            """Creates input id using information about the test course and the current problem."""
            return 'input_i4x-{0}-{1}-problem-{2}_{3}'.format(TEST_COURSE_ORG.lower(),
                                                              TEST_COURSE_NUMBER.replace('.', '_'),
                                                              problem_url_name, response_id)

        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        if self.current_user != username:
            self.login_username(username)
        # make ajax call:
        modx_url = reverse('modx_dispatch',
                           kwargs={'course_id': self.course.id,
                                   'location': TestRescoring.problem_location(problem_url_name),
                                   'dispatch': 'problem_check', })

        resp = self.client.post(modx_url, {
            get_input_id('2_1'): responses[0],
            get_input_id('3_1'): responses[1],
        })
        return resp

    def create_task_request(self, requester_username):
        """Generate request that can be used for submitting tasks"""
        request = Mock()
        request.user = User.objects.get(username=requester_username)
        request.get_host = Mock(return_value="testhost")
        request.META = {'REMOTE_ADDR': '0:0:0:0', 'SERVER_NAME': 'testhost'}
        request.is_secure = Mock(return_value=False)
        return request

    def submit_rescore_all_student_answers(self, instructor, problem_url_name):
        """Submits the particular problem for rescoring"""
        return submit_rescore_problem_for_all_students(self.create_task_request(instructor), self.course.id,
                                                       TestRescoringBase.problem_location(problem_url_name))

    def submit_rescore_one_student_answer(self, instructor, problem_url_name, student):
        """Submits the particular problem for rescoring for a particular student"""
        return submit_rescore_problem_for_student(self.create_task_request(instructor), self.course.id,
                                                  TestRescoringBase.problem_location(problem_url_name),
                                                  student)

    def _create_course_task(self, task_state="QUEUED", task_input=None, student=None):
        """Creates a CourseTask entry for testing."""
        task_id = str(uuid4())
        task_key = "dummy value"
        course_task = CourseTaskFactory.create(requester=self.instructor,
                                                      task_input=json.dumps(task_input),
                                                      task_key=task_key,
                                                      task_id=task_id,
                                                      task_state=task_state)
        return course_task

    def rescore_all_student_answers(self, instructor, problem_url_name):
        """Runs the task to rescore the current problem"""
#TODO: fix this...
#        task_input = {'problem_url': TestRescoringBase.problem_location(problem_url_name)}
#       rescore_problem(entry_id, self.course_id, task_input, xmodule_instance_args)
        return submit_rescore_problem_for_all_students(self.create_task_request(instructor), self.course.id,
                                                       TestRescoringBase.problem_location(problem_url_name))

    def get_student_module(self, username, descriptor):
        """Get StudentModule object for test course, given the `username` and the problem's `descriptor`."""
        return StudentModule.objects.get(course_id=self.course.id,
                                         student=User.objects.get(username=username),
                                         module_type=descriptor.location.category,
                                         module_state_key=descriptor.location.url(),
                                         )

    def check_state(self, username, descriptor, expected_score, expected_max_score, expected_attempts):
        """
        Check that the StudentModule state contains the expected values.

        The student module is found for the test course, given the `username` and problem `descriptor`.

        Values checked include the number of attempts, the score, and the max score for a problem.
        """
        module = self.get_student_module(username, descriptor)
        self.assertEqual(module.grade, expected_score, "Scores were not equal")
        self.assertEqual(module.max_grade, expected_max_score, "Max scores were not equal")
        state = json.loads(module.state)
        attempts = state['attempts']
        self.assertEqual(attempts, expected_attempts, "Attempts were not equal")
        if attempts > 0:
            self.assertTrue('correct_map' in state)
            self.assertTrue('student_answers' in state)
            self.assertGreater(len(state['correct_map']), 0)
            self.assertGreater(len(state['student_answers']), 0)


class TestRescoring(TestRescoringBase):
    """Test rescoring problems in a background task."""

    def setUp(self):
        self.initialize_course()
        self.create_instructor('instructor')
        self.create_student('u1')
        self.create_student('u2')
        self.create_student('u3')
        self.create_student('u4')
        self.logout()

    def test_rescoring_option_problem(self):
        '''Run rescore scenario on option problem'''
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = TestRescoring.problem_location(problem_url_name)
        descriptor = self.module_store.get_instance(self.course.id, location)

        # first store answers for each of the separate users:
        self.submit_student_answer('u1', problem_url_name, ['Option 1', 'Option 1'])
        self.submit_student_answer('u2', problem_url_name, ['Option 1', 'Option 2'])
        self.submit_student_answer('u3', problem_url_name, ['Option 2', 'Option 1'])
        self.submit_student_answer('u4', problem_url_name, ['Option 2', 'Option 2'])

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
        self.submit_student_answer('u1', problem_url_name, ['Option 1', 'Option 1'])

        expected_message = "bad things happened"
        with patch('capa.capa_problem.LoncapaProblem.rescore_existing_answers') as mock_rescore:
            mock_rescore.side_effect = ZeroDivisionError(expected_message)
            course_task = self.submit_rescore_all_student_answers('instructor', problem_url_name)

        # check task_log returned
        self.assertEqual(course_task.task_state, 'FAILURE')
        self.assertEqual(course_task.requester.username, 'instructor')
        self.assertEqual(course_task.task_type, 'rescore_problem')
        task_input = json.loads(course_task.task_input)
        self.assertFalse('student' in task_input)
        self.assertEqual(task_input['problem_url'], TestRescoring.problem_location(problem_url_name))
        status = json.loads(course_task.task_output)
        self.assertEqual(status['exception'], 'ZeroDivisionError')
        self.assertEqual(status['message'], expected_message)

        # check status returned:
        mock_request = Mock()
        mock_request.REQUEST = {'task_id': course_task.task_id}
        response = course_task_status(mock_request)
        status = json.loads(response.content)
        self.assertEqual(status['message'], expected_message)

    def test_rescoring_non_problem(self):
        """confirm that a non-problem will not submit"""
        problem_url_name = self.problem_section.location.url()
        with self.assertRaises(NotImplementedError):
            self.submit_rescore_all_student_answers('instructor', problem_url_name)

    def test_rescoring_nonexistent_problem(self):
        """confirm that a non-existent problem will not submit"""
        problem_url_name = 'NonexistentProblem'
        with self.assertRaises(ItemNotFoundError):
            self.submit_rescore_all_student_answers('instructor', problem_url_name)

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
                           template="i4x://edx/templates/problem/Blank_Common_Problem",
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

        course_task = self.submit_rescore_all_student_answers('instructor', problem_url_name)
        self.assertEqual(course_task.task_state, FAILURE)
        status = json.loads(course_task.task_output)
        self.assertEqual(status['exception'], 'NotImplementedError')
        self.assertEqual(status['message'], "Problem's definition does not support rescoring")

        mock_request = Mock()
        mock_request.REQUEST = {'task_id': course_task.task_id}
        response = course_task_status(mock_request)
        status = json.loads(response.content)
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
        if redefine:
            script = textwrap.dedent("""
                def check_func(expect, answer_given):
                    expected = str(random.randint(0, 100))
                    return {'ok': answer_given != expected, 'msg': expected}
            """)
        else:
            script = textwrap.dedent("""
                def check_func(expect, answer_given):
                    expected = str(random.randint(0, 100))
                    return {'ok': answer_given == expected, 'msg': expected}
            """)
        problem_xml = factory.build_xml(script=script, cfn="check_func", expect="42", num_responses=1)
        if redefine:
            self.module_store.update_item(TestRescoringBase.problem_location(problem_url_name), problem_xml)
        else:
            # Use "per-student" rerandomization so that check-problem can be called more than once.
            # Using "always" means we cannot check a problem twice, but we want to call once to get the
            # correct answer, and call a second time with that answer to confirm it's graded as correct.
            # Per-student rerandomization will at least generate different seeds for different users, so
            # we get a little more test coverage.
            ItemFactory.create(parent_location=self.problem_section.location,
                               template="i4x://edx/templates/problem/Blank_Common_Problem",
                               display_name=str(problem_url_name),
                               data=problem_xml,
                               metadata={"rerandomize": "per_student"})

    def test_rescoring_randomized_problem(self):
        """Run rescore scenario on custom problem that uses randomize"""
        # First define the custom response problem:
        problem_url_name = 'H1P1'
        self.define_randomized_custom_response_problem(problem_url_name)
        location = TestRescoring.problem_location(problem_url_name)
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
            answer = correct_map[correct_map.keys()[0]]['msg']
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
        self.check_state('u1', descriptor, 0, 1, 2)
        self.check_state('u2', descriptor, 1, 1, 2)
        self.check_state('u3', descriptor, 1, 1, 2)
        self.check_state('u4', descriptor, 1, 1, 2)

        # rescore the problem for all students
        self.submit_rescore_all_student_answers('instructor', problem_url_name)

        # all grades should change to being wrong (with no change in attempts)
        for username in userlist:
            self.check_state(username, descriptor, 0, 1, 2)


class TestResetAttempts(TestRescoringBase):
    """Test resetting problem attempts in a background task."""
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
                                                              TestRescoringBase.problem_location(problem_url_name))

    def test_reset_attempts_on_problem(self):
        '''Run reset-attempts scenario on option problem'''
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = TestRescoringBase.problem_location(problem_url_name)
        descriptor = self.module_store.get_instance(self.course.id, location)
        num_attempts = 3
        # first store answers for each of the separate users:
        for _ in range(num_attempts):
            for username in self.userlist:
                self.submit_student_answer(username, problem_url_name, ['Option 1', 'Option 1'])

        for username in self.userlist:
            self.assertEquals(self.get_num_attempts(username, descriptor), num_attempts)

        self.reset_problem_attempts('instructor', problem_url_name)

        for username in self.userlist:
            self.assertEquals(self.get_num_attempts(username, descriptor), 0)

    def test_reset_failure(self):
        """Simulate a failure in resetting attempts on a problem"""
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, ['Option 1', 'Option 1'])

        expected_message = "bad things happened"
        with patch('courseware.models.StudentModule.save') as mock_save:
            mock_save.side_effect = ZeroDivisionError(expected_message)
            course_task = self.reset_problem_attempts('instructor', problem_url_name)

        # check task_log returned
        self.assertEqual(course_task.task_state, FAILURE)
        self.assertEqual(course_task.requester.username, 'instructor')
        self.assertEqual(course_task.task_type, 'reset_problem_attempts')
        task_input = json.loads(course_task.task_input)
        self.assertFalse('student' in task_input)
        self.assertEqual(task_input['problem_url'], TestRescoring.problem_location(problem_url_name))
        status = json.loads(course_task.task_output)
        self.assertEqual(status['exception'], 'ZeroDivisionError')
        self.assertEqual(status['message'], expected_message)

        # check status returned:
        mock_request = Mock()
        mock_request.REQUEST = {'task_id': course_task.task_id}
        response = course_task_status(mock_request)
        status = json.loads(response.content)
        self.assertEqual(status['message'], expected_message)

    def test_reset_non_problem(self):
        """confirm that a non-problem can still be successfully reset"""
        problem_url_name = self.problem_section.location.url()
        course_task = self.reset_problem_attempts('instructor', problem_url_name)
        self.assertEqual(course_task.task_state, SUCCESS)

    def test_reset_nonexistent_problem(self):
        """confirm that a non-existent problem will not submit"""
        problem_url_name = 'NonexistentProblem'
        with self.assertRaises(ItemNotFoundError):
            self.reset_problem_attempts('instructor', problem_url_name)


class TestDeleteProblem(TestRescoringBase):
    """Test deleting problem state in a background task."""
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
                                                            TestRescoringBase.problem_location(problem_url_name))

    def test_delete_problem_state(self):
        '''Run delete-state scenario on option problem'''
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = TestRescoringBase.problem_location(problem_url_name)
        descriptor = self.module_store.get_instance(self.course.id, location)
        # first store answers for each of the separate users:
        for username in self.userlist:
            self.submit_student_answer(username, problem_url_name, ['Option 1', 'Option 1'])
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
        self.submit_student_answer('u1', problem_url_name, ['Option 1', 'Option 1'])

        expected_message = "bad things happened"
        with patch('courseware.models.StudentModule.delete') as mock_delete:
            mock_delete.side_effect = ZeroDivisionError(expected_message)
            course_task = self.delete_problem_state('instructor', problem_url_name)

        # check task_log returned
        self.assertEqual(course_task.task_state, FAILURE)
        self.assertEqual(course_task.requester.username, 'instructor')
        self.assertEqual(course_task.task_type, 'delete_problem_state')
        task_input = json.loads(course_task.task_input)
        self.assertFalse('student' in task_input)
        self.assertEqual(task_input['problem_url'], TestRescoring.problem_location(problem_url_name))
        status = json.loads(course_task.task_output)
        self.assertEqual(status['exception'], 'ZeroDivisionError')
        self.assertEqual(status['message'], expected_message)

        # check status returned:
        mock_request = Mock()
        mock_request.REQUEST = {'task_id': course_task.task_id}
        response = course_task_status(mock_request)
        status = json.loads(response.content)
        self.assertEqual(status['message'], expected_message)

    def test_delete_non_problem(self):
        """confirm that a non-problem can still be successfully deleted"""
        problem_url_name = self.problem_section.location.url()
        course_task = self.delete_problem_state('instructor', problem_url_name)
        self.assertEqual(course_task.task_state, SUCCESS)

    def test_delete_nonexistent_module(self):
        """confirm that a non-existent module will not submit"""
        problem_url_name = 'NonexistentProblem'
        with self.assertRaises(ItemNotFoundError):
            self.delete_problem_state('instructor', problem_url_name)
