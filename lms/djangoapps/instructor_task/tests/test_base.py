"""
Base test classes for LMS instructor-initiated background tasks

"""
import os
import json
from mock import Mock
import shutil
import unicodecsv
from uuid import uuid4

from celery.states import SUCCESS, FAILURE
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
from django.contrib.auth.models import User
from lms.djangoapps.lms_xblock.runtime import quote_slashes
from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from courseware.model_data import StudentModule
from courseware.tests.tests import LoginEnrollmentTestCase
from openedx.core.djangoapps.content.course_structures.signals import listen_for_course_publish
from openedx.core.djangoapps.util.testing import SignalDisconnectTestMixin
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from instructor_task.api_helper import encode_problem_and_student_input
from instructor_task.models import PROGRESS, QUEUING, ReportStore
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
        super(InstructorTaskTestCase, self).setUp()

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


class InstructorTaskCourseTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Base test class for InstructorTask-related tests that require
    the setup of a course.
    """
    course = None
    current_user = None

    def setUp(self):
        super(InstructorTaskCourseTestCase, self).setUp()
        SignalHandler.course_published.connect(listen_for_course_publish)
        self.addCleanup(SignalDisconnectTestMixin.disconnect_course_published_signals)

    def initialize_course(self, course_factory_kwargs=None):
        """
        Create a course in the store, with a chapter and section.

        Arguments:
            course_factory_kwargs (dict): kwargs dict to pass to
            CourseFactory.create()
        """
        self.module_store = modulestore()

        # Create the course
        course_args = {
            "org": TEST_COURSE_ORG,
            "number": TEST_COURSE_NUMBER,
            "display_name": TEST_COURSE_NAME
        }
        if course_factory_kwargs is not None:
            course_args.update(course_factory_kwargs)
        self.course = CourseFactory.create(**course_args)
        self.add_course_content()

    def add_course_content(self):
        """
        Add a chapter and a sequential to the current course.
        """
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
        return u'{0}@test.com'.format(username)

    def login_username(self, username):
        """Login the user, given the `username`."""
        if self.current_user != username:
            self.logout()
            user_email = User.objects.get(username=username).email
            self.login(user_email, "test")
            self.current_user = username

    def _create_user(self, username, email=None, is_staff=False, mode='honor'):
        """Creates a user and enrolls them in the test course."""
        if email is None:
            email = InstructorTaskCourseTestCase.get_user_email(username)
        thisuser = UserFactory.create(username=username, email=email, is_staff=is_staff)
        CourseEnrollmentFactory.create(user=thisuser, course_id=self.course.id, mode=mode)
        return thisuser

    def create_instructor(self, username, email=None):
        """Creates an instructor for the test course."""
        return self._create_user(username, email, is_staff=True)

    def create_student(self, username, email=None, mode='honor'):
        """Creates a student for the test course."""
        return self._create_user(username, email, is_staff=False, mode=mode)

    @staticmethod
    def get_task_status(task_id):
        """Use api method to fetch task status, using mock request."""
        mock_request = Mock()
        mock_request.GET = mock_request.POST = {'task_id': task_id}
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


class InstructorTaskModuleTestCase(InstructorTaskCourseTestCase):
    """
    Base test class for InstructorTask-related tests that require
    the setup of a course and problem in order to access StudentModule state.
    """
    @staticmethod
    def problem_location(problem_url_name, course_key=None):
        """
        Create an internal location for a test problem.
        """
        if "i4x:" in problem_url_name:
            return Location.from_deprecated_string(problem_url_name)
        elif course_key:
            return course_key.make_usage_key('problem', problem_url_name)
        else:
            return TEST_COURSE_KEY.make_usage_key('problem', problem_url_name)

    def define_option_problem(self, problem_url_name, parent=None, **kwargs):
        """Create the problem definition so the answer is Option 1"""
        if parent is None:
            parent = self.problem_section
        factory = OptionResponseXMLFactory()
        factory_args = {'question_text': 'The correct answer is {0}'.format(OPTION_1),
                        'options': [OPTION_1, OPTION_2],
                        'correct_option': OPTION_1,
                        'num_responses': 2}
        problem_xml = factory.build_xml(**factory_args)
        ItemFactory.create(parent_location=parent.location,
                           parent=parent,
                           category="problem",
                           display_name=problem_url_name,
                           data=problem_xml,
                           **kwargs)

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
            course_key = self.course.id
            return u'input_i4x-{0}-{1}-problem-{2}_{3}'.format(
                course_key.org.replace(u'.', u'_'),
                course_key.course.replace(u'.', u'_'),
                problem_url_name,
                response_id
            )

        # make sure that the requested user is logged in, so that the ajax call works
        # on the right problem:
        self.login_username(username)
        # make ajax call:
        modx_url = reverse('xblock_handler', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'usage_id': quote_slashes(
                InstructorTaskModuleTestCase.problem_location(problem_url_name, self.course.id).to_deprecated_string()
            ),
            'handler': 'xmodule_handler',
            'suffix': 'problem_check',
        })

        # assign correct identifier to each response.
        resp = self.client.post(modx_url, {
            get_input_id(u'{}_1').format(index): response for index, response in enumerate(responses, 2)
        })
        return resp


class TestReportMixin(object):
    """
    Cleans up after tests that place files in the reports directory.
    """
    def tearDown(self):
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        try:
            reports_download_path = report_store.storage.path('')
        except NotImplementedError:
            pass  # storage backend does not use the local filesystem
        else:
            if os.path.exists(reports_download_path):
                shutil.rmtree(reports_download_path)

    def verify_rows_in_csv(self, expected_rows, file_index=0, verify_order=True, ignore_other_columns=False):
        """
        Verify that the last ReportStore CSV contains the expected content.

        Arguments:
            expected_rows (iterable): An iterable of dictionaries,
                where each dict represents a row of data in the last
                ReportStore CSV.  Each dict maps keys from the CSV
                header to values in that row's corresponding cell.
            file_index (int): Describes which report store file to
                open.  Files are ordered by last modified date, and 0
                corresponds to the most recently modified file.
            verify_order (boolean): When True, we verify that both the
                content and order of `expected_rows` matches the
                actual csv rows.  When False (default), we only verify
                that the content matches.
            ignore_other_columns (boolean): When True, we verify that `expected_rows`
                contain data which is the subset of actual csv rows.
        """
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        report_csv_filename = report_store.links_for(self.course.id)[file_index][0]
        report_path = report_store.path_to(self.course.id, report_csv_filename)
        with report_store.storage.open(report_path) as csv_file:
            # Expand the dict reader generator so we don't lose it's content
            csv_rows = [row for row in unicodecsv.DictReader(csv_file)]

            if ignore_other_columns:
                csv_rows = [
                    {key: row.get(key) for key in expected_rows[index].keys()} for index, row in enumerate(csv_rows)
                ]

            if verify_order:
                self.assertEqual(csv_rows, expected_rows)
            else:
                self.assertItemsEqual(csv_rows, expected_rows)

    def get_csv_row_with_headers(self):
        """
        Helper function to return list with the column names from the CSV file (the first row)
        """
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        report_csv_filename = report_store.links_for(self.course.id)[0][0]
        report_path = report_store.path_to(self.course.id, report_csv_filename)
        with report_store.storage.open(report_path) as csv_file:
            rows = unicodecsv.reader(csv_file, encoding='utf-8')
            return rows.next()
