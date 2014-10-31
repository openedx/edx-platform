"""
Base test classes for LMS instructor-initiated background tasks

"""
import json
from uuid import uuid4
from mock import Mock

from celery.states import SUCCESS, FAILURE

from django.test.testcases import TestCase
from django.contrib.auth.models import User
from django.test.utils import override_settings

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey

from student.tests.factories import CourseEnrollmentFactory, UserFactory
from courseware.model_data import StudentModule
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_MONGO_MODULESTORE

from instructor_task.api_helper import encode_problem_and_student_input
from instructor_task.models import PROGRESS, QUEUING
from instructor_task.tests.factories import InstructorTaskFactory
from instructor_task.views import instructor_task_status


TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'test_course'
TEST_COURSE_NUMBER = '1.23x'
TEST_COURSE_KEY = SlashSeparatedCourseKey(TEST_COURSE_ORG, TEST_COURSE_NUMBER, TEST_COURSE_NAME)
TEST_SECTION_NAME = "Problem"

TEST_FAILURE_MESSAGE = 'task failed horribly'
TEST_FAILURE_EXCEPTION = 'RandomCauseError'

OPTION_1 = 'Option 1'
OPTION_2 = 'Option 2'


class InstructorTaskTestCase(TestCase):
    """
    Tests API and view methods that involve the reporting of status for background tasks.
    """
    def setUp(self):
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")
        self.problem_url = InstructorTaskTestCase.problem_location("test_urlname")

    @staticmethod
    def problem_location(problem_url_name):
        """
        Create an internal location for a test problem.
        """
        return TEST_COURSE_KEY.make_usage_key('problem', problem_url_name)

    def _create_entry(self, task_state=QUEUING, task_output=None, student=None):
        """Creates a InstructorTask entry for testing."""
        task_id = str(uuid4())
        progress_json = json.dumps(task_output) if task_output is not None else None
        task_input, task_key = encode_problem_and_student_input(self.problem_url, student)

        instructor_task = InstructorTaskFactory.create(course_id=TEST_COURSE_KEY,
                                                       requester=self.instructor,
                                                       task_input=json.dumps(task_input),
                                                       task_key=task_key,
                                                       task_id=task_id,
                                                       task_state=task_state,
                                                       task_output=progress_json)
        return instructor_task

    def _create_failure_entry(self):
        """Creates a InstructorTask entry representing a failed task."""
        # view task entry for task failure
        progress = {'message': TEST_FAILURE_MESSAGE,
                    'exception': TEST_FAILURE_EXCEPTION,
                    }
        return self._create_entry(task_state=FAILURE, task_output=progress)

    def _create_success_entry(self, student=None):
        """Creates a InstructorTask entry representing a successful task."""
        return self._create_progress_entry(student, task_state=SUCCESS)

    def _create_progress_entry(self, student=None, task_state=PROGRESS):
        """Creates a InstructorTask entry representing a task in progress."""
        progress = {'attempted': 3,
                    'succeeded': 2,
                    'total': 5,
                    'action_name': 'rescored',
                    }
        return self._create_entry(task_state=task_state, task_output=progress, student=student)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class InstructorTaskCourseTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Base test class for InstructorTask-related tests that require
    the setup of a course.
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
                                                  category='sequential',
                                                  metadata={'graded': True, 'format': 'Homework'},
                                                  display_name=TEST_SECTION_NAME)

    @staticmethod
    def get_user_email(username):
        """Generate email address based on username"""
        return '{0}@test.com'.format(username)

    def login_username(self, username):
        """Login the user, given the `username`."""
        if self.current_user != username:
            self.login(InstructorTaskCourseTestCase.get_user_email(username), "test")
            self.current_user = username

    def _create_user(self, username, is_staff=False):
        """Creates a user and enrolls them in the test course."""
        email = InstructorTaskCourseTestCase.get_user_email(username)
        thisuser = UserFactory.create(username=username, email=email, is_staff=is_staff)
        CourseEnrollmentFactory.create(user=thisuser, course_id=self.course.id)
        return thisuser

    def create_instructor(self, username):
        """Creates an instructor for the test course."""
        return self._create_user(username, is_staff=True)

    def create_student(self, username):
        """Creates a student for the test course."""
        return self._create_user(username, is_staff=False)

    @staticmethod
    def get_task_status(task_id):
        """Use api method to fetch task status, using mock request."""
        mock_request = Mock()
        mock_request.REQUEST = {'task_id': task_id}
        response = instructor_task_status(mock_request)
        status = json.loads(response.content)
        return status

    def create_task_request(self, requester_username):
        """Generate request that can be used for submitting tasks"""
        request = Mock()
        request.user = User.objects.get(username=requester_username)
        request.get_host = Mock(return_value="testhost")
        request.META = {'REMOTE_ADDR': '0:0:0:0', 'SERVER_NAME': 'testhost'}
        request.is_secure = Mock(return_value=False)
        return request


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class InstructorTaskModuleTestCase(InstructorTaskCourseTestCase):
    """
    Base test class for InstructorTask-related tests that require
    the setup of a course and problem in order to access StudentModule state.
    """
    @staticmethod
    def problem_location(problem_url_name):
        """
        Create an internal location for a test problem.
        """
        if "i4x:" in problem_url_name:
            return Location.from_deprecated_string(problem_url_name)
        else:
            return TEST_COURSE_KEY.make_usage_key('problem', problem_url_name)

    def define_option_problem(self, problem_url_name):
        """Create the problem definition so the answer is Option 1"""
        factory = OptionResponseXMLFactory()
        factory_args = {'question_text': 'The correct answer is {0}'.format(OPTION_1),
                        'options': [OPTION_1, OPTION_2],
                        'correct_option': OPTION_1,
                        'num_responses': 2}
        problem_xml = factory.build_xml(**factory_args)
        ItemFactory.create(parent_location=self.problem_section.location,
                           parent=self.problem_section,
                           category="problem",
                           display_name=str(problem_url_name),
                           data=problem_xml)

    def redefine_option_problem(self, problem_url_name):
        """Change the problem definition so the answer is Option 2"""
        factory = OptionResponseXMLFactory()
        factory_args = {'question_text': 'The correct answer is {0}'.format(OPTION_2),
                        'options': [OPTION_1, OPTION_2],
                        'correct_option': OPTION_2,
                        'num_responses': 2}
        problem_xml = factory.build_xml(**factory_args)
        location = InstructorTaskTestCase.problem_location(problem_url_name)
        item = self.module_store.get_item(location)
        with self.module_store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, location.course_key):
            item.data = problem_xml
            self.module_store.update_item(item, self.user.id)
            self.module_store.publish(location, self.user.id)

    def get_student_module(self, username, descriptor):
        """Get StudentModule object for test course, given the `username` and the problem's `descriptor`."""
        return StudentModule.objects.get(course_id=self.course.id,
                                         student=User.objects.get(username=username),
                                         module_type=descriptor.location.category,
                                         module_state_key=descriptor.location,
                                         )
