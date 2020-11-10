# -*- coding: utf-8 -*-
"""
Unit tests for instructor.api methods.
"""


import datetime
import functools
import io
import json
import random
import shutil
import tempfile

import ddt
import pytest
import six
from boto.exception import BotoServerError
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse as django_reverse
from django.utils.translation import ugettext as _
from edx_when.api import get_dates_for_course, get_overrides_for_user, set_date_for_block
from mock import Mock, NonCallableMock, patch
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import UsageKey
from pytz import UTC
from six import text_type, unichr
from six.moves import range, zip
from testfixtures import LogCapture

from lms.djangoapps.bulk_email.models import BulkEmailFlag, CourseEmail, CourseEmailTemplate
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.certificates.api import generate_user_certificates
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.courseware.tests.factories import (
    BetaTesterFactory,
    GlobalStaffFactory,
    InstructorFactory,
    StaffFactory,
    UserProfileFactory
)
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from lms.djangoapps.instructor.tests.utils import FakeContentTask, FakeEmail, FakeEmailInfo
from lms.djangoapps.instructor.views.api import (
    _split_input_list,
    common_exceptions_400,
    generate_unique_password,
    require_finance_admin
)
from lms.djangoapps.instructor_task.api_helper import (
    AlreadyRunningError,
    QueueConnectionError,
    generate_already_running_error_message
)
from openedx.core.djangoapps.course_date_signals.handlers import extract_dates
from openedx.core.djangoapps.course_groups.cohorts import set_course_cohorted
from openedx.core.djangoapps.django_comment_common.models import FORUM_ROLE_COMMUNITY_TA
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.lib.teams_config import TeamsConfig
from openedx.core.lib.xblock_utils import grade_histogram
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from common.djangoapps.student.models import (
    ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED,
    ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL,
    UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED,
    CourseEnrollment,
    CourseEnrollmentAllowed,
    ManualEnrollmentAudit,
    NonExistentCourseError,
    get_retired_email_by_email,
    get_retired_username_by_username
)
from common.djangoapps.student.roles import (
    CourseBetaTesterRole,
    CourseDataResearcherRole,
    CourseFinanceAdminRole,
    CourseInstructorRole,
    CourseSalesAdminRole
)
from common.djangoapps.student.tests.factories import AdminFactory, UserFactory
from xmodule.fields import Date
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .test_tools import msk_from_problem_urlname

DATE_FIELD = Date()
EXPECTED_CSV_HEADER = (
    '"code","redeem_code_url","course_id","company_name","created_by","redeemed_by","invoice_id","purchaser",'
    '"customer_reference_number","internal_reference"'
)

# ddt data for test cases involving reports
REPORTS_DATA = (
    {
        'report_type': 'grade',
        'instructor_api_endpoint': 'calculate_grades_csv',
        'task_api_endpoint': 'lms.djangoapps.instructor_task.api.submit_calculate_grades_csv',
        'extra_instructor_api_kwargs': {}
    },
    {
        'report_type': 'enrolled learner profile',
        'instructor_api_endpoint': 'get_students_features',
        'task_api_endpoint': 'lms.djangoapps.instructor_task.api.submit_calculate_students_features_csv',
        'extra_instructor_api_kwargs': {'csv': '/csv'}
    },
    {
        'report_type': 'enrollment',
        'instructor_api_endpoint': 'get_students_who_may_enroll',
        'task_api_endpoint': 'lms.djangoapps.instructor_task.api.submit_calculate_may_enroll_csv',
        'extra_instructor_api_kwargs': {},
    },
    {
        'report_type': 'proctored exam results',
        'instructor_api_endpoint': 'get_proctored_exam_results',
        'task_api_endpoint': 'lms.djangoapps.instructor_task.api.submit_proctored_exam_results_report',
        'extra_instructor_api_kwargs': {},
    },
    {
        'report_type': 'problem responses',
        'instructor_api_endpoint': 'get_problem_responses',
        'task_api_endpoint': 'lms.djangoapps.instructor_task.api.submit_calculate_problem_responses_csv',
        'extra_instructor_api_kwargs': {},
    }
)


INSTRUCTOR_GET_ENDPOINTS = set([
    'get_anon_ids',
    'get_issued_certificates',
])
INSTRUCTOR_POST_ENDPOINTS = set([
    'add_users_to_cohorts',
    'bulk_beta_modify_access',
    'calculate_grades_csv',
    'change_due_date',
    'export_ora2_data',
    'export_ora2_submission_files',
    'get_grading_config',
    'get_problem_responses',
    'get_proctored_exam_results',
    'get_student_enrollment_status',
    'get_student_progress_url',
    'get_students_features',
    'get_students_who_may_enroll',
    'list_background_email_tasks',
    'list_course_role_members',
    'list_email_content',
    'list_entrance_exam_instructor_tasks',
    'list_forum_members',
    'list_instructor_tasks',
    'list_report_downloads',
    'mark_student_can_skip_entrance_exam',
    'modify_access',
    'register_and_enroll_students',
    'rescore_entrance_exam',
    'rescore_problem',
    'reset_due_date',
    'reset_student_attempts',
    'reset_student_attempts_for_entrance_exam',
    'show_student_extensions',
    'show_unit_extensions',
    'send_email',
    'students_update_enrollment',
    'update_forum_role_membership',
    'override_problem_score',
])


def reverse(endpoint, args=None, kwargs=None, is_dashboard_endpoint=True):
    """
    Simple wrapper of Django's reverse that first ensures that we have declared
    each endpoint under test.

    Arguments:
        args: The args to be passed through to reverse.
        endpoint: The endpoint to be passed through to reverse.
        kwargs: The kwargs to be passed through to reverse.
        is_dashboard_endpoint: True if this is an instructor dashboard endpoint
            that must be declared in the INSTRUCTOR_GET_ENDPOINTS or
            INSTRUCTOR_GET_ENDPOINTS sets, or false otherwise.

    Returns:
        The return of Django's reverse function

    """
    is_endpoint_declared = endpoint in INSTRUCTOR_GET_ENDPOINTS or endpoint in INSTRUCTOR_POST_ENDPOINTS
    if is_dashboard_endpoint and is_endpoint_declared is False:
        # Verify that all endpoints are declared so we can ensure they are
        # properly validated elsewhere.
        raise ValueError(u"The endpoint {} must be declared in ENDPOINTS before use.".format(endpoint))
    return django_reverse(endpoint, args=args, kwargs=kwargs)


@common_exceptions_400
def view_success(request):
    "A dummy view for testing that returns a simple HTTP response"
    return HttpResponse('success')


@common_exceptions_400
def view_user_doesnotexist(request):
    "A dummy view that raises a User.DoesNotExist exception"
    raise User.DoesNotExist()


@common_exceptions_400
def view_alreadyrunningerror(request):
    "A dummy view that raises an AlreadyRunningError exception"
    raise AlreadyRunningError()


@common_exceptions_400
def view_alreadyrunningerror_unicode(request):
    """
    A dummy view that raises an AlreadyRunningError exception with unicode message
    """
    raise AlreadyRunningError(u'Text with unicode chárácters')


@common_exceptions_400
def view_queue_connection_error(request):
    """
    A dummy view that raises a QueueConnectionError exception.
    """
    raise QueueConnectionError()


@ddt.ddt
class TestCommonExceptions400(TestCase):
    """
    Testing the common_exceptions_400 decorator.
    """

    def setUp(self):
        super(TestCommonExceptions400, self).setUp()
        self.request = Mock(spec=HttpRequest)
        self.request.META = {}

    def test_happy_path(self):
        resp = view_success(self.request)
        self.assertEqual(resp.status_code, 200)

    def test_user_doesnotexist(self):
        self.request.is_ajax.return_value = False
        resp = view_user_doesnotexist(self.request)
        self.assertContains(resp, "User does not exist", status_code=400)

    def test_user_doesnotexist_ajax(self):
        self.request.is_ajax.return_value = True
        resp = view_user_doesnotexist(self.request)
        self.assertContains(resp, "User does not exist", status_code=400)

    @ddt.data(True, False)
    def test_alreadyrunningerror(self, is_ajax):
        self.request.is_ajax.return_value = is_ajax
        resp = view_alreadyrunningerror(self.request)
        self.assertContains(resp, "Requested task is already running", status_code=400)

    @ddt.data(True, False)
    def test_alreadyrunningerror_with_unicode(self, is_ajax):
        self.request.is_ajax.return_value = is_ajax
        resp = view_alreadyrunningerror_unicode(self.request)
        self.assertContains(
            resp,
            u'Text with unicode chárácters',
            status_code=400,
        )

    @ddt.data(True, False)
    def test_queue_connection_error(self, is_ajax):
        """
        Tests that QueueConnectionError exception is handled in common_exception_400.
        """
        self.request.is_ajax.return_value = is_ajax
        resp = view_queue_connection_error(self.request)
        self.assertContains(
            resp,
            'Error occured. Please try again later',
            status_code=400,
        )


@ddt.ddt
class TestEndpointHttpMethods(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Ensure that users can make GET requests against endpoints that allow GET,
    and not against those that don't allow GET.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up test course.
        """
        super(TestEndpointHttpMethods, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """
        Set up global staff role so authorization will not fail.
        """
        super(TestEndpointHttpMethods, self).setUp()
        global_user = GlobalStaffFactory()
        self.client.login(username=global_user.username, password='test')

    @ddt.data(*INSTRUCTOR_POST_ENDPOINTS)
    def test_endpoints_reject_get(self, data):
        """
        Tests that POST endpoints are rejected with 405 when using GET.
        """
        url = reverse(data, kwargs={'course_id': text_type(self.course.id)})
        response = self.client.get(url)

        self.assertEqual(
            response.status_code, 405,
            u"Endpoint {} returned status code {} instead of a 405. It should not allow GET.".format(
                data, response.status_code
            )
        )

    @ddt.data(*INSTRUCTOR_GET_ENDPOINTS)
    def test_endpoints_accept_get(self, data):
        """
        Tests that GET endpoints are not rejected with 405 when using GET.
        """
        url = reverse(data, kwargs={'course_id': text_type(self.course.id)})
        response = self.client.get(url)

        self.assertNotEqual(
            response.status_code, 405,
            u"Endpoint {} returned status code 405 where it shouldn't, since it should allow GET.".format(
                data
            )
        )


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestInstructorAPIDenyLevels(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Ensure that users cannot access endpoints they shouldn't be able to.
    """

    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIDenyLevels, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(
            parent=cls.course,
            category='chapter',
            display_name="Chapter",
            publish_item=True,
            start=datetime.datetime(2018, 3, 10, tzinfo=UTC),
        )
        cls.sequential = ItemFactory.create(
            parent=cls.chapter,
            category='sequential',
            display_name="Lesson",
            publish_item=True,
            start=datetime.datetime(2018, 3, 10, tzinfo=UTC),
            metadata={'graded': True, 'format': 'Homework'},
        )
        cls.vertical = ItemFactory.create(
            parent=cls.sequential,
            category='vertical',
            display_name='Subsection',
            publish_item=True,
            start=datetime.datetime(2018, 3, 10, tzinfo=UTC),
        )
        cls.problem = ItemFactory.create(
            category="problem",
            parent=cls.vertical,
            display_name="A Problem Block",
            weight=1,
            publish_item=True,
        )

        cls.problem_urlname = text_type(cls.problem.location)
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    @classmethod
    def tearDownClass(cls):
        super(TestInstructorAPIDenyLevels, cls).tearDownClass()
        BulkEmailFlag.objects.all().delete()

    def setUp(self):
        super(TestInstructorAPIDenyLevels, self).setUp()
        self.user = UserFactory.create()
        CourseEnrollment.enroll(self.user, self.course.id)

        _module = StudentModule.objects.create(
            student=self.user,
            course_id=self.course.id,
            module_state_key=self.problem.location,
            state=json.dumps({'attempts': 10}),
        )

        # Endpoints that only Staff or Instructors can access
        self.staff_level_endpoints = [
            ('students_update_enrollment',
             {'identifiers': 'foo@example.org', 'action': 'enroll'}),
            ('get_grading_config', {}),
            ('get_students_features', {}),
            ('get_student_progress_url', {'unique_student_identifier': self.user.username}),
            ('update_forum_role_membership',
             {'unique_student_identifier': self.user.email, 'rolename': 'Moderator', 'action': 'allow'}),
            ('list_forum_members', {'rolename': FORUM_ROLE_COMMUNITY_TA}),
            ('send_email', {'send_to': '["staff"]', 'subject': 'test', 'message': 'asdf'}),
            ('list_instructor_tasks', {}),
            ('list_background_email_tasks', {}),
            ('list_report_downloads', {}),
            ('calculate_grades_csv', {}),
            ('get_students_features', {}),
            ('get_students_who_may_enroll', {}),
            ('get_proctored_exam_results', {}),
            ('get_problem_responses', {}),
            ('export_ora2_data', {}),
            ('export_ora2_submission_files', {}),
            ('rescore_problem',
             {'problem_to_reset': self.problem_urlname, 'unique_student_identifier': self.user.email}),
            ('override_problem_score',
             {'problem_to_reset': self.problem_urlname, 'unique_student_identifier': self.user.email, 'score': 0}),
            ('reset_student_attempts',
             {'problem_to_reset': self.problem_urlname, 'unique_student_identifier': self.user.email}),
            (
                'reset_student_attempts',
                {
                    'problem_to_reset': self.problem_urlname,
                    'unique_student_identifier': self.user.email,
                    'delete_module': True
                }
            ),
        ]
        # Endpoints that only Instructors can access
        self.instructor_level_endpoints = [
            ('bulk_beta_modify_access', {'identifiers': 'foo@example.org', 'action': 'add'}),
            ('modify_access', {'unique_student_identifier': self.user.email, 'rolename': 'beta', 'action': 'allow'}),
            ('list_course_role_members', {'rolename': 'beta'}),
            ('rescore_problem', {'problem_to_reset': self.problem_urlname, 'all_students': True}),
            ('reset_student_attempts', {'problem_to_reset': self.problem_urlname, 'all_students': True}),
        ]

    def _access_endpoint(self, endpoint, args, status_code, msg):
        """
        Asserts that accessing the given `endpoint` gets a response of `status_code`.

        endpoint: string, endpoint for instructor dash API
        args: dict, kwargs for `reverse` call
        status_code: expected HTTP status code response
        msg: message to display if assertion fails.
        """
        url = reverse(endpoint, kwargs={'course_id': text_type(self.course.id)})
        if endpoint in INSTRUCTOR_GET_ENDPOINTS:
            response = self.client.get(url, args)
        else:
            response = self.client.post(url, args)
        self.assertEqual(
            response.status_code,
            status_code,
            msg=msg
        )

    def test_student_level(self):
        """
        Ensure that an enrolled student can't access staff or instructor endpoints.
        """
        self.client.login(username=self.user.username, password='test')

        for endpoint, args in self.staff_level_endpoints:
            self._access_endpoint(
                endpoint,
                args,
                403,
                "Student should not be allowed to access endpoint " + endpoint
            )

        for endpoint, args in self.instructor_level_endpoints:
            self._access_endpoint(
                endpoint,
                args,
                403,
                "Student should not be allowed to access endpoint " + endpoint
            )

    def _access_problem_responses_endpoint(self, msg):
        """
        Access endpoint for problem responses report, ensuring that
        UsageKey.from_string returns a problem key that the endpoint
        can work with.

        msg: message to display if assertion fails.
        """
        mock_problem_key = NonCallableMock(return_value=u'')
        mock_problem_key.course_key = self.course.id
        with patch.object(UsageKey, 'from_string') as patched_method:
            patched_method.return_value = mock_problem_key
            self._access_endpoint('get_problem_responses', {}, 200, msg)

    def test_staff_level(self):
        """
        Ensure that a staff member can't access instructor endpoints.
        """
        staff_member = StaffFactory(course_key=self.course.id)
        CourseEnrollment.enroll(staff_member, self.course.id)
        CourseFinanceAdminRole(self.course.id).add_users(staff_member)
        CourseDataResearcherRole(self.course.id).add_users(staff_member)
        self.client.login(username=staff_member.username, password='test')
        # Try to promote to forums admin - not working
        # update_forum_role(self.course.id, staff_member, FORUM_ROLE_ADMINISTRATOR, 'allow')

        for endpoint, args in self.staff_level_endpoints:
            expected_status = 200

            # TODO: make these work
            if endpoint in ['update_forum_role_membership', 'list_forum_members']:
                continue
            elif endpoint == 'get_problem_responses':
                self._access_problem_responses_endpoint(
                    "Staff member should be allowed to access endpoint " + endpoint
                )
                continue
            self._access_endpoint(
                endpoint,
                args,
                expected_status,
                "Staff member should be allowed to access endpoint " + endpoint
            )

        for endpoint, args in self.instructor_level_endpoints:
            self._access_endpoint(
                endpoint,
                args,
                403,
                "Staff member should not be allowed to access endpoint " + endpoint
            )

    def test_instructor_level(self):
        """
        Ensure that an instructor member can access all endpoints.
        """
        inst = InstructorFactory(course_key=self.course.id)
        CourseEnrollment.enroll(inst, self.course.id)

        CourseFinanceAdminRole(self.course.id).add_users(inst)
        CourseDataResearcherRole(self.course.id).add_users(inst)
        self.client.login(username=inst.username, password='test')

        for endpoint, args in self.staff_level_endpoints:
            expected_status = 200

            # TODO: make these work
            if endpoint in ['update_forum_role_membership']:
                continue
            elif endpoint == 'get_problem_responses':
                self._access_problem_responses_endpoint(
                    "Instructor should be allowed to access endpoint " + endpoint
                )
                continue
            self._access_endpoint(
                endpoint,
                args,
                expected_status,
                "Instructor should be allowed to access endpoint " + endpoint
            )

        for endpoint, args in self.instructor_level_endpoints:
            expected_status = 200
            self._access_endpoint(
                endpoint,
                args,
                expected_status,
                "Instructor should be allowed to access endpoint " + endpoint
            )


@patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': True})
class TestInstructorAPIBulkAccountCreationAndEnrollment(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test Bulk account creation and enrollment from csv file
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIBulkAccountCreationAndEnrollment, cls).setUpClass()
        cls.course = CourseFactory.create()

        # Create a course with mode 'audit'
        cls.audit_course = CourseFactory.create()
        CourseModeFactory.create(course_id=cls.audit_course.id, mode_slug=CourseMode.AUDIT)

        cls.url = reverse(
            'register_and_enroll_students', kwargs={'course_id': text_type(cls.course.id)}
        )
        cls.audit_course_url = reverse(
            'register_and_enroll_students', kwargs={'course_id': text_type(cls.audit_course.id)}
        )

    def setUp(self):
        super(TestInstructorAPIBulkAccountCreationAndEnrollment, self).setUp()

        # Create a course with mode 'honor' and with price
        self.white_label_course = CourseFactory.create()
        self.white_label_course_mode = CourseModeFactory.create(
            course_id=self.white_label_course.id,
            mode_slug=CourseMode.HONOR,
            min_price=10,
            suggested_prices='10',
        )

        self.white_label_course_url = reverse(
            'register_and_enroll_students', kwargs={'course_id': text_type(self.white_label_course.id)}
        )

        self.request = RequestFactory().request()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.audit_course_instructor = InstructorFactory(course_key=self.audit_course.id)
        self.white_label_course_instructor = InstructorFactory(course_key=self.white_label_course.id)

        self.client.login(username=self.instructor.username, password='test')

        self.not_enrolled_student = UserFactory(
            username='NotEnrolledStudent',
            email='nonenrolled@test.com',
            first_name='NotEnrolled',
            last_name='Student'
        )

    @patch('lms.djangoapps.instructor.views.api.log.info')
    def test_account_creation_and_enrollment_with_csv(self, info_log):
        """
        Happy path test to create a single new user
        """
        csv_content = b"test_student@example.com,test_student_1,tester1,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # test the log for email that's send to new created user.
        info_log.assert_called_with(u'email sent to new created user at %s', 'test_student@example.com')

    @patch('lms.djangoapps.instructor.views.api.log.info')
    def test_account_creation_and_enrollment_with_csv_with_blank_lines(self, info_log):
        """
        Happy path test to create a single new user
        """
        csv_content = b"\ntest_student@example.com,test_student_1,tester1,USA\n\n"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # test the log for email that's send to new created user.
        info_log.assert_called_with(u'email sent to new created user at %s', 'test_student@example.com')

    @patch('lms.djangoapps.instructor.views.api.log.info')
    def test_email_and_username_already_exist(self, info_log):
        """
        If the email address and username already exists
        and the user is enrolled in the course, do nothing (including no email gets sent out)
        """
        csv_content = b"test_student@example.com,test_student_1,tester1,USA\n" \
                      b"test_student@example.com,test_student_1,tester2,US"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # test the log for email that's send to new created user.
        info_log.assert_called_with(
            u"user already exists with username '%s' and email '%s'",
            'test_student_1',
            'test_student@example.com'
        )

    def test_file_upload_type_not_csv(self):
        """
        Try uploading some non-CSV file and verify that it is rejected
        """
        uploaded_file = SimpleUploadedFile("temp.jpg", io.BytesIO(b"some initial binary data: \x00\x01").read())
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['general_errors']), 0)
        self.assertEqual(
            data['general_errors'][0]['response'],
            'Make sure that the file you upload is in CSV format with no extraneous characters or rows.'
        )

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_bad_file_upload_type(self):
        """
        Try uploading some non-CSV file and verify that it is rejected
        """
        uploaded_file = SimpleUploadedFile("temp.csv", io.BytesIO(b"some initial binary data: \x00\x01").read())
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['general_errors']), 0)
        self.assertEqual(data['general_errors'][0]['response'], 'Could not read uploaded file.')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_insufficient_data(self):
        """
        Try uploading a CSV file which does not have the exact four columns of data
        """
        csv_content = b"test_student@example.com,test_student_1\n"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 1)
        self.assertEqual(data['general_errors'][0]['response'], 'Data in row #1 must have exactly four columns: email, username, full name, and country')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_invalid_email_in_csv(self):
        """
        Test failure case of a poorly formatted email field
        """
        csv_content = b"test_student.example.com,test_student_1,tester1,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 0)
        self.assertEqual(data['row_errors'][0]['response'], u'Invalid email {0}.'.format('test_student.example.com'))

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    @patch('lms.djangoapps.instructor.views.api.log.info')
    def test_csv_user_exist_and_not_enrolled(self, info_log):
        """
        If the email address and username already exists
        and the user is not enrolled in the course, enrolled him/her and iterate to next one.
        """
        csv_content = b"nonenrolled@test.com,NotEnrolledStudent,tester1,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        info_log.assert_called_with(
            u'user %s enrolled in the course %s',
            u'NotEnrolledStudent',
            self.course.id
        )
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertTrue(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

    def test_user_with_already_existing_email_in_csv(self):
        """
        If the email address already exists, but the username is different,
        assume it is the correct user and just register the user in the course.
        """
        csv_content = b"test_student@example.com,test_student_1,tester1,USA\n" \
                      b"test_student@example.com,test_student_2,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        warning_message = u'An account with email {email} exists but the provided username {username} ' \
                          u'is different. Enrolling anyway with {email}.'.format(email='test_student@example.com', username='test_student_2')
        self.assertNotEqual(len(data['warnings']), 0)
        self.assertEqual(data['warnings'][0]['response'], warning_message)
        user = User.objects.get(email='test_student@example.com')
        self.assertTrue(CourseEnrollment.is_enrolled(user, self.course.id))

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertTrue(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

    def test_user_with_retired_email_in_csv(self):
        """
        If the CSV contains email addresses which correspond with users which
        have already been retired, confirm that the attempt returns invalid
        email errors.
        """

        # This email address is re-used to create a retired account and another account.
        conflicting_email = 'test_student@example.com'

        # prep a retired user
        user = UserFactory.create(username='old_test_student', email=conflicting_email)
        user.email = get_retired_email_by_email(user.email)
        user.username = get_retired_username_by_username(user.username)
        user.is_active = False
        user.save()

        csv_content = "{email},{username},tester,USA".format(email=conflicting_email, username='new_test_student')
        uploaded_file = SimpleUploadedFile("temp.csv", six.b(csv_content))
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['row_errors']), 0)
        self.assertEqual(
            data['row_errors'][0]['response'],
            u'Invalid email {email}.'.format(email=conflicting_email)
        )
        self.assertFalse(User.objects.filter(email=conflicting_email).exists())

    def test_user_with_already_existing_username_in_csv(self):
        """
        If the username already exists (but not the email),
        assume it is a different user and fail to create the new account.
        """
        csv_content = b"test_student1@example.com,test_student_1,tester1,USA\n" \
                      b"test_student2@example.com,test_student_1,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)

        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['row_errors']), 0)
        self.assertEqual(data['row_errors'][0]['response'], u'Username {user} already exists.'.format(user='test_student_1'))

    def test_csv_file_not_attached(self):
        """
        Test when the user does not attach a file
        """
        csv_content = b"test_student1@example.com,test_student_1,tester1,USA\n" \
                      b"test_student2@example.com,test_student_1,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)

        response = self.client.post(self.url, {'file_not_found': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['general_errors']), 0)
        self.assertEqual(data['general_errors'][0]['response'], 'File is not attached.')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_raising_exception_in_auto_registration_and_enrollment_case(self):
        """
        Test that exceptions are handled well
        """
        csv_content = b"test_student1@example.com,test_student_1,tester1,USA\n" \
                      b"test_student2@example.com,test_student_1,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        with patch('lms.djangoapps.instructor.views.api.create_manual_course_enrollment') as mock:
            mock.side_effect = NonExistentCourseError()
            response = self.client.post(self.url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['row_errors']), 0)
        self.assertEqual(data['row_errors'][0]['response'], 'NonExistentCourseError')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_generate_unique_password(self):
        """
        generate_unique_password should generate a unique password string that excludes certain characters.
        """
        password = generate_unique_password([], 12)
        self.assertEqual(len(password), 12)
        for letter in password:
            self.assertNotIn(letter, 'aAeEiIoOuU1l')

    def test_users_created_and_enrolled_successfully_if_others_fail(self):

        # prep a retired user
        user = UserFactory.create(username='old_test_student_4', email='test_student4@example.com')
        user.email = get_retired_email_by_email(user.email)
        user.username = get_retired_username_by_username(user.username)
        user.is_active = False
        user.save()

        csv_content = b"test_student1@example.com,test_student_1,tester1,USA\n" \
                      b"test_student3@example.com,test_student_1,tester3,CA\n" \
                      b"test_student4@example.com,test_student_4,tester4,USA\n" \
                      b"test_student2@example.com,test_student_2,tester2,USA"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(len(data['row_errors']), 0)
        self.assertEqual(
            data['row_errors'][0]['response'],
            u'Username {user} already exists.'.format(user='test_student_1')
        )
        self.assertEqual(
            data['row_errors'][1]['response'],
            u'Invalid email {email}.'.format(email='test_student4@example.com')
        )
        self.assertTrue(User.objects.filter(username='test_student_1', email='test_student1@example.com').exists())
        self.assertTrue(User.objects.filter(username='test_student_2', email='test_student2@example.com').exists())
        self.assertFalse(User.objects.filter(email='test_student3@example.com').exists())
        self.assertFalse(User.objects.filter(email='test_student4@example.com').exists())

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 2)

    @patch('lms.djangoapps.instructor.views.api', 'generate_random_string',
           Mock(side_effect=['first', 'first', 'second']))
    def test_generate_unique_password_no_reuse(self):
        """
        generate_unique_password should generate a unique password string that hasn't been generated before.
        """
        generated_password = ['first']
        password = generate_unique_password(generated_password, 12)
        self.assertNotEqual(password, 'first')

    @patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': False})
    def test_allow_automated_signups_flag_not_set(self):
        csv_content = b"test_student1@example.com,test_student_1,tester1,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 403)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    @patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': True})
    def test_audit_enrollment_mode(self):
        """
        Test that enrollment mode for audit courses (paid courses) is 'audit'.
        """
        # Login Audit Course instructor
        self.client.login(username=self.audit_course_instructor.username, password='test')

        csv_content = b"test_student_wl@example.com,test_student_wl,Test Student,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.audit_course_url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # Verify enrollment modes to be 'audit'
        for enrollment in manual_enrollments:
            self.assertEqual(enrollment.enrollment.mode, CourseMode.AUDIT)

    @patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': True})
    def test_honor_enrollment_mode(self):
        """
        Test that enrollment mode for unpaid honor courses is 'honor'.
        """
        # Remove white label course price
        self.white_label_course_mode.min_price = 0
        self.white_label_course_mode.suggested_prices = ''
        self.white_label_course_mode.save()

        # Login Audit Course instructor
        self.client.login(username=self.white_label_course_instructor.username, password='test')

        csv_content = b"test_student_wl@example.com,test_student_wl,Test Student,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.white_label_course_url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['row_errors']), 0)
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # Verify enrollment modes to be 'honor'
        for enrollment in manual_enrollments:
            self.assertEqual(enrollment.enrollment.mode, CourseMode.HONOR)


@ddt.ddt
class TestInstructorAPIEnrollment(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test enrollment modification endpoint.

    This test does NOT exhaustively test state changes, that is the
    job of test_enrollment. This tests the response and action switch.
    """

    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIEnrollment, cls).setUpClass()
        cls.course = CourseFactory.create()

        # Email URL values
        cls.site_name = configuration_helpers.get_value(
            'SITE_NAME',
            settings.SITE_NAME
        )
        cls.about_path = '/courses/{}/about'.format(cls.course.id)
        cls.course_path = '/courses/{}/'.format(cls.course.id)

    def setUp(self):
        super(TestInstructorAPIEnrollment, self).setUp()

        self.request = RequestFactory().request()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

        self.enrolled_student = UserFactory(username='EnrolledStudent', first_name='Enrolled', last_name='Student')
        CourseEnrollment.enroll(
            self.enrolled_student,
            self.course.id
        )
        self.notenrolled_student = UserFactory(username='NotEnrolledStudent', first_name='NotEnrolled',
                                               last_name='Student')

        # Create invited, but not registered, user
        cea = CourseEnrollmentAllowed(email='robot-allowed@robot.org', course_id=self.course.id)
        cea.save()
        self.allowed_email = 'robot-allowed@robot.org'

        self.notregistered_email = 'robot-not-an-email-yet@robot.org'
        self.assertEqual(User.objects.filter(email=self.notregistered_email).count(), 0)

        # uncomment to enable enable printing of large diffs
        # from failed assertions in the event of a test failure.
        # (comment because pylint C0103(invalid-name))
        # self.maxDiff = None

    def test_missing_params(self):
        """ Test missing all query parameters. """
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_bad_action(self):
        """ Test with an invalid action. """
        action = 'robot-not-an-action'
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.enrolled_student.email, 'action': action})
        self.assertEqual(response.status_code, 400)

    def test_invalid_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': 'percivaloctavius@', 'action': 'enroll', 'email_students': False})
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "results": [
                {
                    "identifier": 'percivaloctavius@',
                    "invalidIdentifier": True,
                }
            ]
        }

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_invalid_username(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url,
                                    {'identifiers': 'percivaloctavius', 'action': 'enroll', 'email_students': False})
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "results": [
                {
                    "identifier": 'percivaloctavius',
                    "invalidIdentifier": True,
                }
            ]
        }

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_enroll_with_username(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.username, 'action': 'enroll',
                                          'email_students': False})
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "results": [
                {
                    "identifier": self.notenrolled_student.username,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_enroll_without_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'enroll',
                                          'email_students': False})
        print(u"type(self.notenrolled_student.email): {}".format(type(self.notenrolled_student.email)))
        self.assertEqual(response.status_code, 200)

        # test that the user is now enrolled
        user = User.objects.get(email=self.notenrolled_student.email)
        self.assertTrue(CourseEnrollment.is_enrolled(user, self.course.id))

        # test the response data
        expected = {
            "action": "enroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.notenrolled_student.email,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    @ddt.data('http', 'https')
    def test_enroll_with_email(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notenrolled_student.email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)

        print(u"type(self.notenrolled_student.email): {}".format(type(self.notenrolled_student.email)))
        self.assertEqual(response.status_code, 200)

        # test that the user is now enrolled
        user = User.objects.get(email=self.notenrolled_student.email)
        self.assertTrue(CourseEnrollment.is_enrolled(user, self.course.id))

        # test the response data
        expected = {
            "action": "enroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.notenrolled_student.email,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been enrolled in {}'.format(self.course.display_name)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]

        assert text_body.startswith('Dear NotEnrolled Student\n\n')

        for body in [text_body, html_body]:
            self.assertIn(u'You have been enrolled in {course_name} at edx.org by a member of the course staff.'.format(
                course_name=self.course.display_name,
            ), body)

            self.assertIn('This course will now appear on your edx.org dashboard.', body)
            self.assertIn('{proto}://{site}{course_path}'.format(
                proto=protocol,
                site=self.site_name,
                course_path=self.course_path,
            ), body)

        self.assertIn("To start accessing course materials, please visit", text_body)
        self.assertIn("This email was automatically sent from edx.org to NotEnrolled Student\n\n", text_body)

    @ddt.data('http', 'https')
    def test_enroll_with_email_not_registered(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ALLOWEDTOENROLL)
        self.assertEqual(response.status_code, 200)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been invited to register for {}'.format(self.course.display_name)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        register_url = '{proto}://{site}/register'.format(proto=protocol, site=self.site_name)

        assert text_body.startswith('Dear student,')
        assert u'To finish your registration, please visit {register_url}'.format(
            register_url=register_url,
        ) in text_body
        assert 'Please finish your registration and fill out' in html_body
        assert register_url in html_body

        for body in [text_body, html_body]:
            assert u'You have been invited to join {course} at edx.org by a member of the course staff.'.format(
                course=self.course.display_name
            ) in body

            assert ('fill out the registration form making sure to use '
                    'robot-not-an-email-yet@robot.org in the Email field') in body

            assert 'Once you have registered and activated your account,' in body

            assert '{proto}://{site}{about_path}'.format(
                proto=protocol,
                site=self.site_name,
                about_path=self.about_path
            ) in body

            assert 'This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org' in body

    @ddt.data('http', 'https')
    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_enroll_email_not_registered_mktgsite(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ALLOWEDTOENROLL)
        self.assertEqual(response.status_code, 200)

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]

        assert text_body.startswith('Dear student,')
        assert 'To finish your registration, please visit' in text_body
        assert 'Please finish your registration and fill' in html_body

        for body in [text_body, html_body]:
            assert u'You have been invited to join {display_name} at edx.org by a member of the course staff.'.format(
                display_name=self.course.display_name
            ) in body

            assert '{proto}://{site}/register'.format(
                proto=protocol,
                site=self.site_name
            ) in body

            assert ('fill out the registration form making sure to use '
                    'robot-not-an-email-yet@robot.org in the Email field') in body

            assert u'You can then enroll in {display_name}.'.format(
                display_name=self.course.display_name
            ) in body

            assert 'This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org' in body

    @ddt.data('http', 'https')
    def test_enroll_with_email_not_registered_autoenroll(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True,
                  'auto_enroll': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        print(u"type(self.notregistered_email): {}".format(type(self.notregistered_email)))
        self.assertEqual(response.status_code, 200)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been invited to register for {}'.format(self.course.display_name)
        )
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ALLOWEDTOENROLL)

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        register_url = '{proto}://{site}/register'.format(
            proto=protocol,
            site=self.site_name,
        )

        assert text_body.startswith('Dear student,')
        assert u'To finish your registration, please visit {register_url}'.format(
            register_url=register_url,
        ) in text_body
        assert 'Please finish your registration and fill out the registration' in html_body
        assert 'Finish Your Registration' in html_body
        assert register_url in html_body

        for body in [text_body, html_body]:
            assert u'You have been invited to join {display_name} at edx.org by a member of the course staff.'.format(
                display_name=self.course.display_name
            ) in body

            assert (' and fill '
                    'out the registration form making sure to use robot-not-an-email-yet@robot.org '
                    'in the Email field') in body

            assert (u'Once you have registered and activated your account, '
                    u'you will see {display_name} listed on your dashboard.').format(
                display_name=self.course.display_name
            ) in body

            assert 'This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org' in body

    def test_unenroll_without_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.enrolled_student.email, 'action': 'unenroll',
                                          'email_students': False})
        print(u"type(self.enrolled_student.email): {}".format(type(self.enrolled_student.email)))
        self.assertEqual(response.status_code, 200)

        # test that the user is now unenrolled
        user = User.objects.get(email=self.enrolled_student.email)
        self.assertFalse(CourseEnrollment.is_enrolled(user, self.course.id))

        # test the response data
        expected = {
            "action": "unenroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.enrolled_student.email,
                    "before": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, ENROLLED_TO_UNENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_unenroll_with_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.enrolled_student.email, 'action': 'unenroll',
                                          'email_students': True})
        print(u"type(self.enrolled_student.email): {}".format(type(self.enrolled_student.email)))
        self.assertEqual(response.status_code, 200)

        # test that the user is now unenrolled
        user = User.objects.get(email=self.enrolled_student.email)
        self.assertFalse(CourseEnrollment.is_enrolled(user, self.course.id))

        # test the response data
        expected = {
            "action": "unenroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.enrolled_student.email,
                    "before": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, ENROLLED_TO_UNENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been unenrolled from {display_name}'.format(display_name=self.course.display_name,)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]

        assert text_body.startswith('Dear Enrolled Student')

        for body in [text_body, html_body]:
            assert u'You have been unenrolled from {display_name} at edx.org by a member of the course staff.'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'This course will no longer appear on your edx.org dashboard.' in body
            assert 'Your other courses have not been affected.' in body
            assert 'This email was automatically sent from edx.org to Enrolled Student' in body

    def test_unenroll_with_email_allowed_student(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url,
                                    {'identifiers': self.allowed_email, 'action': 'unenroll', 'email_students': True})
        print(u"type(self.allowed_email): {}".format(type(self.allowed_email)))
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "unenroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.allowed_email,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": False,
                        "allowed": True,
                    },
                    "after": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": False,
                        "allowed": False,
                    }
                }
            ]
        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, ALLOWEDTOENROLL_TO_UNENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been unenrolled from {display_name}'.format(display_name=self.course.display_name,)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        assert text_body.startswith('Dear Student,')

        for body in [text_body, html_body]:
            assert u'You have been unenrolled from the course {display_name} by a member of the course staff.'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'Please disregard the invitation previously sent.' in body
            assert 'This email was automatically sent from edx.org to robot-allowed@robot.org' in body

    @ddt.data('http', 'https')
    @patch('lms.djangoapps.instructor.enrollment.uses_shib')
    def test_enroll_with_email_not_registered_with_shib(self, protocol, mock_uses_shib):
        mock_uses_shib.return_value = True

        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        self.assertEqual(response.status_code, 200)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been invited to register for {display_name}'.format(display_name=self.course.display_name,)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        course_url = '{proto}://{site}{about_path}'.format(
            proto=protocol,
            site=self.site_name,
            about_path=self.about_path,
        )
        assert text_body.startswith('Dear student,')
        assert u'To access this course visit {course_url} and register for this course.'.format(
            course_url=course_url,
        ) in text_body
        assert 'To access this course visit it and register:' in html_body
        assert course_url in html_body

        for body in [text_body, html_body]:
            assert u'You have been invited to join {display_name} at edx.org by a member of the course staff.'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org' in body

    @patch('lms.djangoapps.instructor.enrollment.uses_shib')
    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_enroll_email_not_registered_shib_mktgsite(self, mock_uses_shib):
        # Try with marketing site enabled and shib on
        mock_uses_shib.return_value = True

        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        # Try with marketing site enabled
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            response = self.client.post(url, {'identifiers': self.notregistered_email, 'action': 'enroll',
                                              'email_students': True})

        self.assertEqual(response.status_code, 200)

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        assert text_body.startswith('Dear student,')

        for body in [text_body, html_body]:
            assert u'You have been invited to join {display_name} at edx.org by a member of the course staff.'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org' in body

    @ddt.data('http', 'https')
    @patch('lms.djangoapps.instructor.enrollment.uses_shib')
    def test_enroll_with_email_not_registered_with_shib_autoenroll(self, protocol, mock_uses_shib):
        mock_uses_shib.return_value = True

        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True,
                  'auto_enroll': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        print(u"type(self.notregistered_email): {}".format(type(self.notregistered_email)))
        self.assertEqual(response.status_code, 200)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been invited to register for {display_name}'.format(display_name=self.course.display_name,)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        course_url = '{proto}://{site}{course_path}'.format(
            proto=protocol, site=self.site_name, course_path=self.course_path,
        )

        assert text_body.startswith('Dear student,')
        assert course_url in html_body
        assert u'To access this course visit {course_url} and login.'.format(course_url=course_url) in text_body
        assert 'To access this course click on the button below and login:' in html_body

        for body in [text_body, html_body]:
            assert u'You have been invited to join {display_name} at edx.org by a member of the course staff.'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org' in body

    def test_enroll_already_enrolled_student(self):
        """
        Ensure that already enrolled "verified" students cannot be downgraded
        to "honor"
        """
        course_enrollment = CourseEnrollment.objects.get(
            user=self.enrolled_student, course_id=self.course.id
        )
        # make this enrollment "verified"
        course_enrollment.mode = u'verified'
        course_enrollment.save()
        self.assertEqual(course_enrollment.mode, u'verified')

        # now re-enroll the student through the instructor dash
        self._change_student_enrollment(self.enrolled_student, self.course, 'enroll')

        # affirm that the student is still in "verified" mode
        course_enrollment = CourseEnrollment.objects.get(
            user=self.enrolled_student, course_id=self.course.id
        )
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, ENROLLED_TO_ENROLLED)
        self.assertEqual(course_enrollment.mode, u"verified")

    def create_paid_course(self):
        """
        create paid course mode.
        """
        paid_course = CourseFactory.create()
        CourseModeFactory.create(course_id=paid_course.id, min_price=50, mode_slug=CourseMode.HONOR)
        CourseInstructorRole(paid_course.id).add_users(self.instructor)
        return paid_course

    def test_unenrolled_allowed_to_enroll_user(self):
        """
        test to unenroll allow to enroll user.
        """
        paid_course = self.create_paid_course()
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(paid_course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing..', 'role': 'Learner'}
        response = self.client.post(url, params)
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ALLOWEDTOENROLL)
        self.assertEqual(response.status_code, 200)

        # now registered the user
        UserFactory(email=self.notregistered_email)
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(paid_course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing', 'role': 'Learner'}
        response = self.client.post(url, params)
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 2)
        self.assertEqual(manual_enrollments[1].state_transition, ALLOWEDTOENROLL_TO_ENROLLED)
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.notregistered_email,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": True,
                    },
                    "after": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": True,
                    }
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_unenrolled_already_not_enrolled_user(self):
        """
        test unenrolled user already not enrolled in a course.
        """
        paid_course = self.create_paid_course()
        course_enrollment = CourseEnrollment.objects.filter(
            user__email=self.notregistered_email, course_id=paid_course.id
        )
        self.assertEqual(course_enrollment.count(), 0)

        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(paid_course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'unenroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing', 'role': 'Learner'}

        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "unenroll",
            "auto_enroll": False,
            "results": [
                {
                    "identifier": self.notregistered_email,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": False,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": False,
                        "allowed": False,
                    }
                }
            ]
        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_UNENROLLED)

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_unenroll_and_enroll_verified(self):
        """
        Test that unenrolling and enrolling a student from a verified track
        results in that student being in the default track
        """
        course_enrollment = CourseEnrollment.objects.get(
            user=self.enrolled_student, course_id=self.course.id
        )
        # upgrade enrollment
        course_enrollment.mode = u'verified'
        course_enrollment.save()
        self.assertEqual(course_enrollment.mode, u'verified')

        self._change_student_enrollment(self.enrolled_student, self.course, 'unenroll')

        self._change_student_enrollment(self.enrolled_student, self.course, 'enroll')

        course_enrollment = CourseEnrollment.objects.get(
            user=self.enrolled_student, course_id=self.course.id
        )
        self.assertEqual(course_enrollment.mode, CourseMode.DEFAULT_MODE_SLUG)

    def test_role_and_reason_are_persisted(self):
        """
        test that role and reason fields are persisted in the database
        """
        paid_course = self.create_paid_course()
        url = reverse('students_update_enrollment', kwargs={'course_id': text_type(paid_course.id)})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing', 'role': 'Learner'}
        response = self.client.post(url, params)

        manual_enrollment = ManualEnrollmentAudit.objects.first()
        self.assertEqual(manual_enrollment.reason, 'testing')
        self.assertEqual(manual_enrollment.role, 'Learner')
        self.assertEqual(response.status_code, 200)

    def _change_student_enrollment(self, user, course, action):
        """
        Helper function that posts to 'students_update_enrollment' to change
        a student's enrollment
        """
        url = reverse(
            'students_update_enrollment',
            kwargs={'course_id': text_type(course.id)},
        )
        params = {
            'identifiers': user.email,
            'action': action,
            'email_students': True,
            'reason': 'change user enrollment',
            'role': 'Learner'
        }
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        return response

    def test_get_enrollment_status(self):
        """Check that enrollment states are reported correctly."""

        # enrolled, active
        url = reverse(
            'get_student_enrollment_status',
            kwargs={'course_id': text_type(self.course.id)},
        )
        params = {
            'unique_student_identifier': 'EnrolledStudent'
        }
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            res_json['enrollment_status'],
            'Enrollment status for EnrolledStudent: active'
        )

        # unenrolled, inactive
        CourseEnrollment.unenroll(
            self.enrolled_student,
            self.course.id
        )

        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            res_json['enrollment_status'],
            'Enrollment status for EnrolledStudent: inactive'
        )

        # invited, not yet registered
        params = {
            'unique_student_identifier': 'robot-allowed@robot.org'
        }

        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            res_json['enrollment_status'],
            'Enrollment status for robot-allowed@robot.org: pending'
        )

        # never enrolled or invited
        params = {
            'unique_student_identifier': 'nonotever@example.com'
        }

        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            res_json['enrollment_status'],
            'Enrollment status for nonotever@example.com: never enrolled'
        )


@ddt.ddt
class TestInstructorAPIBulkBetaEnrollment(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test bulk beta modify access endpoint.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIBulkBetaEnrollment, cls).setUpClass()
        cls.course = CourseFactory.create()
        # Email URL values
        cls.site_name = configuration_helpers.get_value(
            'SITE_NAME',
            settings.SITE_NAME
        )
        cls.about_path = '/courses/{}/about'.format(cls.course.id)
        cls.course_path = '/courses/{}/'.format(cls.course.id)

    def setUp(self):
        super(TestInstructorAPIBulkBetaEnrollment, self).setUp()

        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

        self.beta_tester = BetaTesterFactory(course_key=self.course.id)
        CourseEnrollment.enroll(
            self.beta_tester,
            self.course.id
        )
        self.assertTrue(CourseBetaTesterRole(self.course.id).has_user(self.beta_tester))

        self.notenrolled_student = UserFactory(username='NotEnrolledStudent')

        self.notregistered_email = 'robot-not-an-email-yet@robot.org'
        self.assertEqual(User.objects.filter(email=self.notregistered_email).count(), 0)

        self.request = RequestFactory().request()

        # uncomment to enable enable printing of large diffs
        # from failed assertions in the event of a test failure.
        # (comment because pylint C0103(invalid-name))
        # self.maxDiff = None

    def test_beta_tester_must_not_earn_cert(self):
        """
        Test to ensure that beta tester must not earn certificate in a course
        in which he/she is a beta-tester.
        """
        with LogCapture() as capture:
            message = u'Cancelling course certificate generation for user [{}] against course [{}], ' \
                      u'user is a Beta Tester.'
            message = message.format(self.course.id, self.beta_tester.username)
            generate_user_certificates(self.beta_tester, self.course.id, self.course)
            capture.check_present(('edx.certificate', 'INFO', message))

    def test_missing_params(self):
        """ Test missing all query parameters. """
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_bad_action(self):
        """ Test with an invalid action. """
        action = 'robot-not-an-action'
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.beta_tester.email, 'action': action})
        self.assertEqual(response.status_code, 400)

    def add_notenrolled(self, response, identifier):
        """
        Test Helper Method (not a test, called by other tests)

        Takes a client response from a call to bulk_beta_modify_access with 'email_students': False,
        and the student identifier (email or username) given as 'identifiers' in the request.

        Asserts the reponse returns cleanly, that the student was added as a beta tester, and the
        response properly contains their identifier, 'error': False, and 'userDoesNotExist': False.
        Additionally asserts no email was sent.
        """
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CourseBetaTesterRole(self.course.id).has_user(self.notenrolled_student))
        # test the response data
        expected = {
            "action": "add",
            "results": [
                {
                    "identifier": identifier,
                    "error": False,
                    "userDoesNotExist": False,
                    "is_active": True
                }
            ]
        }

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_add_notenrolled_email(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': False})
        self.add_notenrolled(response, self.notenrolled_student.email)
        self.assertFalse(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    def test_add_notenrolled_email_autoenroll(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': False, 'auto_enroll': True})
        self.add_notenrolled(response, self.notenrolled_student.email)
        self.assertTrue(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    def test_add_notenrolled_username(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.username, 'action': 'add', 'email_students': False})
        self.add_notenrolled(response, self.notenrolled_student.username)
        self.assertFalse(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    def test_add_notenrolled_username_autoenroll(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.username, 'action': 'add', 'email_students': False, 'auto_enroll': True})
        self.add_notenrolled(response, self.notenrolled_student.username)
        self.assertTrue(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    @ddt.data('http', 'https')
    def test_add_notenrolled_with_email(self, protocol):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(CourseBetaTesterRole(self.course.id).has_user(self.notenrolled_student))
        # test the response data
        expected = {
            "action": "add",
            "results": [
                {
                    "identifier": self.notenrolled_student.email,
                    "error": False,
                    "userDoesNotExist": False,
                    "is_active": True
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been invited to a beta test for {display_name}'.format(display_name=self.course.display_name,)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        student_name = self.notenrolled_student.profile.name
        assert text_body.startswith(u'Dear {student_name}'.format(student_name=student_name))
        assert u'Visit {display_name}'.format(display_name=self.course.display_name) in html_body

        for body in [text_body, html_body]:
            assert u'You have been invited to be a beta tester for {display_name} at edx.org'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'by a member of the course staff.' in body
            assert 'enroll in this course and begin the beta test' in body

            assert '{proto}://{site}{about_path}'.format(
                proto=protocol,
                site=self.site_name,
                about_path=self.about_path,
            ) in body

            assert u'This email was automatically sent from edx.org to {student_email}'.format(
                student_email=self.notenrolled_student.email,
            ) in body

    @ddt.data('http', 'https')
    def test_add_notenrolled_with_email_autoenroll(self, protocol):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        params = {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': True,
                  'auto_enroll': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(CourseBetaTesterRole(self.course.id).has_user(self.notenrolled_student))
        # test the response data
        expected = {
            "action": "add",
            "results": [
                {
                    "identifier": self.notenrolled_student.email,
                    "error": False,
                    "userDoesNotExist": False,
                    "is_active": True
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been invited to a beta test for {display_name}'.format(display_name=self.course.display_name)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        student_name = self.notenrolled_student.profile.name
        assert text_body.startswith(u'Dear {student_name}'.format(student_name=student_name))

        for body in [text_body, html_body]:
            assert u'You have been invited to be a beta tester for {display_name} at edx.org'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'by a member of the course staff' in body

            assert 'To start accessing course materials, please visit' in body
            assert '{proto}://{site}{course_path}'.format(
                proto=protocol,
                site=self.site_name,
                course_path=self.course_path
            )

            assert u'This email was automatically sent from edx.org to {student_email}'.format(
                student_email=self.notenrolled_student.email,
            ) in body

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_add_notenrolled_email_mktgsite(self):
        # Try with marketing site enabled
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': True})

        self.assertEqual(response.status_code, 200)

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        student_name = self.notenrolled_student.profile.name
        assert text_body.startswith(u'Dear {student_name}'.format(student_name=student_name))

        for body in [text_body, html_body]:
            assert u'You have been invited to be a beta tester for {display_name} at edx.org'.format(
                display_name=self.course.display_name,
            ) in body

            assert 'by a member of the course staff.' in body
            assert 'Visit edx.org' in body
            assert 'enroll in this course and begin the beta test' in body
            assert u'This email was automatically sent from edx.org to {student_email}'.format(
                student_email=self.notenrolled_student.email,
            ) in body

    def test_enroll_with_email_not_registered(self):
        # User doesn't exist
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url,
                                    {'identifiers': self.notregistered_email, 'action': 'add', 'email_students': True,
                                     'reason': 'testing'})
        self.assertEqual(response.status_code, 200)
        # test the response data
        expected = {
            "action": "add",
            "results": [
                {
                    "identifier": self.notregistered_email,
                    "error": True,
                    "userDoesNotExist": True,
                    "is_active": None
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_remove_without_email(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url,
                                    {'identifiers': self.beta_tester.email, 'action': 'remove', 'email_students': False,
                                     'reason': 'testing'})
        self.assertEqual(response.status_code, 200)

        # Works around a caching bug which supposedly can't happen in prod. The instance here is not ==
        # the instance fetched from the email above which had its cache cleared
        if hasattr(self.beta_tester, '_roles'):
            del self.beta_tester._roles
        self.assertFalse(CourseBetaTesterRole(self.course.id).has_user(self.beta_tester))

        # test the response data
        expected = {
            "action": "remove",
            "results": [
                {
                    "identifier": self.beta_tester.email,
                    "error": False,
                    "userDoesNotExist": False,
                    "is_active": True
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_remove_with_email(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url,
                                    {'identifiers': self.beta_tester.email, 'action': 'remove', 'email_students': True,
                                     'reason': 'testing'})
        self.assertEqual(response.status_code, 200)

        # Works around a caching bug which supposedly can't happen in prod. The instance here is not ==
        # the instance fetched from the email above which had its cache cleared
        if hasattr(self.beta_tester, '_roles'):
            del self.beta_tester._roles
        self.assertFalse(CourseBetaTesterRole(self.course.id).has_user(self.beta_tester))

        # test the response data
        expected = {
            "action": "remove",
            "results": [
                {
                    "identifier": self.beta_tester.email,
                    "error": False,
                    "userDoesNotExist": False,
                    "is_active": True
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)
        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been removed from a beta test for {display_name}'.format(display_name=self.course.display_name,)
        )

        text_body = mail.outbox[0].body
        html_body = mail.outbox[0].alternatives[0][0]
        assert text_body.startswith(u'Dear {name}'.format(name=self.beta_tester.profile.name))

        for body in [text_body, html_body]:
            assert u'You have been removed as a beta tester for {display_name} at edx.org'.format(
                display_name=self.course.display_name,
            ) in body

            assert ('This course will remain on your dashboard, but you will no longer be '
                    'part of the beta testing group.') in body

            assert 'Your other courses have not been affected.' in body

            assert u'This email was automatically sent from edx.org to {email_address}'.format(
                email_address=self.beta_tester.email,
            ) in body


class TestInstructorAPILevelsAccess(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints whereby instructors can change permissions
    of other users.

    This test does NOT test whether the actions had an effect on the
    database, that is the job of test_access.
    This tests the response and action switch.
    Actually, modify_access does not have a very meaningful
    response yet, so only the status code is tested.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPILevelsAccess, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAPILevelsAccess, self).setUp()

        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

        self.other_instructor = InstructorFactory(course_key=self.course.id)
        self.other_staff = StaffFactory(course_key=self.course.id)
        self.other_user = UserFactory()

    def test_modify_access_noparams(self):
        """ Test missing all query parameters. """
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_modify_access_bad_action(self):
        """ Test with an invalid action parameter. """
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'staff',
            'action': 'robot-not-an-action',
        })
        self.assertEqual(response.status_code, 400)

    def test_modify_access_bad_role(self):
        """ Test with an invalid action parameter. """
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'robot-not-a-roll',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 400)

    def test_modify_access_allow(self):
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_user.email,
            'rolename': 'staff',
            'action': 'allow',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_allow_with_uname(self):
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_instructor.username,
            'rolename': 'staff',
            'action': 'allow',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke(self):
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'staff',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke_with_username(self):
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.username,
            'rolename': 'staff',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_with_fake_user(self):
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': 'GandalfTheGrey',
            'rolename': 'staff',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)
        expected = {
            'unique_student_identifier': 'GandalfTheGrey',
            'userDoesNotExist': True,
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_modify_access_with_inactive_user(self):
        self.other_user.is_active = False
        self.other_user.save()
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_user.username,
            'rolename': 'beta',
            'action': 'allow',
        })
        self.assertEqual(response.status_code, 200)
        expected = {
            'unique_student_identifier': self.other_user.username,
            'inactiveUser': True,
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_modify_access_revoke_not_allowed(self):
        """ Test revoking access that a user does not have. """
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'instructor',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke_self(self):
        """
        Test that an instructor cannot remove instructor privelages from themself.
        """
        url = reverse('modify_access', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.instructor.email,
            'rolename': 'instructor',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)
        # check response content
        expected = {
            'unique_student_identifier': self.instructor.username,
            'rolename': 'instructor',
            'action': 'revoke',
            'removingSelfAsInstructor': True,
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_list_course_role_members_noparams(self):
        """ Test missing all query parameters. """
        url = reverse('list_course_role_members', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_bad_rolename(self):
        """ Test with an invalid rolename parameter. """
        url = reverse('list_course_role_members', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'rolename': 'robot-not-a-rolename',
        })
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_staff(self):
        url = reverse('list_course_role_members', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'rolename': 'staff',
        })
        self.assertEqual(response.status_code, 200)

        # check response content
        expected = {
            'course_id': text_type(self.course.id),
            'staff': [
                {
                    'username': self.other_staff.username,
                    'email': self.other_staff.email,
                    'first_name': self.other_staff.first_name,
                    'last_name': self.other_staff.last_name,
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_list_course_role_members_beta(self):
        url = reverse('list_course_role_members', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'rolename': 'beta',
        })
        self.assertEqual(response.status_code, 200)

        # check response content
        expected = {
            'course_id': text_type(self.course.id),
            'beta': []
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_update_forum_role_membership(self):
        """
        Test update forum role membership with user's email and username.
        """

        # Seed forum roles for course.
        seed_permissions_roles(self.course.id)

        for user in [self.instructor, self.other_user]:
            for identifier_attr in [user.email, user.username]:
                for rolename in ["Administrator", "Moderator", "Community TA"]:
                    for action in ["allow", "revoke"]:
                        self.assert_update_forum_role_membership(user, identifier_attr, rolename, action)

    def assert_update_forum_role_membership(self, current_user, identifier, rolename, action):
        """
        Test update forum role membership.
        Get unique_student_identifier, rolename and action and update forum role.
        """
        url = reverse('update_forum_role_membership', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(
            url,
            {
                'unique_student_identifier': identifier,
                'rolename': rolename,
                'action': action,
            }
        )

        # Status code should be 200.
        self.assertEqual(response.status_code, 200)

        user_roles = current_user.roles.filter(course_id=self.course.id).values_list("name", flat=True)
        if action == 'allow':
            self.assertIn(rolename, user_roles)
        elif action == 'revoke':
            self.assertNotIn(rolename, user_roles)


@ddt.ddt
class TestInstructorAPILevelsDataDump(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints that show data without side effects.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPILevelsDataDump, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAPILevelsDataDump, self).setUp()
        self.course_mode = CourseMode(course_id=self.course.id,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=40)
        self.course_mode.save()
        self.instructor = InstructorFactory(course_key=self.course.id)
        CourseDataResearcherRole(self.course.id).add_users(self.instructor)
        self.client.login(username=self.instructor.username, password='test')

        self.students = [UserFactory() for _ in range(6)]
        for student in self.students:
            CourseEnrollment.enroll(student, self.course.id)

        self.students_who_may_enroll = self.students + [UserFactory() for _ in range(5)]
        for student in self.students_who_may_enroll:
            CourseEnrollmentAllowed.objects.create(
                email=student.email, course_id=self.course.id
            )

    def test_get_problem_responses_invalid_location(self):
        """
        Test whether get_problem_responses returns an appropriate status
        message when users submit an invalid problem location.
        """
        url = reverse(
            'get_problem_responses',
            kwargs={'course_id': text_type(self.course.id)}
        )
        problem_location = ''

        response = self.client.post(url, {'problem_location': problem_location})
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, "Could not find problem with this location.")

    def valid_problem_location(test):  # pylint: disable=no-self-argument
        """
        Decorator for tests that target get_problem_responses endpoint and
        need to pretend user submitted a valid problem location.
        """
        @functools.wraps(test)
        def wrapper(self, *args, **kwargs):
            """
            Run `test` method, ensuring that UsageKey.from_string returns a
            problem key that the get_problem_responses endpoint can
            work with.
            """
            mock_problem_key = NonCallableMock(return_value=u'')
            mock_problem_key.course_key = self.course.id
            with patch.object(UsageKey, 'from_string') as patched_method:
                patched_method.return_value = mock_problem_key
                test(self, *args, **kwargs)
        return wrapper

    @valid_problem_location
    def test_get_problem_responses_successful(self):
        """
        Test whether get_problem_responses returns an appropriate status
        message if CSV generation was started successfully.
        """
        url = reverse(
            'get_problem_responses',
            kwargs={'course_id': text_type(self.course.id)}
        )
        problem_location = ''

        response = self.client.post(url, {'problem_location': problem_location})
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('status', res_json)
        status = res_json['status']
        self.assertIn('is being created', status)
        self.assertNotIn('already in progress', status)
        self.assertIn("task_id", res_json)

    @valid_problem_location
    def test_get_problem_responses_already_running(self):
        """
        Test whether get_problem_responses returns an appropriate status
        message if CSV generation is already in progress.
        """
        url = reverse(
            'get_problem_responses',
            kwargs={'course_id': text_type(self.course.id)}
        )
        task_type = 'problem_responses_csv'
        already_running_status = generate_already_running_error_message(task_type)
        with patch('lms.djangoapps.instructor_task.api.submit_calculate_problem_responses_csv') as submit_task_function:
            error = AlreadyRunningError(already_running_status)
            submit_task_function.side_effect = error
            response = self.client.post(url, {})

        self.assertContains(response, already_running_status, status_code=400)

    def test_get_students_features(self):
        """
        Test that some minimum of information is formatted
        correctly in the response to get_students_features.
        """
        for student in self.students:
            student.profile.city = u"Mos Eisley {}".format(student.id)
            student.profile.save()
        url = reverse('get_students_features', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {})
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('students', res_json)
        for student in self.students:
            student_json = [
                x for x in res_json['students']
                if x['username'] == student.username
            ][0]
            self.assertEqual(student_json['username'], student.username)
            self.assertEqual(student_json['email'], student.email)
            self.assertEqual(student_json['city'], student.profile.city)
            self.assertEqual(student_json['country'], "")

    @ddt.data(True, False)
    def test_get_students_features_cohorted(self, is_cohorted):
        """
        Test that get_students_features includes cohort info when the course is
        cohorted, and does not when the course is not cohorted.
        """
        url = reverse('get_students_features', kwargs={'course_id': text_type(self.course.id)})
        set_course_cohorted(self.course.id, is_cohorted)

        response = self.client.post(url, {})
        res_json = json.loads(response.content.decode('utf-8'))

        self.assertEqual('cohort' in res_json['feature_names'], is_cohorted)

    @ddt.data(True, False)
    def test_get_students_features_teams(self, has_teams):
        """
        Test that get_students_features includes team info when the course is
        has teams enabled, and does not when the course does not have teams enabled
        """
        if has_teams:
            self.course = CourseFactory.create(teams_configuration=TeamsConfig({
                'max_size': 2, 'topics': [{'id': 'topic', 'name': 'Topic', 'description': 'A Topic'}]
            }))
            course_instructor = InstructorFactory(course_key=self.course.id)
            CourseDataResearcherRole(self.course.id).add_users(course_instructor)
            self.client.login(username=course_instructor.username, password='test')

        url = reverse('get_students_features', kwargs={'course_id': text_type(self.course.id)})

        response = self.client.post(url, {})
        res_json = json.loads(response.content.decode('utf-8'))

        self.assertEqual('team' in res_json['feature_names'], has_teams)

    def test_get_students_who_may_enroll(self):
        """
        Test whether get_students_who_may_enroll returns an appropriate
        status message when users request a CSV file of students who
        may enroll in a course.
        """
        url = reverse(
            'get_students_who_may_enroll',
            kwargs={'course_id': text_type(self.course.id)}
        )
        # Successful case:
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        # CSV generation already in progress:
        task_type = 'may_enroll_info_csv'
        already_running_status = generate_already_running_error_message(task_type)
        with patch('lms.djangoapps.instructor_task.api.submit_calculate_may_enroll_csv') as submit_task_function:
            error = AlreadyRunningError(already_running_status)
            submit_task_function.side_effect = error
            response = self.client.post(url, {})
        self.assertContains(response, already_running_status, status_code=400)

    def test_get_student_exam_results(self):
        """
        Test whether get_proctored_exam_results returns an appropriate
        status message when users request a CSV file.
        """
        url = reverse(
            'get_proctored_exam_results',
            kwargs={'course_id': text_type(self.course.id)}
        )

        # Successful case:
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        # CSV generation already in progress:
        task_type = 'proctored_exam_results_report'
        already_running_status = generate_already_running_error_message(task_type)
        with patch('lms.djangoapps.instructor_task.api.submit_proctored_exam_results_report') as submit_task_function:
            error = AlreadyRunningError(already_running_status)
            submit_task_function.side_effect = error
            response = self.client.post(url, {})
            self.assertContains(response, already_running_status, status_code=400)

    def test_access_course_finance_admin_with_invalid_course_key(self):
        """
        Test assert require_course fiance_admin before generating
        a detailed enrollment report
        """
        func = Mock()
        decorated_func = require_finance_admin(func)
        request = self.mock_request()
        response = decorated_func(request, 'invalid_course_key')
        self.assertEqual(response.status_code, 404)
        self.assertFalse(func.called)

    def mock_request(self):
        """
        mock request
        """
        request = Mock()
        request.user = self.instructor
        return request

    def test_access_course_finance_admin_with_valid_course_key(self):
        """
        Test to check the course_finance_admin role with valid key
        but doesn't have access to the function
        """
        func = Mock()
        decorated_func = require_finance_admin(func)
        request = self.mock_request()
        response = decorated_func(request, 'valid/course/key')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(func.called)

    def test_add_user_to_fiance_admin_role_with_valid_course(self):
        """
        test to check that a function is called using a fiance_admin
        rights.
        """
        func = Mock()
        decorated_func = require_finance_admin(func)
        request = self.mock_request()
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        decorated_func(request, text_type(self.course.id))
        self.assertTrue(func.called)

    @patch('lms.djangoapps.instructor.views.api.anonymous_id_for_user', Mock(return_value='42'))
    @patch('lms.djangoapps.instructor.views.api.unique_id_for_user', Mock(return_value='41'))
    def test_get_anon_ids(self):
        """
        Test the CSV output for the anonymized user ids.
        """
        url = reverse('get_anon_ids', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {})
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.decode("utf-8").replace('\r', '')
        self.assertTrue(body.startswith(
            '"User ID","Anonymized User ID","Course Specific Anonymized User ID"'
            '\n"{user_id}","41","42"\n'.format(user_id=self.students[0].id)
        ))
        self.assertTrue(
            body.endswith('"{user_id}","41","42"\n'.format(user_id=self.students[-1].id))
        )
        self.assertIn("attachment; filename=org", response['Content-Disposition'])

    @patch('lms.djangoapps.instructor_task.models.logger.error')
    @patch.dict(settings.GRADES_DOWNLOAD, {'STORAGE_TYPE': 's3', 'ROOT_PATH': 'tmp/edx-s3/grades'})
    def test_list_report_downloads_error(self, mock_error):
        """
        Tests the Rate-Limit exceeded is handled and does not raise 500 error.
        """
        ex_status = 503
        ex_reason = 'Slow Down'
        url = reverse('list_report_downloads', kwargs={'course_id': text_type(self.course.id)})
        with patch('storages.backends.s3boto.S3BotoStorage.listdir', side_effect=BotoServerError(ex_status, ex_reason)):
            response = self.client.post(url, {})
        mock_error.assert_called_with(
            u'Fetching files failed for course: %s, status: %s, reason: %s',
            self.course.id,
            ex_status,
            ex_reason,
        )

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, {"downloads": []})

    def test_list_report_downloads(self):
        url = reverse('list_report_downloads', kwargs={'course_id': text_type(self.course.id)})
        with patch('lms.djangoapps.instructor_task.models.DjangoStorageReportStore.links_for') as mock_links_for:
            mock_links_for.return_value = [
                ('mock_file_name_1', 'https://1.mock.url'),
                ('mock_file_name_2', 'https://2.mock.url'),
            ]
            response = self.client.post(url, {})

        expected_response = {
            "downloads": [
                {
                    "url": "https://1.mock.url",
                    "link": "<a href=\"https://1.mock.url\">mock_file_name_1</a>",
                    "name": "mock_file_name_1"
                },
                {
                    "url": "https://2.mock.url",
                    "link": "<a href=\"https://2.mock.url\">mock_file_name_2</a>",
                    "name": "mock_file_name_2"
                }
            ]
        }
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected_response)

    @ddt.data(*REPORTS_DATA)
    @ddt.unpack
    @valid_problem_location
    def test_calculate_report_csv_success(
        self, report_type, instructor_api_endpoint, task_api_endpoint, extra_instructor_api_kwargs
    ):
        kwargs = {'course_id': text_type(self.course.id)}
        kwargs.update(extra_instructor_api_kwargs)
        url = reverse(instructor_api_endpoint, kwargs=kwargs)
        success_status = u"The {report_type} report is being created.".format(report_type=report_type)
        with patch(task_api_endpoint) as mock_task_api_endpoint:
            if report_type == 'problem responses':
                mock_task_api_endpoint.return_value = Mock(task_id='task-id-1138')
                response = self.client.post(url, {'problem_location': ''})
                self.assertContains(response, success_status)
            else:
                CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
                response = self.client.post(url, {})
                self.assertContains(response, success_status)

    def test_get_ora2_responses_success(self):
        url = reverse('export_ora2_data', kwargs={'course_id': text_type(self.course.id)})

        with patch('lms.djangoapps.instructor_task.api.submit_export_ora2_data') as mock_submit_ora2_task:
            mock_submit_ora2_task.return_value = True
            response = self.client.post(url, {})
        success_status = "The ORA data report is being created."
        self.assertContains(response, success_status)

    def test_get_ora2_responses_already_running(self):
        url = reverse('export_ora2_data', kwargs={'course_id': text_type(self.course.id)})
        task_type = 'export_ora2_data'
        already_running_status = generate_already_running_error_message(task_type)

        with patch('lms.djangoapps.instructor_task.api.submit_export_ora2_data') as mock_submit_ora2_task:
            mock_submit_ora2_task.side_effect = AlreadyRunningError(already_running_status)
            response = self.client.post(url, {})

        self.assertContains(response, already_running_status, status_code=400)

    def test_get_ora2_submission_files_success(self):
        url = reverse('export_ora2_submission_files', kwargs={'course_id': text_type(self.course.id)})

        with patch(
            'lms.djangoapps.instructor_task.api.submit_export_ora2_submission_files'
        ) as mock_submit_ora2_task:
            mock_submit_ora2_task.return_value = True
            response = self.client.post(url, {})

        success_status = 'Attachments archive is being created.'

        self.assertContains(response, success_status)

    def test_get_ora2_submission_files_already_running(self):
        url = reverse('export_ora2_submission_files', kwargs={'course_id': text_type(self.course.id)})
        task_type = 'export_ora2_submission_files'
        already_running_status = generate_already_running_error_message(task_type)

        with patch(
            'lms.djangoapps.instructor_task.api.submit_export_ora2_submission_files'
        ) as mock_submit_ora2_task:
            mock_submit_ora2_task.side_effect = AlreadyRunningError(already_running_status)
            response = self.client.post(url, {})

        self.assertContains(response, already_running_status, status_code=400)

    def test_get_student_progress_url(self):
        """ Test that progress_url is in the successful response. """
        url = reverse('get_student_progress_url', kwargs={'course_id': text_type(self.course.id)})
        data = {'unique_student_identifier': self.students[0].email}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('progress_url', res_json)

    def test_get_student_progress_url_from_uname(self):
        """ Test that progress_url is in the successful response. """
        url = reverse('get_student_progress_url', kwargs={'course_id': text_type(self.course.id)})
        data = {'unique_student_identifier': self.students[0].username}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('progress_url', res_json)

    def test_get_student_progress_url_noparams(self):
        """ Test that the endpoint 404's without the required query params. """
        url = reverse('get_student_progress_url', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_get_student_progress_url_nostudent(self):
        """ Test that the endpoint 400's when requesting an unknown email. """
        url = reverse('get_student_progress_url', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)


class TestInstructorAPIRegradeTask(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints whereby instructors can change student grades.
    This includes resetting attempts and starting rescore tasks.

    This test does NOT test whether the actions had an effect on the
    database, that is the job of task tests and test_enrollment.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIRegradeTask, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-problem-urlname'
        )
        cls.problem_urlname = text_type(cls.problem_location)

    def setUp(self):
        super(TestInstructorAPIRegradeTask, self).setUp()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        self.module_to_reset = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.problem_location,
            state=json.dumps({'attempts': 10}),
        )

    def test_reset_student_attempts_deletall(self):
        """ Make sure no one can delete all students state on a problem. """
        url = reverse('reset_student_attempts', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_student_attempts_single(self):
        """ Test reset single student attempts. """
        url = reverse('reset_student_attempts', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        # make sure problem attempts have been reset.
        changed_module = StudentModule.objects.get(pk=self.module_to_reset.pk)
        self.assertEqual(
            json.loads(changed_module.state)['attempts'],
            0
        )

    # mock out the function which should be called to execute the action.
    @patch('lms.djangoapps.instructor_task.api.submit_reset_problem_attempts_for_all_students')
    def test_reset_student_attempts_all(self, act):
        """ Test reset all student attempts. """
        url = reverse('reset_student_attempts', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_reset_student_attempts_missingmodule(self):
        """ Test reset for non-existant problem. """
        url = reverse('reset_student_attempts', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': 'robot-not-a-real-module',
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_reset_student_attempts_delete(self, _mock_signal):
        """ Test delete single student state. """
        url = reverse('reset_student_attempts', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 200)
        # make sure the module has been deleted
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.module_to_reset.student,
                course_id=self.module_to_reset.course_id,
                # module_id=self.module_to_reset.module_id,
            ).count(),
            0
        )

    def test_reset_student_attempts_nonsense(self):
        """ Test failure with both unique_student_identifier and all_students. """
        url = reverse('reset_student_attempts', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 400)

    @patch('lms.djangoapps.instructor_task.api.submit_rescore_problem_for_student')
    def test_rescore_problem_single(self, act):
        """ Test rescoring of a single student. """
        url = reverse('rescore_problem', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch('lms.djangoapps.instructor_task.api.submit_rescore_problem_for_student')
    def test_rescore_problem_single_from_uname(self, act):
        """ Test rescoring of a single student. """
        url = reverse('rescore_problem', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.username,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch('lms.djangoapps.instructor_task.api.submit_rescore_problem_for_all_students')
    def test_rescore_problem_all(self, act):
        """ Test rescoring for all students. """
        url = reverse('rescore_problem', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True})
    def test_course_has_entrance_exam_in_student_attempts_reset(self):
        """ Test course has entrance exam id set while resetting attempts"""
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
            'delete_module': False,
        })
        self.assertEqual(response.status_code, 400)

    @patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True})
    def test_rescore_entrance_exam_with_invalid_exam(self):
        """ Test course has entrance exam id set while re-scoring. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)


@patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True})
@ddt.ddt
class TestEntranceExamInstructorAPIRegradeTask(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints whereby instructors can rescore student grades,
    reset student attempts and delete state for entrance exam.
    """
    @classmethod
    def setUpClass(cls):
        super(TestEntranceExamInstructorAPIRegradeTask, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='test_org',
            course='test_course',
            run='test_run',
            entrance_exam_id='i4x://{}/{}/chapter/Entrance_exam'.format('test_org', 'test_course')
        )
        cls.course_with_invalid_ee = CourseFactory.create(entrance_exam_id='invalid_exam')

        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            cls.entrance_exam = ItemFactory.create(
                parent=cls.course,
                category='chapter',
                display_name='Entrance exam'
            )
            subsection = ItemFactory.create(
                parent=cls.entrance_exam,
                category='sequential',
                display_name='Subsection 1'
            )
            vertical = ItemFactory.create(
                parent=subsection,
                category='vertical',
                display_name='Vertical 1'
            )
            cls.ee_problem_1 = ItemFactory.create(
                parent=vertical,
                category="problem",
                display_name="Exam Problem - Problem 1"
            )
            cls.ee_problem_2 = ItemFactory.create(
                parent=vertical,
                category="problem",
                display_name="Exam Problem - Problem 2"
            )

    def setUp(self):
        super(TestEntranceExamInstructorAPIRegradeTask, self).setUp()

        self.instructor = InstructorFactory(course_key=self.course.id)
        # Add instructor to invalid ee course
        CourseInstructorRole(self.course_with_invalid_ee.id).add_users(self.instructor)
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        ee_module_to_reset1 = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.ee_problem_1.location,
            state=json.dumps({'attempts': 10, 'done': True}),
        )
        ee_module_to_reset2 = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.ee_problem_2.location,
            state=json.dumps({'attempts': 10, 'done': True}),
        )
        self.ee_modules = [ee_module_to_reset1.module_state_key, ee_module_to_reset2.module_state_key]

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_grade_histogram(self, store):
        """
        Verify that a histogram has been created.
        """
        course = CourseFactory.create(default_store=store)

        usage_key = course.id.make_usage_key('problem', 'first_problem')
        StudentModule.objects.create(
            student_id=1,
            grade=100,
            module_state_key=usage_key
        )
        StudentModule.objects.create(
            student_id=2,
            grade=50,
            module_state_key=usage_key
        )

        grades = grade_histogram(usage_key)
        self.assertEqual(grades[0], (50.0, 1))
        self.assertEqual(grades[1], (100.0, 1))

    def test_reset_entrance_exam_student_attempts_delete_all(self):
        """ Make sure no one can delete all students state on entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_entrance_exam_student_attempts_single(self):
        """ Test reset single student attempts for entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        # make sure problem attempts have been reset.
        changed_modules = StudentModule.objects.filter(module_state_key__in=self.ee_modules)
        for changed_module in changed_modules:
            self.assertEqual(
                json.loads(changed_module.state)['attempts'],
                0
            )

    # mock out the function which should be called to execute the action.
    @patch('lms.djangoapps.instructor_task.api.submit_reset_problem_attempts_in_entrance_exam')
    def test_reset_entrance_exam_all_student_attempts(self, act):
        """ Test reset all student attempts for entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_reset_student_attempts_invalid_entrance_exam(self):
        """ Test reset for invalid entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course_with_invalid_ee.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_entrance_exam_student_delete_state(self):
        """ Test delete single student entrance exam state. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 200)
        # make sure the module has been deleted
        changed_modules = StudentModule.objects.filter(module_state_key__in=self.ee_modules)
        self.assertEqual(changed_modules.count(), 0)

    def test_entrance_exam_delete_state_with_staff(self):
        """ Test entrance exam delete state failure with staff access. """
        self.client.logout()
        staff_user = StaffFactory(course_key=self.course.id)
        self.client.login(username=staff_user.username, password='test')
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 403)

    def test_entrance_exam_reset_student_attempts_nonsense(self):
        """ Test failure with both unique_student_identifier and all_students. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 400)

    @patch('lms.djangoapps.instructor_task.api.submit_rescore_entrance_exam_for_student')
    def test_rescore_entrance_exam_single_student(self, act):
        """ Test re-scoring of entrance exam for single student. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_rescore_entrance_exam_all_student(self):
        """ Test rescoring for all students. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)

    def test_rescore_entrance_exam_if_higher_all_student(self):
        """ Test rescoring for all students only if higher. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
            'only_if_higher': True,
        })
        self.assertEqual(response.status_code, 200)

    def test_rescore_entrance_exam_all_student_and_single(self):
        """ Test re-scoring with both all students and single student parameters. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_rescore_entrance_exam_with_invalid_exam(self):
        """ Test re-scoring of entrance exam with invalid exam. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course_with_invalid_ee.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_list_entrance_exam_instructor_tasks_student(self):
        """ Test list task history for entrance exam AND student. """
        # create a re-score entrance exam task
        url = reverse('rescore_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)

        url = reverse('list_entrance_exam_instructor_tasks', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)

        # check response
        tasks = json.loads(response.content.decode('utf-8'))['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['status'], _('Complete'))

    def test_list_entrance_exam_instructor_tasks_all_student(self):
        """ Test list task history for entrance exam AND all student. """
        url = reverse('list_entrance_exam_instructor_tasks', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        # check response
        tasks = json.loads(response.content.decode('utf-8'))['tasks']
        self.assertEqual(len(tasks), 0)

    def test_list_entrance_exam_instructor_with_invalid_exam_key(self):
        """ Test list task history for entrance exam failure if course has invalid exam. """
        url = reverse('list_entrance_exam_instructor_tasks',
                      kwargs={'course_id': text_type(self.course_with_invalid_ee.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_skip_entrance_exam_student(self):
        """ Test skip entrance exam api for student. """
        # create a re-score entrance exam task
        url = reverse('mark_student_can_skip_entrance_exam', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        # check response
        message = _(u'This student (%s) will skip the entrance exam.') % self.student.email
        self.assertContains(response, message)

        # post again with same student
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })

        # This time response message should be different
        message = _(u'This student (%s) is already allowed to skip the entrance exam.') % self.student.email
        self.assertContains(response, message)


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestInstructorSendEmail(SiteMixin, SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Checks that only instructors have access to email endpoints, and that
    these endpoints are only accessible with courses that actually exist,
    only with valid email messages.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorSendEmail, cls).setUpClass()
        cls.course = CourseFactory.create()
        test_subject = u'\u1234 test subject'
        test_message = u'\u6824 test message'
        cls.full_test_message = {
            'send_to': '["myself", "staff"]',
            'subject': test_subject,
            'message': test_message,
        }
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    @classmethod
    def tearDownClass(cls):
        super(TestInstructorSendEmail, cls).tearDownClass()
        BulkEmailFlag.objects.all().delete()

    def setUp(self):
        super(TestInstructorSendEmail, self).setUp()

        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def test_send_email_as_logged_in_instructor(self):
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 200)

    def test_send_email_but_not_logged_in(self):
        self.client.logout()
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 403)

    def test_send_email_but_not_staff(self):
        self.client.logout()
        student = UserFactory()
        self.client.login(username=student.username, password='test')
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 403)

    def test_send_email_but_course_not_exist(self):
        url = reverse('send_email', kwargs={'course_id': 'GarbageCourse/DNE/NoTerm'})
        response = self.client.post(url, self.full_test_message)
        self.assertNotEqual(response.status_code, 200)

    def test_send_email_no_sendto(self):
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'subject': 'test subject',
            'message': 'test message',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_invalid_sendto(self):
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'send_to': '["invalid_target", "staff"]',
            'subject': 'test subject',
            'message': 'test message',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_no_subject(self):
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'send_to': '["staff"]',
            'message': 'test message',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_no_message(self):
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'send_to': '["staff"]',
            'subject': 'test subject',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_with_site_template_and_from_addr(self):
        site_email = self.site_configuration.site_values.get('course_email_from_addr')
        site_template = self.site_configuration.site_values.get('course_email_template_name')
        CourseEmailTemplate.objects.create(name=site_template)
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, CourseEmail.objects.filter(
            course_id=self.course.id,
            sender=self.instructor,
            subject=self.full_test_message['subject'],
            html_message=self.full_test_message['message'],
            template_name=site_template,
            from_addr=site_email
        ).count())

    def test_send_email_with_org_template_and_from_addr(self):
        org_email = 'fake_org@example.com'
        org_template = 'fake_org_email_template'
        CourseEmailTemplate.objects.create(name=org_template)
        self.site_configuration.site_values.update({
            'course_email_from_addr': {self.course.id.org: org_email},
            'course_email_template_name': {self.course.id.org: org_template}
        })
        self.site_configuration.save()
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, CourseEmail.objects.filter(
            course_id=self.course.id,
            sender=self.instructor,
            subject=self.full_test_message['subject'],
            html_message=self.full_test_message['message'],
            template_name=org_template,
            from_addr=org_email
        ).count())


class MockCompletionInfo(object):
    """Mock for get_task_completion_info"""
    times_called = 0

    def mock_get_task_completion_info(self, *args):  # pylint: disable=unused-argument
        """Mock for get_task_completion_info"""
        self.times_called += 1
        if self.times_called % 2 == 0:
            return True, 'Task Completed'
        return False, 'Task Errored In Some Way'


class TestInstructorAPITaskLists(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test instructor task list endpoint.
    """

    class FakeTask(object):
        """ Fake task object """
        FEATURES = [
            'task_type',
            'task_input',
            'task_id',
            'requester',
            'task_state',
            'created',
            'status',
            'task_message',
            'duration_sec'
        ]

        def __init__(self, completion):
            for feature in self.FEATURES:
                setattr(self, feature, 'expected')
            # created needs to be a datetime
            self.created = datetime.datetime(2013, 10, 25, 11, 42, 35)
            # set 'status' and 'task_message' attrs
            success, task_message = completion()
            if success:
                self.status = "Complete"
            else:
                self.status = "Incomplete"
            self.task_message = task_message
            # Set 'task_output' attr, which will be parsed to the 'duration_sec' attr.
            self.task_output = '{"duration_ms": 1035000}'
            self.duration_sec = 1035000 / 1000.0

        def make_invalid_output(self):
            """Munge task_output to be invalid json"""
            self.task_output = 'HI MY NAME IS INVALID JSON'
            # This should be given the value of 'unknown' if the task output
            # can't be properly parsed
            self.duration_sec = 'unknown'

        def to_dict(self):
            """ Convert fake task to dictionary representation. """
            attr_dict = {key: getattr(self, key) for key in self.FEATURES}
            attr_dict['created'] = attr_dict['created'].isoformat()
            return attr_dict

    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPITaskLists, cls).setUpClass()
        cls.course = CourseFactory.create(
            entrance_exam_id='i4x://{}/{}/chapter/Entrance_exam'.format('test_org', 'test_course')
        )
        cls.problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-problem-urlname'
        )
        cls.problem_urlname = text_type(cls.problem_location)

    def setUp(self):
        super(TestInstructorAPITaskLists, self).setUp()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        self.module = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.problem_location,
            state=json.dumps({'attempts': 10}),
        )
        mock_factory = MockCompletionInfo()
        self.tasks = [self.FakeTask(mock_factory.mock_get_task_completion_info) for _ in range(7)]
        self.tasks[-1].make_invalid_output()

    @patch('lms.djangoapps.instructor_task.api.get_running_instructor_tasks')
    def test_list_instructor_tasks_running(self, act):
        """ Test list of all running tasks. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': text_type(self.course.id)})
        mock_factory = MockCompletionInfo()
        with patch(
            'lms.djangoapps.instructor.views.instructor_task_helpers.get_task_completion_info'
        ) as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content.decode('utf-8'))['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)
        self.assertEqual(actual_tasks, expected_tasks)

    @patch('lms.djangoapps.instructor_task.api.get_instructor_task_history')
    def test_list_background_email_tasks(self, act):
        """Test list of background email tasks."""
        act.return_value = self.tasks
        url = reverse('list_background_email_tasks', kwargs={'course_id': text_type(self.course.id)})
        mock_factory = MockCompletionInfo()
        with patch(
            'lms.djangoapps.instructor.views.instructor_task_helpers.get_task_completion_info'
        ) as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content.decode('utf-8'))['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)
        self.assertEqual(actual_tasks, expected_tasks)

    @patch('lms.djangoapps.instructor_task.api.get_instructor_task_history')
    def test_list_instructor_tasks_problem(self, act):
        """ Test list task history for problem. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': text_type(self.course.id)})
        mock_factory = MockCompletionInfo()
        with patch(
            'lms.djangoapps.instructor.views.instructor_task_helpers.get_task_completion_info'
        ) as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {
                'problem_location_str': self.problem_urlname,
            })
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content.decode('utf-8'))['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)
        self.assertEqual(actual_tasks, expected_tasks)

    @patch('lms.djangoapps.instructor_task.api.get_instructor_task_history')
    def test_list_instructor_tasks_problem_student(self, act):
        """ Test list task history for problem AND student. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': text_type(self.course.id)})
        mock_factory = MockCompletionInfo()
        with patch(
            'lms.djangoapps.instructor.views.instructor_task_helpers.get_task_completion_info'
        ) as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {
                'problem_location_str': self.problem_urlname,
                'unique_student_identifier': self.student.email,
            })
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content.decode('utf-8'))['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)

        self.assertEqual(actual_tasks, expected_tasks)


@patch('lms.djangoapps.instructor_task.api.get_instructor_task_history', autospec=True)
class TestInstructorEmailContentList(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test the instructor email content history endpoint.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorEmailContentList, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorEmailContentList, self).setUp()

        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')
        self.tasks = {}
        self.emails = {}
        self.emails_info = {}

    def setup_fake_email_info(self, num_emails, with_failures=False):
        """ Initialize the specified number of fake emails """
        for email_id in range(num_emails):
            num_sent = random.randint(1, 15401)
            if with_failures:
                failed = random.randint(1, 15401)
            else:
                failed = 0

            self.tasks[email_id] = FakeContentTask(email_id, num_sent, failed, 'expected')
            self.emails[email_id] = FakeEmail(email_id)
            self.emails_info[email_id] = FakeEmailInfo(self.emails[email_id], num_sent, failed)

    def get_matching_mock_email(self, **kwargs):
        """ Returns the matching mock emails for the given id """
        email_id = kwargs.get('id', 0)
        return self.emails[email_id]

    def get_email_content_response(self, num_emails, task_history_request, with_failures=False):
        """ Calls the list_email_content endpoint and returns the repsonse """
        self.setup_fake_email_info(num_emails, with_failures)
        task_history_request.return_value = list(self.tasks.values())
        url = reverse('list_email_content', kwargs={'course_id': text_type(self.course.id)})
        with patch('lms.djangoapps.instructor.views.api.CourseEmail.objects.get') as mock_email_info:
            mock_email_info.side_effect = self.get_matching_mock_email
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        return response

    def check_emails_sent(self, num_emails, task_history_request, with_failures=False):
        """ Tests sending emails with or without failures """
        response = self.get_email_content_response(num_emails, task_history_request, with_failures)
        self.assertTrue(task_history_request.called)
        expected_email_info = [email_info.to_dict() for email_info in self.emails_info.values()]
        actual_email_info = json.loads(response.content.decode('utf-8'))['emails']

        self.assertEqual(len(actual_email_info), num_emails)
        for exp_email, act_email in zip(expected_email_info, actual_email_info):
            self.assertDictEqual(exp_email, act_email)

        self.assertEqual(expected_email_info, actual_email_info)

    def test_content_list_one_email(self, task_history_request):
        """ Test listing of bulk emails when email list has one email """
        response = self.get_email_content_response(1, task_history_request)
        self.assertTrue(task_history_request.called)
        email_info = json.loads(response.content.decode('utf-8'))['emails']

        # Emails list should have one email
        self.assertEqual(len(email_info), 1)

        # Email content should be what's expected
        expected_message = self.emails[0].html_message
        returned_email_info = email_info[0]
        received_message = returned_email_info[u'email'][u'html_message']
        self.assertEqual(expected_message, received_message)

    def test_content_list_no_emails(self, task_history_request):
        """ Test listing of bulk emails when email list empty """
        response = self.get_email_content_response(0, task_history_request)
        self.assertTrue(task_history_request.called)
        email_info = json.loads(response.content.decode('utf-8'))['emails']

        # Emails list should be empty
        self.assertEqual(len(email_info), 0)

    def test_content_list_email_content_many(self, task_history_request):
        """ Test listing of bulk emails sent large amount of emails """
        self.check_emails_sent(50, task_history_request)

    def test_list_email_content_error(self, task_history_request):
        """ Test handling of error retrieving email """
        invalid_task = FakeContentTask(0, 0, 0, 'test')
        invalid_task.make_invalid_input()
        task_history_request.return_value = [invalid_task]
        url = reverse('list_email_content', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        self.assertTrue(task_history_request.called)
        returned_email_info = json.loads(response.content.decode('utf-8'))['emails']
        self.assertEqual(len(returned_email_info), 1)
        returned_info = returned_email_info[0]
        for info in ['created', 'sent_to', 'email', 'number_sent', 'requester']:
            self.assertEqual(returned_info[info], None)

    def test_list_email_with_failure(self, task_history_request):
        """ Test the handling of email task that had failures """
        self.check_emails_sent(1, task_history_request, True)

    def test_list_many_emails_with_failures(self, task_history_request):
        """ Test the handling of many emails with failures """
        self.check_emails_sent(50, task_history_request, True)

    def test_list_email_with_no_successes(self, task_history_request):
        task_info = FakeContentTask(0, 0, 10, 'expected')
        email = FakeEmail(0)
        email_info = FakeEmailInfo(email, 0, 10)
        task_history_request.return_value = [task_info]
        url = reverse('list_email_content', kwargs={'course_id': text_type(self.course.id)})
        with patch('lms.djangoapps.instructor.views.api.CourseEmail.objects.get') as mock_email_info:
            mock_email_info.return_value = email
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        self.assertTrue(task_history_request.called)
        returned_info_list = json.loads(response.content.decode('utf-8'))['emails']

        self.assertEqual(len(returned_info_list), 1)
        returned_info = returned_info_list[0]
        expected_info = email_info.to_dict()
        self.assertDictEqual(expected_info, returned_info)


class TestInstructorAPIHelpers(TestCase):
    """ Test helpers for instructor.api """

    def test_split_input_list(self):
        strings = []
        lists = []
        strings.append(
            "Lorem@ipsum.dolor, sit@amet.consectetur\nadipiscing@elit.Aenean\r convallis@at.lacus\r, ut@lacinia.Sed")
        lists.append(['Lorem@ipsum.dolor', 'sit@amet.consectetur', 'adipiscing@elit.Aenean', 'convallis@at.lacus',
                      'ut@lacinia.Sed'])

        for (stng, lst) in zip(strings, lists):
            self.assertEqual(_split_input_list(stng), lst)

    def test_split_input_list_unicode(self):
        self.assertEqual(_split_input_list('robot@robot.edu, robot2@robot.edu'),
                         ['robot@robot.edu', 'robot2@robot.edu'])
        self.assertEqual(_split_input_list(u'robot@robot.edu, robot2@robot.edu'),
                         ['robot@robot.edu', 'robot2@robot.edu'])
        self.assertEqual(_split_input_list(u'robot@robot.edu, robot2@robot.edu'),
                         [u'robot@robot.edu', 'robot2@robot.edu'])
        scary_unistuff = unichr(40960) + u'abcd' + unichr(1972)
        self.assertEqual(_split_input_list(scary_unistuff), [scary_unistuff])

    def test_msk_from_problem_urlname(self):
        course_id = CourseKey.from_string('MITx/6.002x/2013_Spring')
        name = 'L2Node1'
        output = 'i4x://MITx/6.002x/problem/L2Node1'
        self.assertEqual(text_type(msk_from_problem_urlname(course_id, name)), output)

    def test_msk_from_problem_urlname_error(self):
        args = ('notagoodcourse', 'L2Node1')
        with pytest.raises(ValueError):
            msk_from_problem_urlname(*args)


def get_extended_due(course, unit, user):
    """
    Gets the overridden due date for the given user on the given unit.  Returns
    `None` if there is no override set.
    """
    location = text_type(unit.location)
    dates = get_overrides_for_user(course.id, user)
    for override in dates:
        if text_type(override['location']) == location:
            return override['actual_date']
    return None


def get_date_for_block(course, unit, user):
    """
    Gets the due date for the given user on the given unit (overridden or original).
    Returns `None` if there is no date set.
    (Differs from edx-when's get_date_for_block only in that we skip the cache.
    """
    return get_dates_for_course(course.id, user=user, use_cached=False).get((unit.location, 'due'), None)


class TestDueDateExtensions(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test data dumps for reporting.
    """
    @classmethod
    def setUpClass(cls):
        super(TestDueDateExtensions, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=UTC)

        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            cls.week1 = ItemFactory.create(due=cls.due)
            cls.week2 = ItemFactory.create(due=cls.due)
            cls.week3 = ItemFactory.create()  # No due date
            cls.course.children = [
                text_type(cls.week1.location),
                text_type(cls.week2.location),
                text_type(cls.week3.location)
            ]
            cls.homework = ItemFactory.create(
                parent_location=cls.week1.location,
                due=cls.due
            )
            cls.week1.children = [text_type(cls.homework.location)]

    def setUp(self):
        """
        Fixtures.
        """
        super(TestDueDateExtensions, self).setUp()

        user1 = UserFactory.create()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.week1.location).save()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.week2.location).save()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.week3.location).save()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.homework.location).save()

        user2 = UserFactory.create()
        StudentModule(
            state='{}',
            student_id=user2.id,
            course_id=self.course.id,
            module_state_key=self.week1.location).save()
        StudentModule(
            state='{}',
            student_id=user2.id,
            course_id=self.course.id,
            module_state_key=self.homework.location).save()

        user3 = UserFactory.create()
        StudentModule(
            state='{}',
            student_id=user3.id,
            course_id=self.course.id,
            module_state_key=self.week1.location).save()
        StudentModule(
            state='{}',
            student_id=user3.id,
            course_id=self.course.id,
            module_state_key=self.homework.location).save()

        self.user1 = user1
        self.user2 = user2
        ScheduleFactory.create(enrollment__user=self.user1, enrollment__course_id=self.course.id)
        ScheduleFactory.create(enrollment__user=self.user2, enrollment__course_id=self.course.id)
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')
        extract_dates(None, self.course.id)

    def test_change_due_date(self):
        url = reverse('change_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week1.location),
            'due_datetime': '12/30/2013 00:00'
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(datetime.datetime(2013, 12, 30, 0, 0, tzinfo=UTC),
                         get_extended_due(self.course, self.week1, self.user1))

    def test_change_to_invalid_due_date(self):
        url = reverse('change_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week1.location),
            'due_datetime': '01/01/2009 00:00'
        })
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            None,
            get_extended_due(self.course, self.week1, self.user1)
        )

    def test_change_nonexistent_due_date(self):
        url = reverse('change_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week3.location),
            'due_datetime': '12/30/2013 00:00'
        })
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            None,
            get_extended_due(self.course, self.week3, self.user1)
        )

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_reset_date(self):
        self.test_change_due_date()
        url = reverse('reset_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week1.location),
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            self.due,
            get_extended_due(self.course, self.week1, self.user1)
        )

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_reset_date_only_in_edx_when(self):
        # Start with a unit that only has a date in edx-when
        self.assertEqual(get_date_for_block(self.course, self.week3, self.user1), None)
        original_due = datetime.datetime(2010, 4, 1, tzinfo=UTC)
        set_date_for_block(self.course.id, self.week3.location, 'due', original_due)
        self.assertEqual(get_date_for_block(self.course, self.week3, self.user1), original_due)

        # set override, confirm it took
        override = datetime.datetime(2010, 7, 1, tzinfo=UTC)
        set_date_for_block(self.course.id, self.week3.location, 'due', override, user=self.user1)
        self.assertEqual(get_date_for_block(self.course, self.week3, self.user1), override)

        # Now test that we noticed the edx-when date
        url = reverse('reset_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week3.location),
        })
        self.assertContains(response, 'Successfully reset due date for student')
        self.assertEqual(get_date_for_block(self.course, self.week3, self.user1), original_due)

    def test_show_unit_extensions(self):
        self.test_change_due_date()
        url = reverse('show_unit_extensions',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'url': text_type(self.week1.location)})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            u'data': [{u'Extended Due Date': u'2013-12-30 00:00',
                       u'Full Name': self.user1.profile.name,
                       u'Username': self.user1.username}],
            u'header': [u'Username', u'Full Name', u'Extended Due Date'],
            u'title': u'Users with due date extensions for %s' %
                      self.week1.display_name})

    def test_show_student_extensions(self):
        self.test_change_due_date()
        url = reverse('show_student_extensions',
                      kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {'student': self.user1.username})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            u'data': [{u'Extended Due Date': u'2013-12-30 00:00',
                       u'Unit': self.week1.display_name}],
            u'header': [u'Unit', u'Extended Due Date'],
            u'title': u'Due date extensions for %s (%s)' % (
                self.user1.profile.name, self.user1.username)})


class TestDueDateExtensionsDeletedDate(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for deleting due date extensions
    """

    def setUp(self):
        """
        Fixtures.
        """
        super(TestDueDateExtensionsDeletedDate, self).setUp()

        self.course = CourseFactory.create()
        self.due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=UTC)

        with self.store.bulk_operations(self.course.id, emit_signals=False):
            self.week1 = ItemFactory.create(due=self.due)
            self.week2 = ItemFactory.create(due=self.due)
            self.week3 = ItemFactory.create()  # No due date
            self.course.children = [
                text_type(self.week1.location),
                text_type(self.week2.location),
                text_type(self.week3.location)
            ]
            self.homework = ItemFactory.create(
                parent_location=self.week1.location,
                due=self.due
            )
            self.week1.children = [text_type(self.homework.location)]

        user1 = UserFactory.create()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.week1.location).save()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.week2.location).save()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.week3.location).save()
        StudentModule(
            state='{}',
            student_id=user1.id,
            course_id=self.course.id,
            module_state_key=self.homework.location).save()

        user2 = UserFactory.create()
        StudentModule(
            state='{}',
            student_id=user2.id,
            course_id=self.course.id,
            module_state_key=self.week1.location).save()
        StudentModule(
            state='{}',
            student_id=user2.id,
            course_id=self.course.id,
            module_state_key=self.homework.location).save()

        user3 = UserFactory.create()
        StudentModule(
            state='{}',
            student_id=user3.id,
            course_id=self.course.id,
            module_state_key=self.week1.location).save()
        StudentModule(
            state='{}',
            student_id=user3.id,
            course_id=self.course.id,
            module_state_key=self.homework.location).save()

        self.user1 = user1
        self.user2 = user2
        ScheduleFactory.create(enrollment__user=self.user1, enrollment__course_id=self.course.id)
        ScheduleFactory.create(enrollment__user=self.user2, enrollment__course_id=self.course.id)
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')
        extract_dates(None, self.course.id)

    @override_experiment_waffle_flag(RELATIVE_DATES_FLAG, active=True)
    def test_reset_extension_to_deleted_date(self):
        """
        Test that we can delete a due date extension after deleting the normal
        due date, without causing an error.
        """

        url = reverse('change_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week1.location),
            'due_datetime': '12/30/2013 00:00'
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(datetime.datetime(2013, 12, 30, 0, 0, tzinfo=UTC),
                         get_extended_due(self.course, self.week1, self.user1))

        self.week1.due = None
        self.week1 = self.store.update_item(self.week1, self.user1.id)
        extract_dates(None, self.course.id)
        # Now, week1's normal due date is deleted but the extension still exists.
        url = reverse('reset_due_date', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': text_type(self.week1.location),
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            self.due,
            get_extended_due(self.course, self.week1, self.user1)
        )


class TestCourseIssuedCertificatesData(SharedModuleStoreTestCase):
    """
    Test data dumps for issued certificates.
    """
    @classmethod
    def setUpClass(cls):
        super(TestCourseIssuedCertificatesData, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestCourseIssuedCertificatesData, self).setUp()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def generate_certificate(self, course_id, mode, status):
        """
        Generate test certificate
        """
        test_user = UserFactory()
        GeneratedCertificateFactory.create(
            user=test_user,
            course_id=course_id,
            mode=mode,
            status=status
        )

    def test_certificates_features_against_status(self):
        """
        Test certificates with status 'downloadable' should be in the response.
        """
        url = reverse('get_issued_certificates', kwargs={'course_id': text_type(self.course.id)})
        # firstly generating downloadable certificates with 'honor' mode
        certificate_count = 3
        for __ in range(certificate_count):
            self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.generating)

        response = self.client.post(url)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('certificates', res_json)
        self.assertEqual(len(res_json['certificates']), 0)

        # Certificates with status 'downloadable' should be in response.
        self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.downloadable)
        response = self.client.post(url)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('certificates', res_json)
        self.assertEqual(len(res_json['certificates']), 1)

    def test_certificates_features_group_by_mode(self):
        """
        Test for certificate csv features against mode. Certificates should be group by 'mode' in reponse.
        """
        url = reverse('get_issued_certificates', kwargs={'course_id': text_type(self.course.id)})
        # firstly generating downloadable certificates with 'honor' mode
        certificate_count = 3
        for __ in range(certificate_count):
            self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.downloadable)

        response = self.client.post(url)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('certificates', res_json)
        self.assertEqual(len(res_json['certificates']), 1)

        # retrieve the first certificate from the list, there should be 3 certificates for 'honor' mode.
        certificate = res_json['certificates'][0]
        self.assertEqual(certificate.get('total_issued_certificate'), 3)
        self.assertEqual(certificate.get('mode'), 'honor')
        self.assertEqual(certificate.get('course_id'), str(self.course.id))

        # Now generating downloadable certificates with 'verified' mode
        for __ in range(certificate_count):
            self.generate_certificate(
                course_id=self.course.id,
                mode='verified',
                status=CertificateStatuses.downloadable
            )

        response = self.client.post(url)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIn('certificates', res_json)

        # total certificate count should be 2 for 'verified' mode.
        self.assertEqual(len(res_json['certificates']), 2)

        # retrieve the second certificate from the list
        certificate = res_json['certificates'][1]
        self.assertEqual(certificate.get('total_issued_certificate'), 3)
        self.assertEqual(certificate.get('mode'), 'verified')

    def test_certificates_features_csv(self):
        """
        Test for certificate csv features.
        """
        url = reverse('get_issued_certificates', kwargs={'course_id': text_type(self.course.id)})
        # firstly generating downloadable certificates with 'honor' mode
        certificate_count = 3
        for __ in range(certificate_count):
            self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.downloadable)

        current_date = datetime.date.today().strftime(u"%B %d, %Y")
        response = self.client.get(url, {'csv': 'true'})
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], u'attachment; filename={0}'.format('issued_certificates.csv'))
        self.assertEqual(
            response.content.strip().decode('utf-8'),
            '"CourseID","Certificate Type","Total Certificates Issued","Date Report Run"\r\n"'
            + str(self.course.id) + '","honor","3","' + current_date + '"'
        )


class TestBulkCohorting(SharedModuleStoreTestCase):
    """
    Test adding users to cohorts in bulk via CSV upload.
    """
    @classmethod
    def setUpClass(cls):
        super(TestBulkCohorting, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestBulkCohorting, self).setUp()
        self.staff_user = StaffFactory(course_key=self.course.id)
        self.non_staff_user = UserFactory.create()
        self.tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempdir)

    def call_add_users_to_cohorts(self, csv_data, suffix='.csv'):
        """
        Call `add_users_to_cohorts` with a file generated from `csv_data`.
        """
        # this temporary file will be removed in `self.tearDown()`
        __, file_name = tempfile.mkstemp(suffix=suffix, dir=self.tempdir)
        with open(file_name, 'w') as file_pointer:
            file_pointer.write(csv_data)
        with open(file_name, 'r') as file_pointer:
            url = reverse('add_users_to_cohorts', kwargs={'course_id': text_type(self.course.id)})
            return self.client.post(url, {'uploaded-file': file_pointer})

    def expect_error_on_file_content(self, file_content, error, file_suffix='.csv'):
        """
        Verify that we get the error we expect for a given file input.
        """
        self.client.login(username=self.staff_user.username, password='test')
        response = self.call_add_users_to_cohorts(file_content, suffix=file_suffix)
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content.decode('utf-8'))
        self.assertEqual(result['error'], error)

    def verify_success_on_file_content(self, file_content, mock_store_upload, mock_cohort_task):
        """
        Verify that `addd_users_to_cohorts` successfully validates the
        file content, uploads the input file, and triggers the
        background task.
        """
        mock_store_upload.return_value = (None, 'fake_file_name.csv')
        self.client.login(username=self.staff_user.username, password='test')
        response = self.call_add_users_to_cohorts(file_content)
        self.assertEqual(response.status_code, 204)
        self.assertTrue(mock_store_upload.called)
        self.assertTrue(mock_cohort_task.called)

    def test_no_cohort_field(self):
        """
        Verify that we get a descriptive verification error when we haven't
        included a cohort field in the uploaded CSV.
        """
        self.expect_error_on_file_content(
            'username,email\n', "The file must contain a 'cohort' column containing cohort names."
        )

    def test_no_username_or_email_field(self):
        """
        Verify that we get a descriptive verification error when we haven't
        included a username or email field in the uploaded CSV.
        """
        self.expect_error_on_file_content(
            'cohort\n', "The file must contain a 'username' column, an 'email' column, or both."
        )

    def test_empty_csv(self):
        """
        Verify that we get a descriptive verification error when we haven't
        included any data in the uploaded CSV.
        """
        self.expect_error_on_file_content(
            '', "The file must contain a 'cohort' column containing cohort names."
        )

    def test_wrong_extension(self):
        """
        Verify that we get a descriptive verification error when we haven't
        uploaded a file with a '.csv' extension.
        """
        self.expect_error_on_file_content(
            '', "The file must end with the extension '.csv'.", file_suffix='.notcsv'
        )

    def test_non_staff_no_access(self):
        """
        Verify that we can't access the view when we aren't a staff user.
        """
        self.client.login(username=self.non_staff_user.username, password='test')
        response = self.call_add_users_to_cohorts('')
        self.assertEqual(response.status_code, 403)

    @patch('lms.djangoapps.instructor_task.api.submit_cohort_students')
    @patch('lms.djangoapps.instructor.views.api.store_uploaded_file')
    def test_success_username(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call a background task when
        the CSV has username and cohort columns.
        """
        self.verify_success_on_file_content(
            'username,cohort\nfoo_username,bar_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('lms.djangoapps.instructor_task.api.submit_cohort_students')
    @patch('lms.djangoapps.instructor.views.api.store_uploaded_file')
    def test_success_email(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when the CSV has email and cohort columns.
        """
        self.verify_success_on_file_content(
            'email,cohort\nfoo_email,bar_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('lms.djangoapps.instructor_task.api.submit_cohort_students')
    @patch('lms.djangoapps.instructor.views.api.store_uploaded_file')
    def test_success_username_and_email(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when the CSV has username, email and cohort columns.
        """
        self.verify_success_on_file_content(
            'username,email,cohort\nfoo_username,bar_email,baz_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('lms.djangoapps.instructor_task.api.submit_cohort_students')
    @patch('lms.djangoapps.instructor.views.api.store_uploaded_file')
    def test_success_carriage_return(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when lines in the CSV are delimited by carriage returns.
        """
        self.verify_success_on_file_content(
            'username,email,cohort\rfoo_username,bar_email,baz_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('lms.djangoapps.instructor_task.api.submit_cohort_students')
    @patch('lms.djangoapps.instructor.views.api.store_uploaded_file')
    def test_success_carriage_return_line_feed(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when lines in the CSV are delimited by carriage returns and line
        feeds.
        """
        self.verify_success_on_file_content(
            'username,email,cohort\r\nfoo_username,bar_email,baz_cohort', mock_store_upload, mock_cohort_task
        )
