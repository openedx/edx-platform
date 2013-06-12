"""
Integration Test for LMS instructor-initiated background tasks

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
import logging
import json
from mock import Mock

from django.contrib.auth.models import User
from django.test.utils import override_settings

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from student.tests.factories import CourseEnrollmentFactory, UserFactory, AdminFactory
from courseware.model_data import StudentModule
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_MONGO_MODULESTORE

from instructor_task.views import instructor_task_status


log = logging.getLogger(__name__)


TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_COURSE_NUMBER = '1.23x'
TEST_SECTION_NAME = "Problem"


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class InstructorTaskTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
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
        self.login(InstructorTaskTestCase.get_user_email(username), "test")
        self.current_user = username

    def _create_user(self, username, is_staff=False):
        """Creates a user and enrolls them in the test course."""
        email = InstructorTaskTestCase.get_user_email(username)
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
        location = InstructorTaskTestCase.problem_location(problem_url_name)
        self.module_store.update_item(location, problem_xml)

    def get_student_module(self, username, descriptor):
        """Get StudentModule object for test course, given the `username` and the problem's `descriptor`."""
        return StudentModule.objects.get(course_id=self.course.id,
                                         student=User.objects.get(username=username),
                                         module_type=descriptor.location.category,
                                         module_state_key=descriptor.location.url(),
                                         )

    def get_task_status(self, task_id):
        """Use api method to fetch task status, using mock request."""
        mock_request = Mock()
        mock_request.REQUEST = {'task_id': task_id}
        response = instructor_task_status(mock_request)
        status = json.loads(response.content)
        return status
