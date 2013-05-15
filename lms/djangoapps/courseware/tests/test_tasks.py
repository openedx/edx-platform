'''
Test for LMS courseware background tasks
'''
import logging
import json
from mock import Mock, patch

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from capa.tests.response_xml_factory import OptionResponseXMLFactory, CodeResponseXMLFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.exceptions import ItemNotFoundError
from student.tests.factories import CourseEnrollmentFactory, UserFactory, AdminFactory

from courseware.model_data import StudentModule
from courseware.task_queue import (submit_regrade_problem_for_all_students, 
                                   submit_regrade_problem_for_student,
                                   course_task_log_status)
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_MONGO_MODULESTORE


log = logging.getLogger("mitx." + __name__)


TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_COURSE_NUMBER = '1.23x'
TEST_SECTION_NAME = "Problem"


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestRegradingBase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Test that all students' answers to a problem can be regraded after the
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
        return '{0}@test.com'.format(username)

    @staticmethod
    def get_user_password(username):
        return 'test'

    def login_username(self, username):
        self.login(TestRegradingBase.get_user_email(username), TestRegradingBase.get_user_password(username))
        self.current_user = username

    def _create_user(self, username, is_staff=False):
        email = TestRegradingBase.get_user_email(username)
        if (is_staff):
            AdminFactory.create(username=username, email=email)
        else:
            UserFactory.create(username=username, email=email)
        thisuser = User.objects.get(username=username)
        CourseEnrollmentFactory.create(user=thisuser, course_id=self.course.id)
        return thisuser

    def create_instructor(self, username):
        return self._create_user(username, is_staff=True)

    def create_student(self, username):
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
        location = TestRegrading.problem_location(problem_url_name)
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
                            kwargs={
                                'course_id': self.course.id,
                                'location': TestRegrading.problem_location(problem_url_name),
                                'dispatch': 'problem_get', })
        resp = self.client.post(modx_url, {})
        return resp

    def submit_student_answer(self, username, problem_url_name, responses):
        """
        Use ajax interface to submit a student answer.

        Assumes the input list of responses has two values.
        """
        def get_input_id(response_id):
            return 'input_i4x-{0}-{1}-problem-{2}_{3}'.format(TEST_COURSE_ORG.lower(),
                                                              TEST_COURSE_NUMBER.replace('.', '_'),
                                                              problem_url_name, response_id)

        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        if self.current_user != username:
            self.login_username(username)
        # make ajax call:
        modx_url = reverse('modx_dispatch',
                            kwargs={
                                'course_id': self.course.id,
                                'location': TestRegrading.problem_location(problem_url_name),
                                'dispatch': 'problem_check', })

        resp = self.client.post(modx_url, {
            get_input_id('2_1'): responses[0],
            get_input_id('3_1'): responses[1],
        })
        return resp

    def _create_task_request(self, requester_username):
        """Generate request that can be used for submitting tasks"""
        request = Mock()
        request.user = User.objects.get(username=requester_username)
        request.get_host = Mock(return_value="testhost")
        request.META = {'REMOTE_ADDR': '0:0:0:0', 'SERVER_NAME': 'testhost'}
        request.is_secure = Mock(return_value=False)
        return request

    def regrade_all_student_answers(self, instructor, problem_url_name):
        """Submits the current problem for regrading"""
        return submit_regrade_problem_for_all_students(self._create_task_request(instructor), self.course.id,
                                                       TestRegradingBase.problem_location(problem_url_name))

    def regrade_one_student_answer(self, instructor, problem_url_name, student):
        """Submits the current problem for regrading for a particular student"""
        return submit_regrade_problem_for_student(self._create_task_request(instructor), self.course.id,
                                                  TestRegradingBase.problem_location(problem_url_name),
                                                  student)

    def show_correct_answer(self, problem_url_name):
        modx_url = reverse('modx_dispatch',
                            kwargs={
                                'course_id': self.course.id,
                                'location': TestRegradingBase.problem_location(problem_url_name),
                                'dispatch': 'problem_show', })
        return self.client.post(modx_url, {})

    def get_student_module(self, username, descriptor):
        return StudentModule.objects.get(course_id=self.course.id,
                                         student=User.objects.get(username=username),
                                         module_type=descriptor.location.category,
                                         module_state_key=descriptor.location.url(),
                                         )

    def check_state(self, username, descriptor, expected_score, expected_max_score, expected_attempts):
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


class TestRegrading(TestRegradingBase):

    def setUp(self):
        self.initialize_course()
        self.create_instructor('instructor')
        self.create_student('u1')
        self.create_student('u2')
        self.create_student('u3')
        self.create_student('u4')
        self.logout()

    def testRegradingOptionProblem(self):
        '''Run regrade scenario on option problem'''
        # get descriptor:
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = TestRegrading.problem_location(problem_url_name)
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

        # regrade the problem for only one student -- only that student's grade should change:
        self.regrade_one_student_answer('instructor', problem_url_name, User.objects.get(username='u1'))
        self.check_state('u1', descriptor, 0, 2, 1)
        self.check_state('u2', descriptor, 1, 2, 1)
        self.check_state('u3', descriptor, 1, 2, 1)
        self.check_state('u4', descriptor, 0, 2, 1)

        # regrade the problem for all students
        self.regrade_all_student_answers('instructor', problem_url_name)
        self.check_state('u1', descriptor, 0, 2, 1)
        self.check_state('u2', descriptor, 1, 2, 1)
        self.check_state('u3', descriptor, 1, 2, 1)
        self.check_state('u4', descriptor, 2, 2, 1)

    def define_code_response_problem(self, problem_url_name):
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

    def testRegradingFailure(self):
        """Simulate a failure in regrading a problem"""
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        self.submit_student_answer('u1', problem_url_name, ['Option 1', 'Option 1'])

        expected_message = "bad things happened"
        with patch('capa.capa_problem.LoncapaProblem.regrade_existing_answers') as mock_regrade:
            mock_regrade.side_effect = ZeroDivisionError(expected_message)
            course_task_log = self.regrade_all_student_answers('instructor', problem_url_name)

        # check task_log returned
        self.assertEqual(course_task_log.task_state, 'FAILURE')
        self.assertEqual(course_task_log.student, None)
        self.assertEqual(course_task_log.requester.username, 'instructor')
        self.assertEqual(course_task_log.task_name, 'regrade_problem')
        self.assertEqual(course_task_log.task_args, TestRegrading.problem_location(problem_url_name))
        status = json.loads(course_task_log.task_progress)
        self.assertEqual(status['exception'], 'ZeroDivisionError')
        self.assertEqual(status['message'], expected_message)

        # check status returned:
        mock_request = Mock()
        response = course_task_log_status(mock_request, task_id=course_task_log.task_id)
        status = json.loads(response.content)
        self.assertEqual(status['message'], expected_message)

    def testRegradingNonProblem(self):
        """confirm that a non-problem will not submit"""
        problem_url_name = self.problem_section.location.url()
        with self.assertRaises(NotImplementedError):
            self.regrade_all_student_answers('instructor', problem_url_name)

    def testRegradingNonexistentProblem(self):
        """confirm that a non-existent problem will not submit"""
        problem_url_name = 'NonexistentProblem'
        with self.assertRaises(ItemNotFoundError):
            self.regrade_all_student_answers('instructor', problem_url_name)

    def testRegradingCodeProblem(self):
        '''Run regrade scenario on problem with code submission'''
        problem_url_name = 'H1P2'
        self.define_code_response_problem(problem_url_name)
        # we fully create the CodeResponse problem, but just pretend that we're queuing it:
        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_send_to_queue:
            mock_send_to_queue.return_value = (0, "Successfully queued")
            self.submit_student_answer('u1', problem_url_name, ["answer1", "answer2"])

        course_task_log = self.regrade_all_student_answers('instructor', problem_url_name)
        self.assertEqual(course_task_log.task_state, 'FAILURE')
        status = json.loads(course_task_log.task_progress)
        self.assertEqual(status['exception'], 'NotImplementedError')
        self.assertEqual(status['message'], "Problem's definition does not support regrading")

        mock_request = Mock()
        response = course_task_log_status(mock_request, task_id=course_task_log.task_id)
        status = json.loads(response.content)
        self.assertEqual(status['message'], "Problem's definition does not support regrading")
