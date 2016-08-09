# -*- coding: utf-8 -*-
"""
Unit tests for instructor.api methods.
"""
import datetime
import ddt
import functools
import random
import pytz
import io
import json
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse as django_reverse
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.utils.timezone import utc
from django.utils.translation import ugettext as _

from mock import Mock, patch
from nose.tools import raises
from nose.plugins.attrib import attr
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import UsageKey
from xmodule.modulestore import ModuleStoreEnum

from bulk_email.models import BulkEmailFlag
from course_modes.models import CourseMode
from courseware.models import StudentModule
from courseware.tests.factories import (
    BetaTesterFactory, GlobalStaffFactory, InstructorFactory, StaffFactory, UserProfileFactory
)
from courseware.tests.helpers import LoginEnrollmentTestCase
from django_comment_common.models import FORUM_ROLE_COMMUNITY_TA
from django_comment_common.utils import seed_permissions_roles
from shoppingcart.models import (
    RegistrationCodeRedemption, Order, CouponRedemption,
    PaidCourseRegistration, Coupon, Invoice, CourseRegistrationCode, CourseRegistrationCodeInvoiceItem,
    InvoiceTransaction)
from shoppingcart.pdf import PDFInvoice
from student.models import (
    CourseEnrollment, CourseEnrollmentAllowed, NonExistentCourseError,
    ManualEnrollmentAudit, UNENROLLED_TO_ENROLLED, ENROLLED_TO_UNENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED, ENROLLED_TO_ENROLLED, UNENROLLED_TO_ALLOWEDTOENROLL,
    UNENROLLED_TO_UNENROLLED, ALLOWEDTOENROLL_TO_ENROLLED
)
from student.tests.factories import UserFactory, CourseModeFactory, AdminFactory
from student.roles import CourseBetaTesterRole, CourseSalesAdminRole, CourseFinanceAdminRole, CourseInstructorRole
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.fields import Date

from courseware.models import StudentFieldOverride

import instructor_task.api
import instructor.views.api
from instructor.views.api import require_finance_admin
from instructor.tests.utils import FakeContentTask, FakeEmail, FakeEmailInfo
from instructor.views.api import _split_input_list, common_exceptions_400, generate_unique_password
from instructor_task.api_helper import AlreadyRunningError
from certificates.tests.factories import GeneratedCertificateFactory
from certificates.models import CertificateStatuses

from openedx.core.djangoapps.course_groups.cohorts import set_course_cohort_settings
from openedx.core.lib.xblock_utils import grade_histogram
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from .test_tools import msk_from_problem_urlname

DATE_FIELD = Date()
EXPECTED_CSV_HEADER = (
    '"code","redeem_code_url","course_id","company_name","created_by","redeemed_by","invoice_id","purchaser",'
    '"customer_reference_number","internal_reference"'
)
EXPECTED_COUPON_CSV_HEADER = '"Coupon Code","Course Id","% Discount","Description","Expiration Date",' \
                             '"Is Active","Code Redeemed Count","Total Discounted Seats","Total Discounted Amount"'

# ddt data for test cases involving reports
REPORTS_DATA = (
    {
        'report_type': 'grade',
        'instructor_api_endpoint': 'calculate_grades_csv',
        'task_api_endpoint': 'instructor_task.api.submit_calculate_grades_csv',
        'extra_instructor_api_kwargs': {}
    },
    {
        'report_type': 'enrolled learner profile',
        'instructor_api_endpoint': 'get_students_features',
        'task_api_endpoint': 'instructor_task.api.submit_calculate_students_features_csv',
        'extra_instructor_api_kwargs': {'csv': '/csv'}
    },
    {
        'report_type': 'detailed enrollment',
        'instructor_api_endpoint': 'get_enrollment_report',
        'task_api_endpoint': 'instructor_task.api.submit_detailed_enrollment_features_csv',
        'extra_instructor_api_kwargs': {}
    },
    {
        'report_type': 'enrollment',
        'instructor_api_endpoint': 'get_students_who_may_enroll',
        'task_api_endpoint': 'instructor_task.api.submit_calculate_may_enroll_csv',
        'extra_instructor_api_kwargs': {},
    },
    {
        'report_type': 'proctored exam results',
        'instructor_api_endpoint': 'get_proctored_exam_results',
        'task_api_endpoint': 'instructor_task.api.submit_proctored_exam_results_report',
        'extra_instructor_api_kwargs': {},
    },
    {
        'report_type': 'problem responses',
        'instructor_api_endpoint': 'get_problem_responses',
        'task_api_endpoint': 'instructor_task.api.submit_calculate_problem_responses_csv',
        'extra_instructor_api_kwargs': {},
    }
)

# ddt data for test cases involving executive summary report
EXECUTIVE_SUMMARY_DATA = (
    {
        'report_type': 'executive summary',
        'instructor_api_endpoint': 'get_exec_summary_report',
        'task_api_endpoint': 'instructor_task.api.submit_executive_summary_report',
        'extra_instructor_api_kwargs': {}
    },
)


INSTRUCTOR_GET_ENDPOINTS = set([
    'get_anon_ids',
    'get_coupon_codes',
    'get_issued_certificates',
    'get_sale_order_records',
    'get_sale_records',
])
INSTRUCTOR_POST_ENDPOINTS = set([
    'active_registration_codes',
    'add_users_to_cohorts',
    'bulk_beta_modify_access',
    'calculate_grades_csv',
    'change_due_date',
    'export_ora2_data',
    'generate_registration_codes',
    'get_enrollment_report',
    'get_exec_summary_report',
    'get_grading_config',
    'get_problem_responses',
    'get_proctored_exam_results',
    'get_registration_codes',
    'get_student_progress_url',
    'get_students_features',
    'get_students_who_may_enroll',
    'get_user_invoice_preference',
    'list_background_email_tasks',
    'list_course_role_members',
    'list_email_content',
    'list_entrance_exam_instructor_tasks',
    'list_financial_report_downloads',
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
    'sale_validation',
    'show_student_extensions',
    'show_unit_extensions',
    'send_email',
    'spent_registration_codes',
    'students_update_enrollment',
    'update_forum_role_membership',
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
        raise ValueError("The endpoint {} must be declared in ENDPOINTS before use.".format(endpoint))
    return django_reverse(endpoint, args=args, kwargs=kwargs)


@common_exceptions_400
def view_success(request):  # pylint: disable=unused-argument
    "A dummy view for testing that returns a simple HTTP response"
    return HttpResponse('success')


@common_exceptions_400
def view_user_doesnotexist(request):  # pylint: disable=unused-argument
    "A dummy view that raises a User.DoesNotExist exception"
    raise User.DoesNotExist()


@common_exceptions_400
def view_alreadyrunningerror(request):  # pylint: disable=unused-argument
    "A dummy view that raises an AlreadyRunningError exception"
    raise AlreadyRunningError()


@attr(shard=1)
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
        resp = view_user_doesnotexist(self.request)  # pylint: disable=assignment-from-no-return
        self.assertEqual(resp.status_code, 400)
        self.assertIn("User does not exist", resp.content)

    def test_user_doesnotexist_ajax(self):
        self.request.is_ajax.return_value = True
        resp = view_user_doesnotexist(self.request)  # pylint: disable=assignment-from-no-return
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("User does not exist", result["error"])

    def test_alreadyrunningerror(self):
        self.request.is_ajax.return_value = False
        resp = view_alreadyrunningerror(self.request)  # pylint: disable=assignment-from-no-return
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Task is already running", resp.content)

    def test_alreadyrunningerror_ajax(self):
        self.request.is_ajax.return_value = True
        resp = view_alreadyrunningerror(self.request)  # pylint: disable=assignment-from-no-return
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("Task is already running", result["error"])


@attr(shard=1)
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
        url = reverse(data, kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)

        self.assertEqual(
            response.status_code, 405,
            "Endpoint {} returned status code {} instead of a 405. It should not allow GET.".format(
                data, response.status_code
            )
        )

    @ddt.data(*INSTRUCTOR_GET_ENDPOINTS)
    def test_endpoints_accept_get(self, data):
        """
        Tests that GET endpoints are not rejected with 405 when using GET.
        """
        url = reverse(data, kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)

        self.assertNotEqual(
            response.status_code, 405,
            "Endpoint {} returned status code 405 where it shouldn't, since it should allow GET.".format(
                data
            )
        )


@attr(shard=1)
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestInstructorAPIDenyLevels(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Ensure that users cannot access endpoints they shouldn't be able to.
    """

    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIDenyLevels, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-problem-urlname'
        )
        cls.problem_urlname = cls.problem_location.to_deprecated_string()
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
            module_state_key=self.problem_location,
            state=json.dumps({'attempts': 10}),
        )

        # Endpoints that only Staff or Instructors can access
        self.staff_level_endpoints = [
            ('students_update_enrollment',
             {'identifiers': 'foo@example.org', 'action': 'enroll'}),
            ('get_grading_config', {}),
            ('get_students_features', {}),
            ('get_student_progress_url', {'unique_student_identifier': self.user.username}),
            ('reset_student_attempts',
             {'problem_to_reset': self.problem_urlname, 'unique_student_identifier': self.user.email}),
            ('update_forum_role_membership',
             {'unique_student_identifier': self.user.email, 'rolename': 'Moderator', 'action': 'allow'}),
            ('list_forum_members', {'rolename': FORUM_ROLE_COMMUNITY_TA}),
            ('send_email', {'send_to': '["staff"]', 'subject': 'test', 'message': 'asdf'}),
            ('list_instructor_tasks', {}),
            ('list_background_email_tasks', {}),
            ('list_report_downloads', {}),
            ('list_financial_report_downloads', {}),
            ('calculate_grades_csv', {}),
            ('get_students_features', {}),
            ('get_enrollment_report', {}),
            ('get_students_who_may_enroll', {}),
            ('get_exec_summary_report', {}),
            ('get_proctored_exam_results', {}),
            ('get_problem_responses', {}),
            ('export_ora2_data', {}),
        ]
        # Endpoints that only Instructors can access
        self.instructor_level_endpoints = [
            ('bulk_beta_modify_access', {'identifiers': 'foo@example.org', 'action': 'add'}),
            ('modify_access', {'unique_student_identifier': self.user.email, 'rolename': 'beta', 'action': 'allow'}),
            ('list_course_role_members', {'rolename': 'beta'}),
            ('rescore_problem',
             {'problem_to_reset': self.problem_urlname, 'unique_student_identifier': self.user.email}),
        ]

    def _access_endpoint(self, endpoint, args, status_code, msg):
        """
        Asserts that accessing the given `endpoint` gets a response of `status_code`.

        endpoint: string, endpoint for instructor dash API
        args: dict, kwargs for `reverse` call
        status_code: expected HTTP status code response
        msg: message to display if assertion fails.
        """
        url = reverse(endpoint, kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        mock_problem_key = Mock(return_value=u'')
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

            # TODO: make this work
            if endpoint in ['rescore_problem']:
                continue
            self._access_endpoint(
                endpoint,
                args,
                expected_status,
                "Instructor should be allowed to access endpoint " + endpoint
            )


@attr(shard=1)
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
            'register_and_enroll_students', kwargs={'course_id': unicode(cls.course.id)}
        )
        cls.audit_course_url = reverse(
            'register_and_enroll_students', kwargs={'course_id': unicode(cls.audit_course.id)}
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
            'register_and_enroll_students', kwargs={'course_id': unicode(self.white_label_course.id)}
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

    @patch('instructor.views.api.log.info')
    def test_account_creation_and_enrollment_with_csv(self, info_log):
        """
        Happy path test to create a single new user
        """
        csv_content = "test_student@example.com,test_student_1,tester1,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # test the log for email that's send to new created user.
        info_log.assert_called_with('email sent to new created user at %s', 'test_student@example.com')

    @patch('instructor.views.api.log.info')
    def test_account_creation_and_enrollment_with_csv_with_blank_lines(self, info_log):
        """
        Happy path test to create a single new user
        """
        csv_content = "\ntest_student@example.com,test_student_1,tester1,USA\n\n"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # test the log for email that's send to new created user.
        info_log.assert_called_with('email sent to new created user at %s', 'test_student@example.com')

    @patch('instructor.views.api.log.info')
    def test_email_and_username_already_exist(self, info_log):
        """
        If the email address and username already exists
        and the user is enrolled in the course, do nothing (including no email gets sent out)
        """
        csv_content = "test_student@example.com,test_student_1,tester1,USA\n" \
                      "test_student@example.com,test_student_1,tester2,US"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)

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
        data = json.loads(response.content)
        self.assertNotEquals(len(data['general_errors']), 0)
        self.assertEquals(data['general_errors'][0]['response'], 'Make sure that the file you upload is in CSV format with no extraneous characters or rows.')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_bad_file_upload_type(self):
        """
        Try uploading some non-CSV file and verify that it is rejected
        """
        uploaded_file = SimpleUploadedFile("temp.csv", io.BytesIO(b"some initial binary data: \x00\x01").read())
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['general_errors']), 0)
        self.assertEquals(data['general_errors'][0]['response'], 'Could not read uploaded file.')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_insufficient_data(self):
        """
        Try uploading a CSV file which does not have the exact four columns of data
        """
        csv_content = "test_student@example.com,test_student_1\n"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 1)
        self.assertEquals(data['general_errors'][0]['response'], 'Data in row #1 must have exactly four columns: email, username, full name, and country')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_invalid_email_in_csv(self):
        """
        Test failure case of a poorly formatted email field
        """
        csv_content = "test_student.example.com,test_student_1,tester1,USA"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertNotEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)
        self.assertEquals(data['row_errors'][0]['response'], 'Invalid email {0}.'.format('test_student.example.com'))

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    @patch('instructor.views.api.log.info')
    def test_csv_user_exist_and_not_enrolled(self, info_log):
        """
        If the email address and username already exists
        and the user is not enrolled in the course, enrolled him/her and iterate to next one.
        """
        csv_content = "nonenrolled@test.com,NotEnrolledStudent,tester1,USA"

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
        csv_content = "test_student@example.com,test_student_1,tester1,USA\n" \
                      "test_student@example.com,test_student_2,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        warning_message = 'An account with email {email} exists but the provided username {username} ' \
                          'is different. Enrolling anyway with {email}.'.format(email='test_student@example.com', username='test_student_2')
        self.assertNotEquals(len(data['warnings']), 0)
        self.assertEquals(data['warnings'][0]['response'], warning_message)
        user = User.objects.get(email='test_student@example.com')
        self.assertTrue(CourseEnrollment.is_enrolled(user, self.course.id))

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertTrue(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

    def test_user_with_already_existing_username_in_csv(self):
        """
        If the username already exists (but not the email),
        assume it is a different user and fail to create the new account.
        """
        csv_content = "test_student1@example.com,test_student_1,tester1,USA\n" \
                      "test_student2@example.com,test_student_1,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)

        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['row_errors']), 0)
        self.assertEquals(data['row_errors'][0]['response'], 'Username {user} already exists.'.format(user='test_student_1'))

    def test_csv_file_not_attached(self):
        """
        Test when the user does not attach a file
        """
        csv_content = "test_student1@example.com,test_student_1,tester1,USA\n" \
                      "test_student2@example.com,test_student_1,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)

        response = self.client.post(self.url, {'file_not_found': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['general_errors']), 0)
        self.assertEquals(data['general_errors'][0]['response'], 'File is not attached.')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_raising_exception_in_auto_registration_and_enrollment_case(self):
        """
        Test that exceptions are handled well
        """
        csv_content = "test_student1@example.com,test_student_1,tester1,USA\n" \
                      "test_student2@example.com,test_student_1,tester2,US"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        with patch('instructor.views.api.create_manual_course_enrollment') as mock:
            mock.side_effect = NonExistentCourseError()
            response = self.client.post(self.url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['row_errors']), 0)
        self.assertEquals(data['row_errors'][0]['response'], 'NonExistentCourseError')

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    def test_generate_unique_password(self):
        """
        generate_unique_password should generate a unique password string that excludes certain characters.
        """
        password = generate_unique_password([], 12)
        self.assertEquals(len(password), 12)
        for letter in password:
            self.assertNotIn(letter, 'aAeEiIoOuU1l')

    def test_users_created_and_enrolled_successfully_if_others_fail(self):

        csv_content = "test_student1@example.com,test_student_1,tester1,USA\n" \
                      "test_student3@example.com,test_student_1,tester3,CA\n" \
                      "test_student2@example.com,test_student_2,tester2,USA"

        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotEquals(len(data['row_errors']), 0)
        self.assertEquals(data['row_errors'][0]['response'], 'Username {user} already exists.'.format(user='test_student_1'))
        self.assertTrue(User.objects.filter(username='test_student_1', email='test_student1@example.com').exists())
        self.assertTrue(User.objects.filter(username='test_student_2', email='test_student2@example.com').exists())
        self.assertFalse(User.objects.filter(email='test_student3@example.com').exists())

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 2)

    @patch.object(instructor.views.api, 'generate_random_string',
                  Mock(side_effect=['first', 'first', 'second']))
    def test_generate_unique_password_no_reuse(self):
        """
        generate_unique_password should generate a unique password string that hasn't been generated before.
        """
        generated_password = ['first']
        password = generate_unique_password(generated_password, 12)
        self.assertNotEquals(password, 'first')

    @patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': False})
    def test_allow_automated_signups_flag_not_set(self):
        csv_content = "test_student1@example.com,test_student_1,tester1,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.url, {'students_list': uploaded_file})
        self.assertEquals(response.status_code, 403)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

    @patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': True})
    def test_audit_enrollment_mode(self):
        """
        Test that enrollment mode for audit courses (paid courses) is 'audit'.
        """
        # Login Audit Course instructor
        self.client.login(username=self.audit_course_instructor.username, password='test')

        csv_content = "test_student_wl@example.com,test_student_wl,Test Student,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.audit_course_url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)

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
        self.white_label_course_mode.save()  # pylint: disable=no-member

        # Login Audit Course instructor
        self.client.login(username=self.white_label_course_instructor.username, password='test')

        csv_content = "test_student_wl@example.com,test_student_wl,Test Student,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.white_label_course_url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # Verify enrollment modes to be 'honor'
        for enrollment in manual_enrollments:
            self.assertEqual(enrollment.enrollment.mode, CourseMode.HONOR)

    @patch.dict(settings.FEATURES, {'ALLOW_AUTOMATED_SIGNUPS': True})
    def test_default_shopping_cart_enrollment_mode_for_white_label(self):
        """
        Test that enrollment mode for white label courses (paid courses) is DEFAULT_SHOPPINGCART_MODE_SLUG.
        """
        # Login white label course instructor
        self.client.login(username=self.white_label_course_instructor.username, password='test')

        csv_content = "test_student_wl@example.com,test_student_wl,Test Student,USA"
        uploaded_file = SimpleUploadedFile("temp.csv", csv_content)
        response = self.client.post(self.white_label_course_url, {'students_list': uploaded_file})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(len(data['row_errors']), 0)
        self.assertEquals(len(data['warnings']), 0)
        self.assertEquals(len(data['general_errors']), 0)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)

        # Verify enrollment modes to be CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG
        for enrollment in manual_enrollments:
            self.assertEqual(enrollment.enrollment.mode, CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG)


@attr(shard=1)
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
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_bad_action(self):
        """ Test with an invalid action. """
        action = 'robot-not-an-action'
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.enrolled_student.email, 'action': action})
        self.assertEqual(response.status_code, 400)

    def test_invalid_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
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

        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_invalid_username(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
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

        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_enroll_with_username(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_enroll_without_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'enroll',
                                          'email_students': False})
        print "type(self.notenrolled_student.email): {}".format(type(self.notenrolled_student.email))
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    @ddt.data('http', 'https')
    def test_enroll_with_email(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        params = {'identifiers': self.notenrolled_student.email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)

        print "type(self.notenrolled_student.email): {}".format(type(self.notenrolled_student.email))
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

        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been enrolled in {}'.format(self.course.display_name)
        )
        self.assertEqual(
            mail.outbox[0].body,
            "Dear NotEnrolled Student\n\nYou have been enrolled in {} "
            "at edx.org by a member of the course staff. "
            "The course should now appear on your edx.org dashboard.\n\n"
            "To start accessing course materials, please visit "
            "{proto}://{site}{course_path}\n\n----\n"
            "This email was automatically sent from edx.org to NotEnrolled Student".format(
                self.course.display_name,
                proto=protocol, site=self.site_name, course_path=self.course_path
            )
        )

    @ddt.data('http', 'https')
    def test_enroll_with_email_not_registered(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        self.assertEqual(
            mail.outbox[0].body,
            "Dear student,\n\nYou have been invited to join {} at edx.org by a member of the course staff.\n\n"
            "To finish your registration, please visit {proto}://{site}/register and fill out the "
            "registration form making sure to use robot-not-an-email-yet@robot.org in the E-mail field.\n"
            "Once you have registered and activated your account, "
            "visit {proto}://{site}{about_path} to join the course.\n\n----\n"
            "This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org".format(
                self.course.display_name, proto=protocol, site=self.site_name, about_path=self.about_path
            )
        )

    @ddt.data('http', 'https')
    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_enroll_email_not_registered_mktgsite(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ALLOWEDTOENROLL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            mail.outbox[0].body,
            "Dear student,\n\nYou have been invited to join {display_name}"
            " at edx.org by a member of the course staff.\n\n"
            "To finish your registration, please visit {proto}://{site}/register and fill out the registration form "
            "making sure to use robot-not-an-email-yet@robot.org in the E-mail field.\n"
            "You can then enroll in {display_name}.\n\n----\n"
            "This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org".format(
                display_name=self.course.display_name, proto=protocol, site=self.site_name
            )
        )

    @ddt.data('http', 'https')
    def test_enroll_with_email_not_registered_autoenroll(self, protocol):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True,
                  'auto_enroll': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        print "type(self.notregistered_email): {}".format(type(self.notregistered_email))
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
        self.assertEqual(
            mail.outbox[0].body,
            "Dear student,\n\nYou have been invited to join {display_name}"
            " at edx.org by a member of the course staff.\n\n"
            "To finish your registration, please visit {proto}://{site}/register and fill out the registration form "
            "making sure to use robot-not-an-email-yet@robot.org in the E-mail field.\n"
            "Once you have registered and activated your account,"
            " you will see {display_name} listed on your dashboard.\n\n----\n"
            "This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org".format(
                proto=protocol, site=self.site_name, display_name=self.course.display_name
            )
        )

    def test_unenroll_without_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.enrolled_student.email, 'action': 'unenroll',
                                          'email_students': False})
        print "type(self.enrolled_student.email): {}".format(type(self.enrolled_student.email))
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_unenroll_with_email(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.enrolled_student.email, 'action': 'unenroll',
                                          'email_students': True})
        print "type(self.enrolled_student.email): {}".format(type(self.enrolled_student.email))
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been un-enrolled from {display_name}'.format(display_name=self.course.display_name,)
        )
        self.assertEqual(
            mail.outbox[0].body,
            "Dear Enrolled Student\n\nYou have been un-enrolled in {display_name} "
            "at edx.org by a member of the course staff. "
            "The course will no longer appear on your edx.org dashboard.\n\n"
            "Your other courses have not been affected.\n\n----\n"
            "This email was automatically sent from edx.org to Enrolled Student".format(
                display_name=self.course.display_name,
            )
        )

    def test_unenroll_with_email_allowed_student(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url,
                                    {'identifiers': self.allowed_email, 'action': 'unenroll', 'email_students': True})
        print "type(self.allowed_email): {}".format(type(self.allowed_email))
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been un-enrolled from {display_name}'.format(display_name=self.course.display_name,)
        )
        self.assertEqual(
            mail.outbox[0].body,
            "Dear Student,\n\nYou have been un-enrolled from course {display_name} by a member of the course staff. "
            "Please disregard the invitation previously sent.\n\n----\n"
            "This email was automatically sent from edx.org to robot-allowed@robot.org".format(
                display_name=self.course.display_name,
            )
        )

    @ddt.data('http', 'https')
    @patch('instructor.enrollment.uses_shib')
    def test_enroll_with_email_not_registered_with_shib(self, protocol, mock_uses_shib):
        mock_uses_shib.return_value = True

        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        self.assertEqual(response.status_code, 200)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been invited to register for {display_name}'.format(display_name=self.course.display_name,)
        )

        self.assertEqual(
            mail.outbox[0].body,
            "Dear student,\n\nYou have been invited to join {display_name} at edx.org by a member of the course staff.\n\n"
            "To access the course visit {proto}://{site}{about_path} and register for the course.\n\n----\n"
            "This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org".format(
                proto=protocol, site=self.site_name, about_path=self.about_path,
                display_name=self.course.display_name,
            )
        )

    @patch('instructor.enrollment.uses_shib')
    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_enroll_email_not_registered_shib_mktgsite(self, mock_uses_shib):
        # Try with marketing site enabled and shib on
        mock_uses_shib.return_value = True

        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        # Try with marketing site enabled
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            response = self.client.post(url, {'identifiers': self.notregistered_email, 'action': 'enroll',
                                              'email_students': True})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            mail.outbox[0].body,
            "Dear student,\n\nYou have been invited to join {} at edx.org by a member of the course staff.\n\n----\n"
            "This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org".format(
                self.course.display_name,
            )
        )

    @ddt.data('http', 'https')
    @patch('instructor.enrollment.uses_shib')
    def test_enroll_with_email_not_registered_with_shib_autoenroll(self, protocol, mock_uses_shib):
        mock_uses_shib.return_value = True

        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': True,
                  'auto_enroll': True}
        environ = {'wsgi.url_scheme': protocol}
        response = self.client.post(url, params, **environ)
        print "type(self.notregistered_email): {}".format(type(self.notregistered_email))
        self.assertEqual(response.status_code, 200)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been invited to register for {display_name}'.format(display_name=self.course.display_name,)
        )

        self.assertEqual(
            mail.outbox[0].body,
            "Dear student,\n\nYou have been invited to join {display_name}"
            " at edx.org by a member of the course staff.\n\n"
            "To access the course visit {proto}://{site}{course_path} and login.\n\n----\n"
            "This email was automatically sent from edx.org to robot-not-an-email-yet@robot.org".format(
                display_name=self.course.display_name,
                proto=protocol, site=self.site_name, course_path=self.course_path
            )
        )

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

    def test_reason_field_should_not_be_empty(self):
        """
        test to check that reason field should not be empty when
        manually enrolling the students for the paid courses.
        """
        paid_course = self.create_paid_course()
        url = reverse('students_update_enrollment', kwargs={'course_id': paid_course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': False,
                  'auto_enroll': False}
        response = self.client.post(url, params)
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 0)

        # test the response data
        expected = {
            "action": "enroll",
            "auto_enroll": False,
            "results": [
                {
                    "error": True
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_unenrolled_allowed_to_enroll_user(self):
        """
        test to unenroll allow to enroll user.
        """
        paid_course = self.create_paid_course()
        url = reverse('students_update_enrollment', kwargs={'course_id': paid_course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing..'}
        response = self.client.post(url, params)
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ALLOWEDTOENROLL)
        self.assertEqual(response.status_code, 200)

        # now registered the user
        UserFactory(email=self.notregistered_email)
        url = reverse('students_update_enrollment', kwargs={'course_id': paid_course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'enroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing'}
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
        res_json = json.loads(response.content)
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

        url = reverse('students_update_enrollment', kwargs={'course_id': paid_course.id.to_deprecated_string()})
        params = {'identifiers': self.notregistered_email, 'action': 'unenroll', 'email_students': False,
                  'auto_enroll': False, 'reason': 'testing'}

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

        res_json = json.loads(response.content)
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

    def _change_student_enrollment(self, user, course, action):
        """
        Helper function that posts to 'students_update_enrollment' to change
        a student's enrollment
        """
        url = reverse(
            'students_update_enrollment',
            kwargs={'course_id': course.id.to_deprecated_string()},
        )
        params = {
            'identifiers': user.email,
            'action': action,
            'email_students': True,
            'reason': 'change user enrollment'
        }
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        return response


@attr(shard=1)
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

    def test_missing_params(self):
        """ Test missing all query parameters. """
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_bad_action(self):
        """ Test with an invalid action. """
        action = 'robot-not-an-action'
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                    "userDoesNotExist": False
                }
            ]
        }

        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_add_notenrolled_email(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': False})
        self.add_notenrolled(response, self.notenrolled_student.email)
        self.assertFalse(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    def test_add_notenrolled_email_autoenroll(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': False, 'auto_enroll': True})
        self.add_notenrolled(response, self.notenrolled_student.email)
        self.assertTrue(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    def test_add_notenrolled_username(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.username, 'action': 'add', 'email_students': False})
        self.add_notenrolled(response, self.notenrolled_student.username)
        self.assertFalse(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    def test_add_notenrolled_username_autoenroll(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.username, 'action': 'add', 'email_students': False, 'auto_enroll': True})
        self.add_notenrolled(response, self.notenrolled_student.username)
        self.assertTrue(CourseEnrollment.is_enrolled(self.notenrolled_student, self.course.id))

    @ddt.data('http', 'https')
    def test_add_notenrolled_with_email(self, protocol):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                    "userDoesNotExist": False
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been invited to a beta test for {display_name}'.format(display_name=self.course.display_name,)
        )

        self.assertEqual(
            mail.outbox[0].body,
            u"Dear {student_name}\n\nYou have been invited to be a beta tester "
            "for {display_name} at edx.org by a member of the course staff.\n\n"
            "Visit {proto}://{site}{about_path} to join "
            "the course and begin the beta test.\n\n----\n"
            "This email was automatically sent from edx.org to {student_email}".format(
                display_name=self.course.display_name,
                student_name=self.notenrolled_student.profile.name,
                student_email=self.notenrolled_student.email,
                proto=protocol,
                site=self.site_name,
                about_path=self.about_path
            )
        )

    @ddt.data('http', 'https')
    def test_add_notenrolled_with_email_autoenroll(self, protocol):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                    "userDoesNotExist": False
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You have been invited to a beta test for {display_name}'.format(display_name=self.course.display_name)
        )

        self.assertEqual(
            mail.outbox[0].body,
            u"Dear {student_name}\n\nYou have been invited to be a beta tester "
            "for {display_name} at edx.org by a member of the course staff.\n\n"
            "To start accessing course materials, please visit "
            "{proto}://{site}{course_path}\n\n----\n"
            "This email was automatically sent from edx.org to {student_email}".format(
                display_name=self.course.display_name,
                student_name=self.notenrolled_student.profile.name,
                student_email=self.notenrolled_student.email,
                proto=protocol,
                site=self.site_name,
                course_path=self.course_path
            )
        )

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_add_notenrolled_email_mktgsite(self):
        # Try with marketing site enabled
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'identifiers': self.notenrolled_student.email, 'action': 'add', 'email_students': True})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            mail.outbox[0].body,
            u"Dear {}\n\nYou have been invited to be a beta tester "
            "for {} at edx.org by a member of the course staff.\n\n"
            "Visit edx.org to enroll in the course and begin the beta test.\n\n----\n"
            "This email was automatically sent from edx.org to {}".format(
                self.notenrolled_student.profile.name,
                self.course.display_name,
                self.notenrolled_student.email,
            )
        )

    def test_enroll_with_email_not_registered(self):
        # User doesn't exist
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                    "userDoesNotExist": True
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_remove_without_email(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                    "userDoesNotExist": False
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_remove_with_email(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                    "userDoesNotExist": False
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)
        # Check the outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You have been removed from a beta test for {display_name}'.format(display_name=self.course.display_name,)
        )
        self.assertEqual(
            mail.outbox[0].body,
            "Dear {full_name}\n\nYou have been removed as a beta tester for "
            "{display_name} at edx.org by a member of the course staff. "
            "The course will remain on your dashboard, but you will no longer "
            "be part of the beta testing group.\n\n"
            "Your other courses have not been affected.\n\n----\n"
            "This email was automatically sent from edx.org to {email_address}".format(
                display_name=self.course.display_name,
                full_name=self.beta_tester.profile.name,
                email_address=self.beta_tester.email
            )
        )


@attr(shard=1)
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
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_modify_access_bad_action(self):
        """ Test with an invalid action parameter. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'staff',
            'action': 'robot-not-an-action',
        })
        self.assertEqual(response.status_code, 400)

    def test_modify_access_bad_role(self):
        """ Test with an invalid action parameter. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'robot-not-a-roll',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 400)

    def test_modify_access_allow(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_user.email,
            'rolename': 'staff',
            'action': 'allow',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_allow_with_uname(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_instructor.username,
            'rolename': 'staff',
            'action': 'allow',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.email,
            'rolename': 'staff',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke_with_username(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'unique_student_identifier': self.other_staff.username,
            'rolename': 'staff',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_with_fake_user(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_modify_access_with_inactive_user(self):
        self.other_user.is_active = False
        self.other_user.save()  # pylint: disable=no-member
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_modify_access_revoke_not_allowed(self):
        """ Test revoking access that a user does not have. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        url = reverse('modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_list_course_role_members_noparams(self):
        """ Test missing all query parameters. """
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_bad_rolename(self):
        """ Test with an invalid rolename parameter. """
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'rolename': 'robot-not-a-rolename',
        })
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_staff(self):
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'rolename': 'staff',
        })
        self.assertEqual(response.status_code, 200)

        # check response content
        expected = {
            'course_id': self.course.id.to_deprecated_string(),
            'staff': [
                {
                    'username': self.other_staff.username,
                    'email': self.other_staff.email,
                    'first_name': self.other_staff.first_name,
                    'last_name': self.other_staff.last_name,
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_list_course_role_members_beta(self):
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'rolename': 'beta',
        })
        self.assertEqual(response.status_code, 200)

        # check response content
        expected = {
            'course_id': self.course.id.to_deprecated_string(),
            'beta': []
        }
        res_json = json.loads(response.content)
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
        url = reverse('update_forum_role_membership', kwargs={'course_id': self.course.id.to_deprecated_string()})
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


@attr(shard=1)
@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
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
        self.client.login(username=self.instructor.username, password='test')
        self.cart = Order.get_cart_for_user(self.instructor)
        self.coupon_code = 'abcde'
        self.coupon = Coupon(code=self.coupon_code, description='testing code', course_id=self.course.id,
                             percentage_discount=10, created_by=self.instructor, is_active=True)
        self.coupon.save()

        # Create testing invoice 1
        self.sale_invoice_1 = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName', company_contact_email='Test@company.com',
            recipient_name='Testw', recipient_email='test1@test.com', customer_reference_number='2Fwe23S',
            internal_reference="A", course_id=self.course.id, is_valid=True
        )
        self.invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.sale_invoice_1,
            qty=1,
            unit_price=1234.32,
            course_id=self.course.id
        )

        self.students = [UserFactory() for _ in xrange(6)]
        for student in self.students:
            CourseEnrollment.enroll(student, self.course.id)

        self.students_who_may_enroll = self.students + [UserFactory() for _ in range(5)]
        for student in self.students_who_may_enroll:
            CourseEnrollmentAllowed.objects.create(
                email=student.email, course_id=self.course.id
            )

    def register_with_redemption_code(self, user, code):
        """
        enroll user using a registration code
        """
        redeem_url = reverse('shoppingcart.views.register_code_redemption', args=[code], is_dashboard_endpoint=False)
        self.client.login(username=user.username, password='test')
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

    def test_invalidate_sale_record(self):
        """
        Testing the sale invalidating scenario.
        """
        for i in range(2):
            course_registration_code = CourseRegistrationCode(
                code='sale_invoice{}'.format(i),
                course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor,
                invoice=self.sale_invoice_1,
                invoice_item=self.invoice_item,
                mode_slug='honor'
            )
            course_registration_code.save()

        data = {'invoice_number': self.sale_invoice_1.id, 'event_type': "invalidate"}
        url = reverse('sale_validation', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url, method="POST", data=data)

        #Now try to fetch data against not existing invoice number
        test_data_1 = {'invoice_number': 100, 'event_type': "invalidate"}
        self.assert_request_status_code(404, url, method="POST", data=test_data_1)

        # Now invalidate the same invoice number and expect an Bad request
        response = self.assert_request_status_code(400, url, method="POST", data=data)
        self.assertIn("The sale associated with this invoice has already been invalidated.", response.content)

        # now re_validate the invoice number
        data['event_type'] = "re_validate"
        self.assert_request_status_code(200, url, method="POST", data=data)

        # Now re_validate the same active invoice number and expect an Bad request
        response = self.assert_request_status_code(400, url, method="POST", data=data)
        self.assertIn("This invoice is already active.", response.content)

        test_data_2 = {'invoice_number': self.sale_invoice_1.id}
        response = self.assert_request_status_code(400, url, method="POST", data=test_data_2)
        self.assertIn("Missing required event_type parameter", response.content)

        test_data_3 = {'event_type': "re_validate"}
        response = self.assert_request_status_code(400, url, method="POST", data=test_data_3)
        self.assertIn("Missing required invoice_number parameter", response.content)

        # submitting invalid invoice number
        data['invoice_number'] = 'testing'
        response = self.assert_request_status_code(400, url, method="POST", data=data)
        self.assertIn("invoice_number must be an integer, {value} provided".format(value=data['invoice_number']), response.content)

    def test_get_sale_order_records_features_csv(self):
        """
        Test that the response from get_sale_order_records is in csv format.
        """
        # add the coupon code for the course
        coupon = Coupon(
            code='test_code', description='test_description', course_id=self.course.id,
            percentage_discount='10', created_by=self.instructor, is_active=True
        )
        coupon.save()
        self.cart.order_type = 'business'
        self.cart.save()
        self.cart.add_billing_details(company_name='Test Company', company_contact_name='Test',
                                      company_contact_email='test@123', recipient_name='R1',
                                      recipient_email='', customer_reference_number='PO#23')

        paid_course_reg_item = PaidCourseRegistration.add_to_order(
            self.cart,
            self.course.id,
            mode_slug=CourseMode.HONOR
        )
        # update the quantity of the cart item paid_course_reg_item
        resp = self.client.post(
            reverse('shoppingcart.views.update_user_cart', is_dashboard_endpoint=False),
            {'ItemId': paid_course_reg_item.id, 'qty': '4'}
        )
        self.assertEqual(resp.status_code, 200)
        # apply the coupon code to the item in the cart
        resp = self.client.post(
            reverse('shoppingcart.views.use_code', is_dashboard_endpoint=False),
            {'code': coupon.code}
        )
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase()
        # get the updated item
        item = self.cart.orderitem_set.all().select_subclasses()[0]
        # get the redeemed coupon information
        coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(order=self.cart)

        sale_order_url = reverse('get_sale_order_records', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(sale_order_url)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('36', response.content.split('\r\n')[1])
        self.assertIn(str(item.unit_cost), response.content.split('\r\n')[1],)
        self.assertIn(str(item.list_price), response.content.split('\r\n')[1],)
        self.assertIn(item.status, response.content.split('\r\n')[1],)
        self.assertIn(coupon_redemption[0].coupon.code, response.content.split('\r\n')[1],)

    def test_coupon_redeem_count_in_ecommerce_section(self):
        """
        Test that checks the redeem count in the instructor_dashboard coupon section
        """
        # add the coupon code for the course
        coupon = Coupon(
            code='test_code', description='test_description', course_id=self.course.id,
            percentage_discount='10', created_by=self.instructor, is_active=True
        )
        coupon.save()

        # Coupon Redeem Count only visible for Financial Admins.
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)

        PaidCourseRegistration.add_to_order(self.cart, self.course.id)
        # apply the coupon code to the item in the cart
        resp = self.client.post(
            reverse('shoppingcart.views.use_code', is_dashboard_endpoint=False),
            {'code': coupon.code}
        )
        self.assertEqual(resp.status_code, 200)

        # URL for instructor dashboard
        instructor_dashboard = reverse(
            'instructor_dashboard',
            kwargs={'course_id': self.course.id.to_deprecated_string()},
            is_dashboard_endpoint=False
        )
        # visit the instructor dashboard page and
        # check that the coupon redeem count should be 0
        resp = self.client.get(instructor_dashboard)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Number Redeemed', resp.content)
        self.assertIn('<td>0</td>', resp.content)

        # now make the payment of your cart items
        self.cart.purchase()
        # visit the instructor dashboard page and
        # check that the coupon redeem count should be 1
        resp = self.client.get(instructor_dashboard)
        self.assertEqual(resp.status_code, 200)

        self.assertIn('Number Redeemed', resp.content)
        self.assertIn('<td>1</td>', resp.content)

    def test_get_sale_records_features_csv(self):
        """
        Test that the response from get_sale_records is in csv format.
        """
        for i in range(2):
            course_registration_code = CourseRegistrationCode(
                code='sale_invoice{}'.format(i),
                course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor,
                invoice=self.sale_invoice_1,
                invoice_item=self.invoice_item,
                mode_slug='honor'
            )
            course_registration_code.save()

        url = reverse(
            'get_sale_records',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        response = self.client.post(url + '/csv', {})
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_get_sale_records_features_json(self):
        """
        Test that the response from get_sale_records is in json format.
        """
        for i in range(5):
            course_registration_code = CourseRegistrationCode(
                code='sale_invoice{}'.format(i),
                course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor,
                invoice=self.sale_invoice_1,
                invoice_item=self.invoice_item,
                mode_slug='honor'
            )
            course_registration_code.save()

        url = reverse('get_sale_records', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        res_json = json.loads(response.content)
        self.assertIn('sale', res_json)

        for res in res_json['sale']:
            self.validate_sale_records_response(
                res,
                course_registration_code,
                self.sale_invoice_1,
                0,
                invoice_item=self.invoice_item
            )

    def test_get_sale_records_features_with_multiple_invoices(self):
        """
        Test that the response from get_sale_records is in json format for multiple invoices
        """
        for i in range(5):
            course_registration_code = CourseRegistrationCode(
                code='qwerty{}'.format(i),
                course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor,
                invoice=self.sale_invoice_1,
                invoice_item=self.invoice_item,
                mode_slug='honor'
            )
            course_registration_code.save()

        # Create test invoice 2
        sale_invoice_2 = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName', company_contact_email='Test@company.com',
            recipient_name='Testw_2', recipient_email='test2@test.com', customer_reference_number='2Fwe23S',
            internal_reference="B", course_id=self.course.id
        )

        invoice_item_2 = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=sale_invoice_2,
            qty=1,
            unit_price=1234.32,
            course_id=self.course.id
        )

        for i in range(5):
            course_registration_code = CourseRegistrationCode(
                code='xyzmn{}'.format(i), course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor, invoice=sale_invoice_2, invoice_item=invoice_item_2, mode_slug='honor'
            )
            course_registration_code.save()

        url = reverse('get_sale_records', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        res_json = json.loads(response.content)
        self.assertIn('sale', res_json)

        self.validate_sale_records_response(
            res_json['sale'][0],
            course_registration_code,
            self.sale_invoice_1,
            0,
            invoice_item=self.invoice_item
        )
        self.validate_sale_records_response(
            res_json['sale'][1],
            course_registration_code,
            sale_invoice_2,
            0,
            invoice_item=invoice_item_2
        )

    def validate_sale_records_response(self, res, course_registration_code, invoice, used_codes, invoice_item):
        """
        validate sale records attribute values with the response object
        """
        self.assertEqual(res['total_amount'], invoice.total_amount)
        self.assertEqual(res['recipient_email'], invoice.recipient_email)
        self.assertEqual(res['recipient_name'], invoice.recipient_name)
        self.assertEqual(res['company_name'], invoice.company_name)
        self.assertEqual(res['company_contact_name'], invoice.company_contact_name)
        self.assertEqual(res['company_contact_email'], invoice.company_contact_email)
        self.assertEqual(res['internal_reference'], invoice.internal_reference)
        self.assertEqual(res['customer_reference_number'], invoice.customer_reference_number)
        self.assertEqual(res['invoice_number'], invoice.id)
        self.assertEqual(res['created_by'], course_registration_code.created_by.username)
        self.assertEqual(res['course_id'], invoice_item.course_id.to_deprecated_string())
        self.assertEqual(res['total_used_codes'], used_codes)
        self.assertEqual(res['total_codes'], 5)

    def test_get_problem_responses_invalid_location(self):
        """
        Test whether get_problem_responses returns an appropriate status
        message when users submit an invalid problem location.
        """
        url = reverse(
            'get_problem_responses',
            kwargs={'course_id': unicode(self.course.id)}
        )
        problem_location = ''

        response = self.client.post(url, {'problem_location': problem_location})
        res_json = json.loads(response.content)
        self.assertEqual(res_json, 'Could not find problem with this location.')

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
            mock_problem_key = Mock(return_value=u'')
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
            kwargs={'course_id': unicode(self.course.id)}
        )
        problem_location = ''

        response = self.client.post(url, {'problem_location': problem_location})
        res_json = json.loads(response.content)
        self.assertIn('status', res_json)
        status = res_json['status']
        self.assertIn('is being created', status)
        self.assertNotIn('already in progress', status)

    @valid_problem_location
    def test_get_problem_responses_already_running(self):
        """
        Test whether get_problem_responses returns an appropriate status
        message if CSV generation is already in progress.
        """
        url = reverse(
            'get_problem_responses',
            kwargs={'course_id': unicode(self.course.id)}
        )

        with patch('instructor_task.api.submit_calculate_problem_responses_csv') as submit_task_function:
            error = AlreadyRunningError()
            submit_task_function.side_effect = error
            response = self.client.post(url, {})
            res_json = json.loads(response.content)
            self.assertIn('status', res_json)
            self.assertIn('already in progress', res_json['status'])

    def test_get_students_features(self):
        """
        Test that some minimum of information is formatted
        correctly in the response to get_students_features.
        """
        for student in self.students:
            student.profile.city = "Mos Eisley {}".format(student.id)
            student.profile.save()
        url = reverse('get_students_features', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        res_json = json.loads(response.content)
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
        url = reverse('get_students_features', kwargs={'course_id': unicode(self.course.id)})
        set_course_cohort_settings(self.course.id, is_cohorted=is_cohorted)

        response = self.client.post(url, {})
        res_json = json.loads(response.content)

        self.assertEqual('cohort' in res_json['feature_names'], is_cohorted)

    @ddt.data(True, False)
    def test_get_students_features_teams(self, has_teams):
        """
        Test that get_students_features includes team info when the course is
        has teams enabled, and does not when the course does not have teams enabled
        """
        if has_teams:
            self.course = CourseFactory.create(teams_configuration={
                'max_size': 2, 'topics': [{'topic-id': 'topic', 'name': 'Topic', 'description': 'A Topic'}]
            })
            course_instructor = InstructorFactory(course_key=self.course.id)
            self.client.login(username=course_instructor.username, password='test')

        url = reverse('get_students_features', kwargs={'course_id': unicode(self.course.id)})

        response = self.client.post(url, {})
        res_json = json.loads(response.content)

        self.assertEqual('team' in res_json['feature_names'], has_teams)

    def test_get_students_who_may_enroll(self):
        """
        Test whether get_students_who_may_enroll returns an appropriate
        status message when users request a CSV file of students who
        may enroll in a course.
        """
        url = reverse(
            'get_students_who_may_enroll',
            kwargs={'course_id': unicode(self.course.id)}
        )
        # Successful case:
        response = self.client.post(url, {})
        res_json = json.loads(response.content)
        self.assertIn('status', res_json)
        self.assertNotIn('currently being created', res_json['status'])
        # CSV generation already in progress:
        with patch('instructor_task.api.submit_calculate_may_enroll_csv') as submit_task_function:
            error = AlreadyRunningError()
            submit_task_function.side_effect = error
            response = self.client.post(url, {})
            res_json = json.loads(response.content)
            self.assertIn('status', res_json)
            self.assertIn('currently being created', res_json['status'])

    def test_get_student_exam_results(self):
        """
        Test whether get_proctored_exam_results returns an appropriate
        status message when users request a CSV file.
        """
        url = reverse(
            'get_proctored_exam_results',
            kwargs={'course_id': unicode(self.course.id)}
        )
        # Successful case:
        response = self.client.post(url, {})
        res_json = json.loads(response.content)
        self.assertIn('status', res_json)
        self.assertNotIn('currently being created', res_json['status'])
        # CSV generation already in progress:
        with patch('instructor_task.api.submit_proctored_exam_results_report') as submit_task_function:
            error = AlreadyRunningError()
            submit_task_function.side_effect = error
            response = self.client.post(url, {})
            res_json = json.loads(response.content)
            self.assertIn('status', res_json)
            self.assertIn('currently being created', res_json['status'])

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
        decorated_func(request, self.course.id.to_deprecated_string())
        self.assertTrue(func.called)

    def test_enrollment_report_features_csv(self):
        """
        test to generate enrollment report.
        enroll users, admin staff using registration codes.
        """
        InvoiceTransaction.objects.create(
            invoice=self.sale_invoice_1,
            amount=self.sale_invoice_1.total_amount,
            status='completed',
            created_by=self.instructor,
            last_modified_by=self.instructor
        )
        course_registration_code = CourseRegistrationCode.objects.create(
            code='abcde',
            course_id=self.course.id.to_deprecated_string(),
            created_by=self.instructor,
            invoice=self.sale_invoice_1,
            invoice_item=self.invoice_item,
            mode_slug='honor'
        )

        admin_user = AdminFactory()
        admin_cart = Order.get_cart_for_user(admin_user)
        PaidCourseRegistration.add_to_order(admin_cart, self.course.id)
        admin_cart.purchase()

        # create a new user/student and enroll
        # in the course using a registration code
        # and then validates the generated detailed enrollment report
        test_user = UserFactory()
        self.register_with_redemption_code(test_user, course_registration_code.code)

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        UserProfileFactory.create(user=self.students[0], meta='{"company": "asdasda"}')

        self.client.login(username=self.instructor.username, password='test')
        url = reverse('get_enrollment_report', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        self.assertIn('The detailed enrollment report is being created.', response.content)

    def test_bulk_purchase_detailed_report(self):
        """
        test to generate detailed enrollment report.
        1 Purchase registration codes.
        2 Enroll users via registration code.
        3 Validate generated enrollment report.
        """
        paid_course_reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course.id)
        # update the quantity of the cart item paid_course_reg_item
        resp = self.client.post(
            reverse('shoppingcart.views.update_user_cart', is_dashboard_endpoint=False),
            {'ItemId': paid_course_reg_item.id, 'qty': '4'}
        )
        self.assertEqual(resp.status_code, 200)
        # apply the coupon code to the item in the cart
        resp = self.client.post(
            reverse('shoppingcart.views.use_code', is_dashboard_endpoint=False),
            {'code': self.coupon_code}
        )
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase()

        course_reg_codes = CourseRegistrationCode.objects.filter(order=self.cart)
        self.register_with_redemption_code(self.instructor, course_reg_codes[0].code)

        test_user = UserFactory()
        test_user_cart = Order.get_cart_for_user(test_user)
        PaidCourseRegistration.add_to_order(test_user_cart, self.course.id)
        test_user_cart.purchase()
        InvoiceTransaction.objects.create(
            invoice=self.sale_invoice_1,
            amount=-self.sale_invoice_1.total_amount,
            status='refunded',
            created_by=self.instructor,
            last_modified_by=self.instructor
        )
        course_registration_code = CourseRegistrationCode.objects.create(
            code='abcde',
            course_id=self.course.id.to_deprecated_string(),
            created_by=self.instructor,
            invoice=self.sale_invoice_1,
            invoice_item=self.invoice_item,
            mode_slug='honor'
        )

        test_user1 = UserFactory()
        self.register_with_redemption_code(test_user1, course_registration_code.code)

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        self.client.login(username=self.instructor.username, password='test')

        url = reverse('get_enrollment_report', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        self.assertIn('The detailed enrollment report is being created.', response.content)

    def test_create_registration_code_without_invoice_and_order(self):
        """
        test generate detailed enrollment report,
        used a registration codes which has been created via invoice or bulk
        purchase scenario.
        """
        course_registration_code = CourseRegistrationCode.objects.create(
            code='abcde',
            course_id=self.course.id.to_deprecated_string(),
            created_by=self.instructor,
            mode_slug='honor'
        )
        test_user1 = UserFactory()
        self.register_with_redemption_code(test_user1, course_registration_code.code)

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        self.client.login(username=self.instructor.username, password='test')

        url = reverse('get_enrollment_report', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        self.assertIn('The detailed enrollment report is being created.', response.content)

    def test_invoice_payment_is_still_pending_for_registration_codes(self):
        """
        test generate enrollment report
        enroll a user in a course using registration code
        whose invoice has not been paid yet
        """
        course_registration_code = CourseRegistrationCode.objects.create(
            code='abcde',
            course_id=self.course.id.to_deprecated_string(),
            created_by=self.instructor,
            invoice=self.sale_invoice_1,
            invoice_item=self.invoice_item,
            mode_slug='honor'
        )

        test_user1 = UserFactory()
        self.register_with_redemption_code(test_user1, course_registration_code.code)

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        self.client.login(username=self.instructor.username, password='test')

        url = reverse('get_enrollment_report', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        self.assertIn('The detailed enrollment report is being created.', response.content)

    @patch.object(instructor.views.api, 'anonymous_id_for_user', Mock(return_value='42'))
    @patch.object(instructor.views.api, 'unique_id_for_user', Mock(return_value='41'))
    def test_get_anon_ids(self):
        """
        Test the CSV output for the anonymized user ids.
        """
        url = reverse('get_anon_ids', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(
            '"User ID","Anonymized User ID","Course Specific Anonymized User ID"'
            '\n"{user_id}","41","42"\n'.format(user_id=self.students[0].id)
        ))
        self.assertTrue(
            body.endswith('"{user_id}","41","42"\n'.format(user_id=self.students[-1].id))
        )

    def test_list_report_downloads(self):
        url = reverse('list_report_downloads', kwargs={'course_id': self.course.id.to_deprecated_string()})
        with patch('instructor_task.models.DjangoStorageReportStore.links_for') as mock_links_for:
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected_response)

    @ddt.data(*REPORTS_DATA)
    @ddt.unpack
    @valid_problem_location
    def test_calculate_report_csv_success(self, report_type, instructor_api_endpoint, task_api_endpoint, extra_instructor_api_kwargs):
        kwargs = {'course_id': unicode(self.course.id)}
        kwargs.update(extra_instructor_api_kwargs)
        url = reverse(instructor_api_endpoint, kwargs=kwargs)
        success_status = "The {report_type} report is being created.".format(report_type=report_type)
        if report_type == 'problem responses':
            with patch(task_api_endpoint):
                response = self.client.post(url, {'problem_location': ''})
            self.assertIn(success_status, response.content)
        else:
            CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
            with patch(task_api_endpoint):
                response = self.client.post(url, {})
            self.assertIn(success_status, response.content)

    @ddt.data(*EXECUTIVE_SUMMARY_DATA)
    @ddt.unpack
    def test_executive_summary_report_success(
            self,
            report_type,
            instructor_api_endpoint,
            task_api_endpoint,
            extra_instructor_api_kwargs
    ):
        kwargs = {'course_id': unicode(self.course.id)}
        kwargs.update(extra_instructor_api_kwargs)
        url = reverse(instructor_api_endpoint, kwargs=kwargs)

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        with patch(task_api_endpoint):
            response = self.client.post(url, {})
        success_status = "The {report_type} report is being created." \
                         " To view the status of the report, see Pending" \
                         " Tasks below".format(report_type=report_type)
        self.assertIn(success_status, response.content)

    @ddt.data(*EXECUTIVE_SUMMARY_DATA)
    @ddt.unpack
    def test_executive_summary_report_already_running(
            self,
            report_type,
            instructor_api_endpoint,
            task_api_endpoint,
            extra_instructor_api_kwargs
    ):
        kwargs = {'course_id': unicode(self.course.id)}
        kwargs.update(extra_instructor_api_kwargs)
        url = reverse(instructor_api_endpoint, kwargs=kwargs)

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        with patch(task_api_endpoint) as mock:
            mock.side_effect = AlreadyRunningError()
            response = self.client.post(url, {})
        already_running_status = "The {report_type} report is currently being created." \
                                 " To view the status of the report, see Pending Tasks below." \
                                 " You will be able to download the report" \
                                 " when it is" \
                                 " complete.".format(report_type=report_type)
        self.assertIn(already_running_status, response.content)

    def test_get_ora2_responses_success(self):
        url = reverse('export_ora2_data', kwargs={'course_id': unicode(self.course.id)})

        with patch('instructor_task.api.submit_export_ora2_data') as mock_submit_ora2_task:
            mock_submit_ora2_task.return_value = True
            response = self.client.post(url, {})
        success_status = "The ORA data report is being generated."
        self.assertIn(success_status, response.content)

    def test_get_ora2_responses_already_running(self):
        url = reverse('export_ora2_data', kwargs={'course_id': unicode(self.course.id)})

        with patch('instructor_task.api.submit_export_ora2_data') as mock_submit_ora2_task:
            mock_submit_ora2_task.side_effect = AlreadyRunningError()
            response = self.client.post(url, {})
        already_running_status = "An ORA data report generation task is already in progress."
        self.assertIn(already_running_status, response.content)

    def test_get_student_progress_url(self):
        """ Test that progress_url is in the successful response. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id.to_deprecated_string()})
        data = {'unique_student_identifier': self.students[0].email.encode("utf-8")}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertIn('progress_url', res_json)

    def test_get_student_progress_url_from_uname(self):
        """ Test that progress_url is in the successful response. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id.to_deprecated_string()})
        data = {'unique_student_identifier': self.students[0].username.encode("utf-8")}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertIn('progress_url', res_json)

    def test_get_student_progress_url_noparams(self):
        """ Test that the endpoint 404's without the required query params. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_get_student_progress_url_nostudent(self):
        """ Test that the endpoint 400's when requesting an unknown email. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)


@attr(shard=1)
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
        cls.problem_urlname = cls.problem_location.to_deprecated_string()

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
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_student_attempts_single(self):
        """ Test reset single student attempts. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
    @patch.object(instructor_task.api, 'submit_reset_problem_attempts_for_all_students')
    def test_reset_student_attempts_all(self, act):
        """ Test reset all student attempts. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_reset_student_attempts_missingmodule(self):
        """ Test reset for non-existant problem. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'problem_to_reset': 'robot-not-a-real-module',
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_student_attempts_delete(self):
        """ Test delete single student state. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 400)

    @patch.object(instructor_task.api, 'submit_rescore_problem_for_student')
    def test_rescore_problem_single(self, act):
        """ Test rescoring of a single student. """
        url = reverse('rescore_problem', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch.object(instructor_task.api, 'submit_rescore_problem_for_student')
    def test_rescore_problem_single_from_uname(self, act):
        """ Test rescoring of a single student. """
        url = reverse('rescore_problem', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.username,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch.object(instructor_task.api, 'submit_rescore_problem_for_all_students')
    def test_rescore_problem_all(self, act):
        """ Test rescoring for all students. """
        url = reverse('rescore_problem', kwargs={'course_id': self.course.id.to_deprecated_string()})
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
                      kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
            'delete_module': False,
        })
        self.assertEqual(response.status_code, 400)

    @patch.dict(settings.FEATURES, {'ENTRANCE_EXAMS': True})
    def test_rescore_entrance_exam_with_invalid_exam(self):
        """ Test course has entrance exam id set while re-scoring. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)


@attr(shard=1)
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
                      kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_entrance_exam_student_attempts_single(self):
        """ Test reset single student attempts for entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': unicode(self.course.id)})
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
    @patch.object(instructor_task.api, 'submit_reset_problem_attempts_in_entrance_exam')
    def test_reset_entrance_exam_all_student_attempts(self, act):
        """ Test reset all student attempts for entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_reset_student_attempts_invalid_entrance_exam(self):
        """ Test reset for invalid entrance exam. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': unicode(self.course_with_invalid_ee.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_entrance_exam_student_delete_state(self):
        """ Test delete single student entrance exam state. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': unicode(self.course.id)})
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
                      kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'delete_module': True,
        })
        self.assertEqual(response.status_code, 403)

    def test_entrance_exam_reset_student_attempts_nonsense(self):
        """ Test failure with both unique_student_identifier and all_students. """
        url = reverse('reset_student_attempts_for_entrance_exam',
                      kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 400)

    @patch.object(instructor_task.api, 'submit_rescore_entrance_exam_for_student')
    def test_rescore_entrance_exam_single_student(self, act):
        """ Test re-scoring of entrance exam for single student. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_rescore_entrance_exam_all_student(self):
        """ Test rescoring for all students. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'all_students': True,
        })
        self.assertEqual(response.status_code, 200)

    def test_rescore_entrance_exam_all_student_and_single(self):
        """ Test re-scoring with both all students and single student parameters. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_rescore_entrance_exam_with_invalid_exam(self):
        """ Test re-scoring of entrance exam with invalid exam. """
        url = reverse('rescore_entrance_exam', kwargs={'course_id': unicode(self.course_with_invalid_ee.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_list_entrance_exam_instructor_tasks_student(self):
        """ Test list task history for entrance exam AND student. """
        # create a re-score entrance exam task
        url = reverse('rescore_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)

        url = reverse('list_entrance_exam_instructor_tasks', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)

        # check response
        tasks = json.loads(response.content)['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['status'], _('Complete'))

    def test_list_entrance_exam_instructor_tasks_all_student(self):
        """ Test list task history for entrance exam AND all student. """
        url = reverse('list_entrance_exam_instructor_tasks', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        # check response
        tasks = json.loads(response.content)['tasks']
        self.assertEqual(len(tasks), 0)

    def test_list_entrance_exam_instructor_with_invalid_exam_key(self):
        """ Test list task history for entrance exam failure if course has invalid exam. """
        url = reverse('list_entrance_exam_instructor_tasks',
                      kwargs={'course_id': unicode(self.course_with_invalid_ee.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 400)

    def test_skip_entrance_exam_student(self):
        """ Test skip entrance exam api for student. """
        # create a re-score entrance exam task
        url = reverse('mark_student_can_skip_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })
        self.assertEqual(response.status_code, 200)
        # check response
        message = _('This student (%s) will skip the entrance exam.') % self.student.email
        self.assertContains(response, message)

        # post again with same student
        response = self.client.post(url, {
            'unique_student_identifier': self.student.email,
        })

        # This time response message should be different
        message = _('This student (%s) is already allowed to skip the entrance exam.') % self.student.email
        self.assertContains(response, message)


@attr(shard=1)
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestInstructorSendEmail(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
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
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 200)

    def test_send_email_but_not_logged_in(self):
        self.client.logout()
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 403)

    def test_send_email_but_not_staff(self):
        self.client.logout()
        student = UserFactory()
        self.client.login(username=student.username, password='test')
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, self.full_test_message)
        self.assertEqual(response.status_code, 403)

    def test_send_email_but_course_not_exist(self):
        url = reverse('send_email', kwargs={'course_id': 'GarbageCourse/DNE/NoTerm'})
        response = self.client.post(url, self.full_test_message)
        self.assertNotEqual(response.status_code, 200)

    def test_send_email_no_sendto(self):
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'subject': 'test subject',
            'message': 'test message',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_invalid_sendto(self):
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'send_to': '["invalid_target", "staff"]',
            'subject': 'test subject',
            'message': 'test message',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_no_subject(self):
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'send_to': '["staff"]',
            'message': 'test message',
        })
        self.assertEqual(response.status_code, 400)

    def test_send_email_no_message(self):
        url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'send_to': '["staff"]',
            'subject': 'test subject',
        })
        self.assertEqual(response.status_code, 400)


class MockCompletionInfo(object):
    """Mock for get_task_completion_info"""
    times_called = 0

    def mock_get_task_completion_info(self, *args):  # pylint: disable=unused-argument
        """Mock for get_task_completion_info"""
        self.times_called += 1
        if self.times_called % 2 == 0:
            return True, 'Task Completed'
        return False, 'Task Errored In Some Way'


@attr(shard=1)
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
        cls.problem_urlname = cls.problem_location.to_deprecated_string()

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
        self.tasks = [self.FakeTask(mock_factory.mock_get_task_completion_info) for _ in xrange(7)]
        self.tasks[-1].make_invalid_output()

    @patch.object(instructor_task.api, 'get_running_instructor_tasks')
    def test_list_instructor_tasks_running(self, act):
        """ Test list of all running tasks. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': self.course.id.to_deprecated_string()})
        mock_factory = MockCompletionInfo()
        with patch('instructor.views.instructor_task_helpers.get_task_completion_info') as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content)['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)
        self.assertEqual(actual_tasks, expected_tasks)

    @patch.object(instructor_task.api, 'get_instructor_task_history')
    def test_list_background_email_tasks(self, act):
        """Test list of background email tasks."""
        act.return_value = self.tasks
        url = reverse('list_background_email_tasks', kwargs={'course_id': self.course.id.to_deprecated_string()})
        mock_factory = MockCompletionInfo()
        with patch('instructor.views.instructor_task_helpers.get_task_completion_info') as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content)['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)
        self.assertEqual(actual_tasks, expected_tasks)

    @patch.object(instructor_task.api, 'get_instructor_task_history')
    def test_list_instructor_tasks_problem(self, act):
        """ Test list task history for problem. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': self.course.id.to_deprecated_string()})
        mock_factory = MockCompletionInfo()
        with patch('instructor.views.instructor_task_helpers.get_task_completion_info') as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {
                'problem_location_str': self.problem_urlname,
            })
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content)['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)
        self.assertEqual(actual_tasks, expected_tasks)

    @patch.object(instructor_task.api, 'get_instructor_task_history')
    def test_list_instructor_tasks_problem_student(self, act):
        """ Test list task history for problem AND student. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': self.course.id.to_deprecated_string()})
        mock_factory = MockCompletionInfo()
        with patch('instructor.views.instructor_task_helpers.get_task_completion_info') as mock_completion_info:
            mock_completion_info.side_effect = mock_factory.mock_get_task_completion_info
            response = self.client.post(url, {
                'problem_location_str': self.problem_urlname,
                'unique_student_identifier': self.student.email,
            })
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        actual_tasks = json.loads(response.content)['tasks']
        for exp_task, act_task in zip(expected_tasks, actual_tasks):
            self.assertDictEqual(exp_task, act_task)

        self.assertEqual(actual_tasks, expected_tasks)


@attr(shard=1)
@patch.object(instructor_task.api, 'get_instructor_task_history', autospec=True)
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
        task_history_request.return_value = self.tasks.values()
        url = reverse('list_email_content', kwargs={'course_id': self.course.id.to_deprecated_string()})
        with patch('instructor.views.api.CourseEmail.objects.get') as mock_email_info:
            mock_email_info.side_effect = self.get_matching_mock_email
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        return response

    def check_emails_sent(self, num_emails, task_history_request, with_failures=False):
        """ Tests sending emails with or without failures """
        response = self.get_email_content_response(num_emails, task_history_request, with_failures)
        self.assertTrue(task_history_request.called)
        expected_email_info = [email_info.to_dict() for email_info in self.emails_info.values()]
        actual_email_info = json.loads(response.content)['emails']

        self.assertEqual(len(actual_email_info), num_emails)
        for exp_email, act_email in zip(expected_email_info, actual_email_info):
            self.assertDictEqual(exp_email, act_email)

        self.assertEqual(expected_email_info, actual_email_info)

    def test_content_list_one_email(self, task_history_request):
        """ Test listing of bulk emails when email list has one email """
        response = self.get_email_content_response(1, task_history_request)
        self.assertTrue(task_history_request.called)
        email_info = json.loads(response.content)['emails']

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
        email_info = json.loads(response.content)['emails']

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
        url = reverse('list_email_content', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        self.assertTrue(task_history_request.called)
        returned_email_info = json.loads(response.content)['emails']
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
        url = reverse('list_email_content', kwargs={'course_id': self.course.id.to_deprecated_string()})
        with patch('instructor.views.api.CourseEmail.objects.get') as mock_email_info:
            mock_email_info.return_value = email
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        self.assertTrue(task_history_request.called)
        returned_info_list = json.loads(response.content)['emails']

        self.assertEqual(len(returned_info_list), 1)
        returned_info = returned_info_list[0]
        expected_info = email_info.to_dict()
        self.assertDictEqual(expected_info, returned_info)


@attr(shard=1)
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
        course_id = SlashSeparatedCourseKey('MITx', '6.002x', '2013_Spring')
        name = 'L2Node1'
        output = 'i4x://MITx/6.002x/problem/L2Node1'
        self.assertEqual(msk_from_problem_urlname(course_id, name).to_deprecated_string(), output)

    @raises(ValueError)
    def test_msk_from_problem_urlname_error(self):
        args = ('notagoodcourse', 'L2Node1')
        msk_from_problem_urlname(*args)


def get_extended_due(course, unit, user):
    """
    Gets the overridden due date for the given user on the given unit.  Returns
    `None` if there is no override set.
    """
    try:
        override = StudentFieldOverride.objects.get(
            course_id=course.id,
            student=user,
            location=unit.location,
            field='due'
        )
        return DATE_FIELD.from_json(json.loads(override.value))
    except StudentFieldOverride.DoesNotExist:
        return None


@attr(shard=1)
class TestDueDateExtensions(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test data dumps for reporting.
    """
    @classmethod
    def setUpClass(cls):
        super(TestDueDateExtensions, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)

        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            cls.week1 = ItemFactory.create(due=cls.due)
            cls.week2 = ItemFactory.create(due=cls.due)
            cls.week3 = ItemFactory.create()  # No due date
            cls.course.children = [
                cls.week1.location.to_deprecated_string(),
                cls.week2.location.to_deprecated_string(),
                cls.week3.location.to_deprecated_string()
            ]
            cls.homework = ItemFactory.create(
                parent_location=cls.week1.location,
                due=cls.due
            )
            cls.week1.children = [cls.homework.location.to_deprecated_string()]

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
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def test_change_due_date(self):
        url = reverse('change_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week1.location.to_deprecated_string(),
            'due_datetime': '12/30/2013 00:00'
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(datetime.datetime(2013, 12, 30, 0, 0, tzinfo=utc),
                         get_extended_due(self.course, self.week1, self.user1))

    def test_change_to_invalid_due_date(self):
        url = reverse('change_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week1.location.to_deprecated_string(),
            'due_datetime': '01/01/2009 00:00'
        })
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            None,
            get_extended_due(self.course, self.week1, self.user1)
        )

    def test_change_nonexistent_due_date(self):
        url = reverse('change_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week3.location.to_deprecated_string(),
            'due_datetime': '12/30/2013 00:00'
        })
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(
            None,
            get_extended_due(self.course, self.week3, self.user1)
        )

    def test_reset_date(self):
        self.test_change_due_date()
        url = reverse('reset_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week1.location.to_deprecated_string(),
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            None,
            get_extended_due(self.course, self.week1, self.user1)
        )

    def test_reset_nonexistent_extension(self):
        url = reverse('reset_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week1.location.to_deprecated_string(),
        })
        self.assertEqual(response.status_code, 400, response.content)

    def test_show_unit_extensions(self):
        self.test_change_due_date()
        url = reverse('show_unit_extensions',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'url': self.week1.location.to_deprecated_string()})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(json.loads(response.content), {
            u'data': [{u'Extended Due Date': u'2013-12-30 00:00',
                       u'Full Name': self.user1.profile.name,
                       u'Username': self.user1.username}],
            u'header': [u'Username', u'Full Name', u'Extended Due Date'],
            u'title': u'Users with due date extensions for %s' %
                      self.week1.display_name})

    def test_show_student_extensions(self):
        self.test_change_due_date()
        url = reverse('show_student_extensions',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'student': self.user1.username})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(json.loads(response.content), {
            u'data': [{u'Extended Due Date': u'2013-12-30 00:00',
                       u'Unit': self.week1.display_name}],
            u'header': [u'Unit', u'Extended Due Date'],
            u'title': u'Due date extensions for %s (%s)' % (
                self.user1.profile.name, self.user1.username)})


@attr(shard=1)
class TestDueDateExtensionsDeletedDate(ModuleStoreTestCase, LoginEnrollmentTestCase):
    def setUp(self):
        """
        Fixtures.
        """
        super(TestDueDateExtensionsDeletedDate, self).setUp()

        self.course = CourseFactory.create()
        self.due = datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)

        with self.store.bulk_operations(self.course.id, emit_signals=False):
            self.week1 = ItemFactory.create(due=self.due)
            self.week2 = ItemFactory.create(due=self.due)
            self.week3 = ItemFactory.create()  # No due date
            self.course.children = [
                self.week1.location.to_deprecated_string(),
                self.week2.location.to_deprecated_string(),
                self.week3.location.to_deprecated_string()
            ]
            self.homework = ItemFactory.create(
                parent_location=self.week1.location,
                due=self.due
            )
            self.week1.children = [self.homework.location.to_deprecated_string()]

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
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def test_reset_extension_to_deleted_date(self):
        """
        Test that we can delete a due date extension after deleting the normal
        due date, without causing an error.
        """

        url = reverse('change_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week1.location.to_deprecated_string(),
            'due_datetime': '12/30/2013 00:00'
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(datetime.datetime(2013, 12, 30, 0, 0, tzinfo=utc),
                         get_extended_due(self.course, self.week1, self.user1))

        self.week1.due = None
        self.week1 = self.store.update_item(self.week1, self.user1.id)
        # Now, week1's normal due date is deleted but the extension still exists.
        url = reverse('reset_due_date', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'student': self.user1.username,
            'url': self.week1.location.to_deprecated_string(),
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            None,
            get_extended_due(self.course, self.week1, self.user1)
        )


@attr(shard=1)
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
        url = reverse('get_issued_certificates', kwargs={'course_id': unicode(self.course.id)})
        # firstly generating downloadable certificates with 'honor' mode
        certificate_count = 3
        for __ in xrange(certificate_count):
            self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.generating)

        response = self.client.post(url)
        res_json = json.loads(response.content)
        self.assertIn('certificates', res_json)
        self.assertEqual(len(res_json['certificates']), 0)

        # Certificates with status 'downloadable' should be in response.
        self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.downloadable)
        response = self.client.post(url)
        res_json = json.loads(response.content)
        self.assertIn('certificates', res_json)
        self.assertEqual(len(res_json['certificates']), 1)

    def test_certificates_features_group_by_mode(self):
        """
        Test for certificate csv features against mode. Certificates should be group by 'mode' in reponse.
        """
        url = reverse('get_issued_certificates', kwargs={'course_id': unicode(self.course.id)})
        # firstly generating downloadable certificates with 'honor' mode
        certificate_count = 3
        for __ in xrange(certificate_count):
            self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.downloadable)

        response = self.client.post(url)
        res_json = json.loads(response.content)
        self.assertIn('certificates', res_json)
        self.assertEqual(len(res_json['certificates']), 1)

        # retrieve the first certificate from the list, there should be 3 certificates for 'honor' mode.
        certificate = res_json['certificates'][0]
        self.assertEqual(certificate.get('total_issued_certificate'), 3)
        self.assertEqual(certificate.get('mode'), 'honor')
        self.assertEqual(certificate.get('course_id'), str(self.course.id))

        # Now generating downloadable certificates with 'verified' mode
        for __ in xrange(certificate_count):
            self.generate_certificate(
                course_id=self.course.id,
                mode='verified',
                status=CertificateStatuses.downloadable
            )

        response = self.client.post(url)
        res_json = json.loads(response.content)
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
        url = reverse('get_issued_certificates', kwargs={'course_id': unicode(self.course.id)})
        # firstly generating downloadable certificates with 'honor' mode
        certificate_count = 3
        for __ in xrange(certificate_count):
            self.generate_certificate(course_id=self.course.id, mode='honor', status=CertificateStatuses.downloadable)

        current_date = datetime.date.today().strftime("%B %d, %Y")
        response = self.client.get(url, {'csv': 'true'})
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename={0}'.format('issued_certificates.csv'))
        self.assertEqual(
            response.content.strip(),
            '"CourseID","Certificate Type","Total Certificates Issued","Date Report Run"\r\n"'
            + str(self.course.id) + '","honor","3","' + current_date + '"'
        )


@attr(shard=1)
@override_settings(REGISTRATION_CODE_LENGTH=8)
class TestCourseRegistrationCodes(SharedModuleStoreTestCase):
    """
    Test data dumps for E-commerce Course Registration Codes.
    """
    @classmethod
    def setUpClass(cls):
        super(TestCourseRegistrationCodes, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.url = reverse(
            'generate_registration_codes',
            kwargs={'course_id': cls.course.id.to_deprecated_string()}
        )

    def setUp(self):
        """
        Fixtures.
        """
        super(TestCourseRegistrationCodes, self).setUp()

        CourseModeFactory.create(course_id=self.course.id, min_price=50)
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')
        CourseSalesAdminRole(self.course.id).add_users(self.instructor)

        data = {
            'total_registration_codes': 12, 'company_name': 'Test Group', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street',
            'address_line_2': '', 'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(self.url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        for i in range(5):
            order = Order(user=self.instructor, status='purchased')
            order.save()

        # Spent(used) Registration Codes
        for i in range(5):
            i += 1
            registration_code_redemption = RegistrationCodeRedemption(
                registration_code_id=i,
                redeemed_by=self.instructor
            )
            registration_code_redemption.save()

    @override_settings(FINANCE_EMAIL='finance@example.com')
    def test_finance_email_in_recipient_list_when_generating_registration_codes(self):
        """
        Test to verify that the invoice will also be sent to the FINANCE_EMAIL when
        generating registration codes
        """
        url_reg_code = reverse('generate_registration_codes',
                               kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 5, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 121.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': 'True'
        }

        response = self.client.post(url_reg_code, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        # check for the last mail.outbox, The FINANCE_EMAIL has been appended at the
        # very end, when generating registration codes
        self.assertEqual(mail.outbox[-1].to[0], 'finance@example.com')

    def test_user_invoice_copy_preference(self):
        """
        Test to remember user invoice copy preference
        """
        url_reg_code = reverse('generate_registration_codes',
                               kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 5, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 121.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': 'True'
        }

        # user invoice copy preference will be saved in api user preference; model
        response = self.client.post(url_reg_code, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')

        # get user invoice copy preference.
        url_user_invoice_preference = reverse('get_user_invoice_preference',
                                              kwargs={'course_id': self.course.id.to_deprecated_string()})

        response = self.client.post(url_user_invoice_preference, data)
        result = json.loads(response.content)
        self.assertEqual(result['invoice_copy'], True)

        # updating the user invoice copy preference during code generation flow
        data['invoice'] = ''
        response = self.client.post(url_reg_code, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')

        # get user invoice copy preference.
        url_user_invoice_preference = reverse('get_user_invoice_preference',
                                              kwargs={'course_id': self.course.id.to_deprecated_string()})

        response = self.client.post(url_user_invoice_preference, data)
        result = json.loads(response.content)
        self.assertEqual(result['invoice_copy'], False)

    def test_generate_course_registration_codes_csv(self):
        """
        Test to generate a response of all the generated course registration codes
        """
        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 15, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 17)

    def test_generate_course_registration_with_redeem_url_codes_csv(self):
        """
        Test to generate a response of all the generated course registration codes
        """
        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 15, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 17)
        rows = body.split('\n')
        index = 1
        while index < len(rows):
            if rows[index]:
                row_data = rows[index].split(',')
                code = row_data[0].replace('"', '')
                self.assertTrue(row_data[1].startswith('"http')
                                and row_data[1].endswith('/shoppingcart/register/redeem/{0}/"'.format(code)))
            index += 1

    @patch.object(instructor.views.api, 'random_code_generator',
                  Mock(side_effect=['first', 'second', 'third', 'fourth']))
    def test_generate_course_registration_codes_matching_existing_coupon_code(self):
        """
        Test the generated course registration code is already in the Coupon Table
        """
        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        coupon = Coupon(code='first', course_id=self.course.id.to_deprecated_string(), created_by=self.instructor)
        coupon.save()
        data = {
            'total_registration_codes': 3, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 5)  # 1 for headers, 1 for new line at the end and 3 for the actual data

    @patch.object(instructor.views.api, 'random_code_generator',
                  Mock(side_effect=['first', 'first', 'second', 'third']))
    def test_generate_course_registration_codes_integrity_error(self):
        """
       Test for the Integrity error against the generated code
        """
        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 2, 'company_name': 'Test Group', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 4)

    def test_spent_course_registration_codes_csv(self):
        """
        Test to generate a response of all the spent course registration codes
        """
        url = reverse('spent_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {'spent_company_name': ''}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')

        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))

        self.assertEqual(len(body.split('\n')), 7)

        generate_code_url = reverse(
            'generate_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )

        data = {
            'total_registration_codes': 9, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'unit_price': 122.45, 'company_contact_email': 'Test@company.com', 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(generate_code_url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

        for i in range(9):
            order = Order(user=self.instructor, status='purchased')
            order.save()

        # Spent(used) Registration Codes
        for i in range(9):
            i += 13
            registration_code_redemption = RegistrationCodeRedemption(
                registration_code_id=i,
                redeemed_by=self.instructor
            )
            registration_code_redemption.save()

        data = {'spent_company_name': 'Group Alpha'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 11)

    def test_active_course_registration_codes_csv(self):
        """
        Test to generate a response of all the active course registration codes
        """
        url = reverse('active_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {'active_company_name': ''}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 9)

        generate_code_url = reverse(
            'generate_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )

        data = {
            'total_registration_codes': 9, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(generate_code_url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

        data = {'active_company_name': 'Group Alpha'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 11)

    def test_get_all_course_registration_codes_csv(self):
        """
        Test to generate a response of all the course registration codes
        """
        url = reverse(
            'get_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )

        data = {'download_company_name': ''}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 14)

        generate_code_url = reverse(
            'generate_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )

        data = {
            'total_registration_codes': 9, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(generate_code_url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

        data = {'download_company_name': 'Group Alpha'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))
        self.assertEqual(len(body.split('\n')), 11)

    def test_pdf_file_throws_exception(self):
        """
        test to mock the pdf file generation throws an exception
        when generating registration codes.
        """
        generate_code_url = reverse(
            'generate_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'total_registration_codes': 9, 'company_name': 'Group Alpha', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }
        with patch.object(PDFInvoice, 'generate_pdf', side_effect=Exception):
            response = self.client.post(generate_code_url, data)
            self.assertEqual(response.status_code, 200, response.content)

    def test_get_codes_with_sale_invoice(self):
        """
        Test to generate a response of all the course registration codes
        """
        generate_code_url = reverse(
            'generate_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )

        data = {
            'total_registration_codes': 5.5, 'company_name': 'Group Invoice', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': True
        }

        response = self.client.post(generate_code_url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

        url = reverse('get_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})
        data = {'download_company_name': 'Group Invoice'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_CSV_HEADER))

    def test_with_invalid_unit_price(self):
        """
        Test to generate a response of all the course registration codes
        """
        generate_code_url = reverse(
            'generate_registration_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )

        data = {
            'total_registration_codes': 10, 'company_name': 'Group Invoice', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 'invalid', 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': True
        }

        response = self.client.post(generate_code_url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn('Could not parse amount as', response.content)

    def test_get_historical_coupon_codes(self):
        """
        Test to download a response of all the active coupon codes
        """
        get_coupon_code_url = reverse(
            'get_coupon_codes', kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        for i in range(10):
            coupon = Coupon(
                code='test_code{0}'.format(i), description='test_description', course_id=self.course.id,
                percentage_discount='{0}'.format(i), created_by=self.instructor, is_active=True
            )
            coupon.save()

        #now create coupons with the expiration dates
        for i in range(5):
            coupon = Coupon(
                code='coupon{0}'.format(i), description='test_description', course_id=self.course.id,
                percentage_discount='{0}'.format(i), created_by=self.instructor, is_active=True,
                expiration_date=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=2)
            )
            coupon.save()

        response = self.client.post(get_coupon_code_url)
        self.assertEqual(response.status_code, 200, response.content)
        # filter all the coupons
        for coupon in Coupon.objects.all():
            self.assertIn(
                '"{coupon_code}","{course_id}","{discount}","{description}","{expiration_date}","{is_active}",'
                '"{code_redeemed_count}","{total_discounted_seats}","{total_discounted_amount}"'.format(
                    coupon_code=coupon.code,
                    course_id=coupon.course_id,
                    discount=coupon.percentage_discount,
                    description=coupon.description,
                    expiration_date=coupon.display_expiry_date,
                    is_active=coupon.is_active,
                    code_redeemed_count="0",
                    total_discounted_seats="0",
                    total_discounted_amount="0",
                ), response.content
            )

        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith(EXPECTED_COUPON_CSV_HEADER))


@attr(shard=1)
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
            file_pointer.write(csv_data.encode('utf-8'))
        with open(file_name, 'r') as file_pointer:
            url = reverse('add_users_to_cohorts', kwargs={'course_id': unicode(self.course.id)})
            return self.client.post(url, {'uploaded-file': file_pointer})

    def expect_error_on_file_content(self, file_content, error, file_suffix='.csv'):
        """
        Verify that we get the error we expect for a given file input.
        """
        self.client.login(username=self.staff_user.username, password='test')
        response = self.call_add_users_to_cohorts(file_content, suffix=file_suffix)
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
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

    @patch('instructor.views.api.instructor_task.api.submit_cohort_students')
    @patch('instructor.views.api.store_uploaded_file')
    def test_success_username(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call a background task when
        the CSV has username and cohort columns.
        """
        self.verify_success_on_file_content(
            'username,cohort\nfoo_username,bar_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('instructor.views.api.instructor_task.api.submit_cohort_students')
    @patch('instructor.views.api.store_uploaded_file')
    def test_success_email(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when the CSV has email and cohort columns.
        """
        self.verify_success_on_file_content(
            'email,cohort\nfoo_email,bar_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('instructor.views.api.instructor_task.api.submit_cohort_students')
    @patch('instructor.views.api.store_uploaded_file')
    def test_success_username_and_email(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when the CSV has username, email and cohort columns.
        """
        self.verify_success_on_file_content(
            'username,email,cohort\nfoo_username,bar_email,baz_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('instructor.views.api.instructor_task.api.submit_cohort_students')
    @patch('instructor.views.api.store_uploaded_file')
    def test_success_carriage_return(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when lines in the CSV are delimited by carriage returns.
        """
        self.verify_success_on_file_content(
            'username,email,cohort\rfoo_username,bar_email,baz_cohort', mock_store_upload, mock_cohort_task
        )

    @patch('instructor.views.api.instructor_task.api.submit_cohort_students')
    @patch('instructor.views.api.store_uploaded_file')
    def test_success_carriage_return_line_feed(self, mock_store_upload, mock_cohort_task):
        """
        Verify that we store the input CSV and call the cohorting background
        task when lines in the CSV are delimited by carriage returns and line
        feeds.
        """
        self.verify_success_on_file_content(
            'username,email,cohort\r\nfoo_username,bar_email,baz_cohort', mock_store_upload, mock_cohort_task
        )
