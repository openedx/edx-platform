# -*- coding: utf-8 -*-

"""
Unit tests for LMS instructor-initiated background tasks helper functions.

Tests that CSV grade report generation works with unicode emails.

"""
import ddt
from mock import Mock, patch
import tempfile
import unicodecsv
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from certificates.models import CertificateStatuses
from certificates.tests.factories import GeneratedCertificateFactory, CertificateWhitelistFactory
from course_modes.models import CourseMode
from courseware.tests.factories import InstructorFactory
from instructor_task.tests.test_base import InstructorTaskCourseTestCase, TestReportMixin, InstructorTaskModuleTestCase
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
import openedx.core.djangoapps.user_api.course_tag.api as course_tag_api
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from shoppingcart.models import Order, PaidCourseRegistration, CourseRegistrationCode, Invoice, \
    CourseRegistrationCodeInvoiceItem, InvoiceTransaction, Coupon
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment, CourseEnrollmentAllowed, ManualEnrollmentAudit, ALLOWEDTOENROLL_TO_ENROLLED
from verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition
from instructor_task.models import ReportStore
from instructor_task.tasks_helper import (
    cohort_students_and_upload,
    upload_grades_csv,
    upload_problem_grade_report,
    upload_students_csv,
    upload_may_enroll_csv,
    upload_enrollment_report,
    upload_exec_summary_report,
    generate_students_certificates,
)
from openedx.core.djangoapps.util.testing import ContentGroupTestCase, TestConditionalContent


@ddt.ddt
class TestInstructorGradeReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV grade report generation works.
    """
    def setUp(self):
        super(TestInstructorGradeReport, self).setUp()
        self.course = CourseFactory.create()

    @ddt.data([u'student@example.com', u'ni\xf1o@example.com'])
    def test_unicode_emails(self, emails):
        """
        Test that students with unicode characters in emails is handled.
        """
        for i, email in enumerate(emails):
            self.create_student('student{0}'.format(i), email)

        self.current_task = Mock()
        self.current_task.update_state = Mock()
        with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task
            result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        num_students = len(emails)
        self.assertDictContainsSubset({'attempted': num_students, 'succeeded': num_students, 'failed': 0}, result)

    @patch('instructor_task.tasks_helper._get_current_task')
    @patch('instructor_task.tasks_helper.iterate_grades_for')
    def test_grading_failure(self, mock_iterate_grades_for, _mock_current_task):
        """
        Test that any grading errors are properly reported in the
        progress dict and uploaded to the report store.
        """
        # mock an error response from `iterate_grades_for`
        mock_iterate_grades_for.return_value = [
            (self.create_student('username', 'student@example.com'), {}, 'Cannot grade student')
        ]
        result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 0, 'failed': 1}, result)

        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        self.assertTrue(any('grade_report_err' in item[0] for item in report_store.links_for(self.course.id)))

    def _verify_cell_data_for_user(self, username, course_id, column_header, expected_cell_content):
        """
        Verify cell data in the grades CSV for a particular user.
        """
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_grades_csv(None, None, course_id, None, 'graded')
            self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
            report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
            report_csv_filename = report_store.links_for(course_id)[0][0]
            with open(report_store.path_to(course_id, report_csv_filename)) as csv_file:
                for row in unicodecsv.DictReader(csv_file):
                    if row.get('username') == username:
                        self.assertEqual(row[column_header], expected_cell_content)

    def test_cohort_data_in_grading(self):
        """
        Test that cohort data is included in grades csv if cohort configuration is enabled for course.
        """
        cohort_groups = ['cohort 1', 'cohort 2']
        course = CourseFactory.create(cohort_config={'cohorted': True, 'auto_cohort': True,
                                                     'auto_cohort_groups': cohort_groups})

        user_1 = 'user_1'
        user_2 = 'user_2'
        CourseEnrollment.enroll(UserFactory.create(username=user_1), course.id)
        CourseEnrollment.enroll(UserFactory.create(username=user_2), course.id)

        # In auto cohorting a group will be assigned to a user only when user visits a problem
        # In grading calculation we only add a group in csv if group is already assigned to
        # user rather than creating a group automatically at runtime
        self._verify_cell_data_for_user(user_1, course.id, 'Cohort Name', '')
        self._verify_cell_data_for_user(user_2, course.id, 'Cohort Name', '')

    def test_unicode_cohort_data_in_grading(self):
        """
        Test that cohorts can contain unicode characters.
        """
        course = CourseFactory.create(cohort_config={'cohorted': True})

        # Create users and manually assign cohorts
        user1 = UserFactory.create(username='user1')
        user2 = UserFactory.create(username='user2')
        CourseEnrollment.enroll(user1, course.id)
        CourseEnrollment.enroll(user2, course.id)
        professor_x = u'ÞrÖfessÖr X'
        magneto = u'MàgnëtÖ'
        cohort1 = CohortFactory(course_id=course.id, name=professor_x)
        cohort2 = CohortFactory(course_id=course.id, name=magneto)
        cohort1.users.add(user1)
        cohort2.users.add(user2)

        self._verify_cell_data_for_user(user1.username, course.id, 'Cohort Name', professor_x)
        self._verify_cell_data_for_user(user2.username, course.id, 'Cohort Name', magneto)

    def test_unicode_user_partitions(self):
        """
        Test that user partition groups can contain unicode characters.
        """
        user_groups = [u'ÞrÖfessÖr X', u'MàgnëtÖ']
        user_partition = UserPartition(
            0,
            'x_man',
            'X Man',
            [
                Group(0, user_groups[0]),
                Group(1, user_groups[1])
            ]
        )

        # Create course with group configurations
        self.initialize_course(
            course_factory_kwargs={
                'user_partitions': [user_partition]
            }
        )

        _groups = [group.name for group in self.course.user_partitions[0].groups]
        self.assertEqual(_groups, user_groups)

    def test_cohort_scheme_partition(self):
        """
        Test that cohort-schemed user partitions are ignored in the
        grades export.
        """
        # Set up a course with 'cohort' and 'random' user partitions.
        cohort_scheme_partition = UserPartition(
            0,
            'Cohort-schemed Group Configuration',
            'Group Configuration based on Cohorts',
            [Group(0, 'Group A'), Group(1, 'Group B')],
            scheme_id='cohort'
        )
        experiment_group_a = Group(2, u'Expériment Group A')
        experiment_group_b = Group(3, u'Expériment Group B')
        experiment_partition = UserPartition(
            1,
            u'Content Expériment Configuration',
            u'Group Configuration for Content Expériments',
            [experiment_group_a, experiment_group_b],
            scheme_id='random'
        )
        course = CourseFactory.create(
            cohort_config={'cohorted': True},
            user_partitions=[cohort_scheme_partition, experiment_partition]
        )

        # Create user_a and user_b which are enrolled in the course
        # and assigned to experiment_group_a and experiment_group_b,
        # respectively.
        user_a = UserFactory.create(username='user_a')
        user_b = UserFactory.create(username='user_b')
        CourseEnrollment.enroll(user_a, course.id)
        CourseEnrollment.enroll(user_b, course.id)
        course_tag_api.set_course_tag(
            user_a,
            course.id,
            RandomUserPartitionScheme.key_for_partition(experiment_partition),
            experiment_group_a.id
        )
        course_tag_api.set_course_tag(
            user_b,
            course.id,
            RandomUserPartitionScheme.key_for_partition(experiment_partition),
            experiment_group_b.id
        )

        # Assign user_a to a group in the 'cohort'-schemed user
        # partition (by way of a cohort) to verify that the user
        # partition group does not show up in the "Experiment Group"
        # cell.
        cohort_a = CohortFactory.create(course_id=course.id, name=u'Cohørt A', users=[user_a])
        CourseUserGroupPartitionGroup(
            course_user_group=cohort_a,
            partition_id=cohort_scheme_partition.id,
            group_id=cohort_scheme_partition.groups[0].id
        ).save()

        # Verify that we see user_a and user_b in their respective
        # content experiment groups, and that we do not see any
        # content groups.
        experiment_group_message = u'Experiment Group ({content_experiment})'
        self._verify_cell_data_for_user(
            user_a.username,
            course.id,
            experiment_group_message.format(
                content_experiment=experiment_partition.name
            ),
            experiment_group_a.name
        )
        self._verify_cell_data_for_user(
            user_b.username,
            course.id,
            experiment_group_message.format(
                content_experiment=experiment_partition.name
            ),
            experiment_group_b.name
        )

        # Make sure cohort info is correct.
        cohort_name_header = 'Cohort Name'
        self._verify_cell_data_for_user(
            user_a.username,
            course.id,
            cohort_name_header,
            cohort_a.name
        )
        self._verify_cell_data_for_user(
            user_b.username,
            course.id,
            cohort_name_header,
            ''
        )

    @patch('instructor_task.tasks_helper._get_current_task')
    @patch('instructor_task.tasks_helper.iterate_grades_for')
    def test_unicode_in_csv_header(self, mock_iterate_grades_for, _mock_current_task):
        """
        Tests that CSV grade report works if unicode in headers.
        """
        # mock a response from `iterate_grades_for`
        mock_iterate_grades_for.return_value = [
            (
                self.create_student('username', 'student@example.com'),
                {'section_breakdown': [{'label': u'\u8282\u540e\u9898 01'}], 'percent': 0, 'grade': None},
                'Cannot grade student'
            )
        ]
        result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)


@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class TestInstructorDetailedEnrollmentReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV detailed enrollment generation works.
    """
    def setUp(self):
        super(TestInstructorDetailedEnrollmentReport, self).setUp()
        self.course = CourseFactory.create()

        # create testing invoice 1
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.sale_invoice_1 = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName',
            company_contact_email='Test@company.com',
            recipient_name='Testw', recipient_email='test1@test.com', customer_reference_number='2Fwe23S',
            internal_reference="A", course_id=self.course.id, is_valid=True
        )
        self.invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.sale_invoice_1,
            qty=1,
            unit_price=1234.32,
            course_id=self.course.id
        )

    def test_success(self):
        self.create_student('student', 'student@example.com')
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')

        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)

    def test_student_paid_course_enrollment_report(self):
        """
        test to check the paid user enrollment csv report status
        and enrollment source.
        """
        student = UserFactory()
        student_cart = Order.get_cart_for_user(student)
        PaidCourseRegistration.add_to_order(student_cart, self.course.id)
        student_cart.purchase()

        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_cell_data_in_csv(student.username, 'Enrollment Source', 'Credit Card - Individual')
        self._verify_cell_data_in_csv(student.username, 'Payment Status', 'purchased')

    def test_student_manually_enrolled_in_detailed_enrollment_source(self):
        """
        test to check the manually enrolled user enrollment report status
        and enrollment source.
        """
        student = UserFactory()
        enrollment = CourseEnrollment.enroll(student, self.course.id)
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.instructor, student.email, ALLOWEDTOENROLL_TO_ENROLLED,
            'manually enrolling unenrolled user', enrollment
        )

        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')

        enrollment_source = u'manually enrolled by user_id {user_id}, enrollment state transition: {transition}'.format(
            user_id=self.instructor.id, transition=ALLOWEDTOENROLL_TO_ENROLLED)  # pylint: disable=no-member
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_cell_data_in_csv(student.username, 'Enrollment Source', enrollment_source)
        self._verify_cell_data_in_csv(student.username, 'Payment Status', 'TBD')

    def test_student_used_enrollment_code_for_course_enrollment(self):
        """
        test to check the user enrollment source and payment status in the
        enrollment detailed report
        """
        student = UserFactory()
        self.client.login(username=student.username, password='test')
        student_cart = Order.get_cart_for_user(student)
        paid_course_reg_item = PaidCourseRegistration.add_to_order(student_cart, self.course.id)
        # update the quantity of the cart item paid_course_reg_item
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'),
                                {'ItemId': paid_course_reg_item.id, 'qty': '4'})
        self.assertEqual(resp.status_code, 200)
        student_cart.purchase()

        course_reg_codes = CourseRegistrationCode.objects.filter(order=student_cart)
        redeem_url = reverse('register_code_redemption', args=[course_reg_codes[0].code])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertTrue('Activate Course Enrollment' in response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_cell_data_in_csv(student.username, 'Enrollment Source', 'Used Registration Code')
        self._verify_cell_data_in_csv(student.username, 'Payment Status', 'purchased')

    def test_student_used_invoice_unpaid_enrollment_code_for_course_enrollment(self):
        """
        test to check the user enrollment source and payment status in the
        enrollment detailed report
        """
        student = UserFactory()
        self.client.login(username=student.username, password='test')

        course_registration_code = CourseRegistrationCode(
            code='abcde',
            course_id=self.course.id.to_deprecated_string(),
            created_by=self.instructor,
            invoice=self.sale_invoice_1,
            invoice_item=self.invoice_item,
            mode_slug='honor'
        )
        course_registration_code.save()

        redeem_url = reverse('register_code_redemption', args=['abcde'])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertTrue('Activate Course Enrollment' in response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_cell_data_in_csv(student.username, 'Enrollment Source', 'Used Registration Code')
        self._verify_cell_data_in_csv(student.username, 'Payment Status', 'Invoice Outstanding')

    def test_student_used_invoice_paid_enrollment_code_for_course_enrollment(self):
        """
        test to check the user enrollment source and payment status in the
        enrollment detailed report
        """
        student = UserFactory()
        self.client.login(username=student.username, password='test')
        invoice_transaction = InvoiceTransaction(
            invoice=self.sale_invoice_1,
            amount=self.sale_invoice_1.total_amount,
            status='completed',
            created_by=self.instructor,
            last_modified_by=self.instructor
        )
        invoice_transaction.save()
        course_registration_code = CourseRegistrationCode(
            code='abcde',
            course_id=self.course.id.to_deprecated_string(),
            created_by=self.instructor,
            invoice=self.sale_invoice_1,
            invoice_item=self.invoice_item,
            mode_slug='honor'
        )
        course_registration_code.save()

        redeem_url = reverse('register_code_redemption', args=['abcde'])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertTrue('Activate Course Enrollment' in response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_cell_data_in_csv(student.username, 'Enrollment Source', 'Used Registration Code')
        self._verify_cell_data_in_csv(student.username, 'Payment Status', 'Invoice Paid')

    def _verify_cell_data_in_csv(self, username, column_header, expected_cell_content):
        """
        Verify that the last ReportStore CSV contains the expected content.
        """
        report_store = ReportStore.from_config(config_name='FINANCIAL_REPORTS')
        report_csv_filename = report_store.links_for(self.course.id)[0][0]
        with open(report_store.path_to(self.course.id, report_csv_filename)) as csv_file:
            # Expand the dict reader generator so we don't lose it's content
            for row in unicodecsv.DictReader(csv_file):
                if row.get('Username') == username:
                    self.assertEqual(row[column_header], expected_cell_content)


@ddt.ddt
class TestProblemGradeReport(TestReportMixin, InstructorTaskModuleTestCase):
    """
    Test that the problem CSV generation works.
    """
    def setUp(self):
        super(TestProblemGradeReport, self).setUp()
        self.initialize_course()
        # Add unicode data to CSV even though unicode usernames aren't
        # technically possible in openedx.
        self.student_1 = self.create_student(u'üser_1')
        self.student_2 = self.create_student(u'üser_2')
        self.csv_header_row = [u'Student ID', u'Email', u'Username', u'Final Grade']

    @patch('instructor_task.tasks_helper._get_current_task')
    def test_no_problems(self, _get_current_task):
        """
        Verify that we see no grade information for a course with no graded
        problems.
        """
        result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'action_name': 'graded', 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv([
            dict(zip(
                self.csv_header_row,
                [unicode(self.student_1.id), self.student_1.email, self.student_1.username, '0.0']
            )),
            dict(zip(
                self.csv_header_row,
                [unicode(self.student_2.id), self.student_2.email, self.student_2.username, '0.0']
            ))
        ])

    @patch('instructor_task.tasks_helper._get_current_task')
    def test_single_problem(self, _get_current_task):
        vertical = ItemFactory.create(
            parent_location=self.problem_section.location,
            category='vertical',
            metadata={'graded': True},
            display_name='Problem Vertical'
        )
        self.define_option_problem(u'Pröblem1', parent=vertical)

        self.submit_student_answer(self.student_1.username, u'Pröblem1', ['Option 1'])
        result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'action_name': 'graded', 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        problem_name = u'Homework 1: Problem - Pröblem1'
        header_row = self.csv_header_row + [problem_name + ' (Earned)', problem_name + ' (Possible)']
        self.verify_rows_in_csv([
            dict(zip(
                header_row,
                [
                    unicode(self.student_1.id),
                    self.student_1.email,
                    self.student_1.username,
                    '0.01', '1.0', '2.0']
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.student_2.id),
                    self.student_2.email,
                    self.student_2.username,
                    '0.0', 'N/A', 'N/A'
                ]
            ))
        ])

    @patch('instructor_task.tasks_helper._get_current_task')
    @patch('instructor_task.tasks_helper.iterate_grades_for')
    @ddt.data(u'Cannöt grade student', '')
    def test_grading_failure(self, error_message, mock_iterate_grades_for, _mock_current_task):
        """
        Test that any grading errors are properly reported in the progress
        dict and uploaded to the report store.
        """
        # mock an error response from `iterate_grades_for`
        student = self.create_student(u'username', u'student@example.com')
        mock_iterate_grades_for.return_value = [
            (student, {}, error_message)
        ]
        result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 0, 'failed': 1}, result)

        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        self.assertTrue(any('grade_report_err' in item[0] for item in report_store.links_for(self.course.id)))
        self.verify_rows_in_csv([
            {
                u'Student ID': unicode(student.id),
                u'Email': student.email,
                u'Username': student.username,
                u'error_msg': error_message if error_message else "Unknown error"
            }
        ])


class TestProblemReportSplitTestContent(TestReportMixin, TestConditionalContent, InstructorTaskModuleTestCase):
    """
    Test the problem report on a course that has split tests.
    """

    OPTION_1 = 'Option 1'
    OPTION_2 = 'Option 2'

    def setUp(self):
        super(TestProblemReportSplitTestContent, self).setUp()
        self.problem_a_url = u'pröblem_a_url'
        self.problem_b_url = u'pröblem_b_url'
        self.define_option_problem(self.problem_a_url, parent=self.vertical_a)
        self.define_option_problem(self.problem_b_url, parent=self.vertical_b)

    def test_problem_grade_report(self):
        """
        Test that we generate the correct the correct grade report when dealing with A/B tests.

        In order to verify that the behavior of the grade report is correct, we submit answers for problems
        that the student won't have access to. A/B tests won't restrict access to the problems, but it should
        not show up in that student's course tree when generating the grade report, hence the N/A's in the grade report.
        """
        # student A will get 100%, student B will get 50% because
        # OPTION_1 is the correct option, and OPTION_2 is the
        # incorrect option
        self.submit_student_answer(self.student_a.username, self.problem_a_url, [self.OPTION_1, self.OPTION_1])
        self.submit_student_answer(self.student_a.username, self.problem_b_url, [self.OPTION_1, self.OPTION_1])

        self.submit_student_answer(self.student_b.username, self.problem_a_url, [self.OPTION_1, self.OPTION_2])
        self.submit_student_answer(self.student_b.username, self.problem_b_url, [self.OPTION_1, self.OPTION_2])

        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
            self.assertDictContainsSubset(
                {'action_name': 'graded', 'attempted': 2, 'succeeded': 2, 'failed': 0}, result
            )

        problem_names = [u'Homework 1: Problem - pröblem_a_url', u'Homework 1: Problem - pröblem_b_url']
        header_row = [u'Student ID', u'Email', u'Username', u'Final Grade']
        for problem in problem_names:
            header_row += [problem + ' (Earned)', problem + ' (Possible)']

        self.verify_rows_in_csv([
            dict(zip(
                header_row,
                [
                    unicode(self.student_a.id),
                    self.student_a.email,
                    self.student_a.username,
                    u'1.0', u'2.0', u'2.0', u'N/A', u'N/A'
                ]
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.student_b.id),
                    self.student_b.email,
                    self.student_b.username, u'0.5', u'N/A', u'N/A', u'1.0', u'2.0'
                ]
            ))
        ])


class TestProblemReportCohortedContent(TestReportMixin, ContentGroupTestCase, InstructorTaskModuleTestCase):
    """
    Test the problem report on a course that has cohorted content.
    """
    def setUp(self):
        super(TestProblemReportCohortedContent, self).setUp()
        # contstruct cohorted problems to work on.
        self.add_course_content()
        vertical = ItemFactory.create(
            parent_location=self.problem_section.location,
            category='vertical',
            metadata={'graded': True},
            display_name='Problem Vertical'
        )
        self.define_option_problem(
            u"Pröblem0",
            parent=vertical,
            group_access={self.course.user_partitions[0].id: [self.course.user_partitions[0].groups[0].id]}
        )
        self.define_option_problem(
            u"Pröblem1",
            parent=vertical,
            group_access={self.course.user_partitions[0].id: [self.course.user_partitions[0].groups[1].id]}
        )

    def test_cohort_content(self):
        self.submit_student_answer(self.alpha_user.username, u'Pröblem0', ['Option 1', 'Option 1'])
        resp = self.submit_student_answer(self.alpha_user.username, u'Pröblem1', ['Option 1', 'Option 1'])
        self.assertEqual(resp.status_code, 404)

        resp = self.submit_student_answer(self.beta_user.username, u'Pröblem0', ['Option 1', 'Option 2'])
        self.assertEqual(resp.status_code, 404)
        self.submit_student_answer(self.beta_user.username, u'Pröblem1', ['Option 1', 'Option 2'])

        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
            self.assertDictContainsSubset(
                {'action_name': 'graded', 'attempted': 4, 'succeeded': 4, 'failed': 0}, result
            )

        problem_names = [u'Homework 1: Problem - Pröblem0', u'Homework 1: Problem - Pröblem1']
        header_row = [u'Student ID', u'Email', u'Username', u'Final Grade']
        for problem in problem_names:
            header_row += [problem + ' (Earned)', problem + ' (Possible)']

        self.verify_rows_in_csv([
            dict(zip(
                header_row,
                [
                    unicode(self.staff_user.id),
                    self.staff_user.email,
                    self.staff_user.username, u'0.0', u'N/A', u'N/A', u'N/A', u'N/A'
                ]
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.alpha_user.id),
                    self.alpha_user.email,
                    self.alpha_user.username,
                    u'1.0', u'2.0', u'2.0', u'N/A', u'N/A'
                ]
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.beta_user.id),
                    self.beta_user.email,
                    self.beta_user.username,
                    u'0.5', u'N/A', u'N/A', u'1.0', u'2.0'
                ]
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.non_cohorted_user.id),
                    self.non_cohorted_user.email,
                    self.non_cohorted_user.username,
                    u'0.0', u'N/A', u'N/A', u'N/A', u'N/A'
                ]
            )),
        ])


@ddt.ddt
class TestExecutiveSummaryReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that Executive Summary report generation works.
    """
    def setUp(self):
        super(TestExecutiveSummaryReport, self).setUp()
        self.course = CourseFactory.create()
        CourseModeFactory.create(course_id=self.course.id, min_price=50)

        self.instructor = InstructorFactory(course_key=self.course.id)
        self.student1 = UserFactory()
        self.student2 = UserFactory()
        self.student1_cart = Order.get_cart_for_user(self.student1)
        self.student2_cart = Order.get_cart_for_user(self.student2)

        self.sale_invoice_1 = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName',
            company_contact_email='Test@company.com',
            recipient_name='Testw', recipient_email='test1@test.com', customer_reference_number='2Fwe23S',
            internal_reference="A", course_id=self.course.id, is_valid=True
        )
        InvoiceTransaction.objects.create(
            invoice=self.sale_invoice_1,
            amount=self.sale_invoice_1.total_amount,
            status='completed',
            created_by=self.instructor,
            last_modified_by=self.instructor
        )
        self.invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.sale_invoice_1,
            qty=10,
            unit_price=1234.32,
            course_id=self.course.id
        )
        for i in range(5):
            coupon = Coupon(
                code='coupon{0}'.format(i), description='test_description', course_id=self.course.id,
                percentage_discount='{0}'.format(i), created_by=self.instructor, is_active=True,
            )
            coupon.save()

    def test_successfully_generate_executive_summary_report(self):
        """
        Test that successfully generates the executive summary report.
        """
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_exec_summary_report(
                None, None, self.course.id,
                task_input, 'generating executive summary report'
            )
        ReportStore.from_config(config_name='FINANCIAL_REPORTS')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)

    def students_purchases(self):
        """
        Students purchases the courses using enrollment
        and coupon codes.
        """
        self.client.login(username=self.student1.username, password='test')
        paid_course_reg_item = PaidCourseRegistration.add_to_order(self.student1_cart, self.course.id)
        # update the quantity of the cart item paid_course_reg_item
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {
            'ItemId': paid_course_reg_item.id, 'qty': '4'
        })
        self.assertEqual(resp.status_code, 200)
        # apply the coupon code to the item in the cart
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': 'coupon1'})
        self.assertEqual(resp.status_code, 200)

        self.student1_cart.purchase()

        course_reg_codes = CourseRegistrationCode.objects.filter(order=self.student1_cart)
        redeem_url = reverse('register_code_redemption', args=[course_reg_codes[0].code])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertTrue('Activate Course Enrollment' in response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        self.client.login(username=self.student2.username, password='test')
        PaidCourseRegistration.add_to_order(self.student2_cart, self.course.id)

        # apply the coupon code to the item in the cart
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': 'coupon1'})
        self.assertEqual(resp.status_code, 200)

        self.student2_cart.purchase()

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_generate_executive_summary_report(self):
        """
        test to generate executive summary report
        and then test the report authenticity.
        """
        self.students_purchases()
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_exec_summary_report(
                None, None, self.course.id,
                task_input, 'generating executive summary report'
            )
        report_store = ReportStore.from_config(config_name='FINANCIAL_REPORTS')
        expected_data = [
            'Gross Revenue Collected', '$1481.82',
            'Gross Revenue Pending', '$0.00',
            'Average Price per Seat', '$296.36',
            'Number of seats purchased using coupon codes', '<td>2</td>'
        ]
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_html_file_report(report_store, expected_data)

    def _verify_html_file_report(self, report_store, expected_data):
        """
        Verify grade report data.
        """
        report_html_filename = report_store.links_for(self.course.id)[0][0]
        with open(report_store.path_to(self.course.id, report_html_filename)) as html_file:
            html_file_data = html_file.read()
            for data in expected_data:
                self.assertTrue(data in html_file_data)


@ddt.ddt
class TestStudentReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV student profile report generation works.
    """
    def setUp(self):
        super(TestStudentReport, self).setUp()
        self.course = CourseFactory.create()

    def test_success(self):
        self.create_student('student', 'student@example.com')
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_students_csv(None, None, self.course.id, task_input, 'calculated')
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        links = report_store.links_for(self.course.id)

        self.assertEquals(len(links), 1)
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)

    @ddt.data([u'student', u'student\xec'])
    def test_unicode_usernames(self, students):
        """
        Test that students with unicode characters in their usernames
        are handled.
        """
        for i, student in enumerate(students):
            self.create_student(username=student, email='student{0}@example.com'.format(i))

        self.current_task = Mock()
        self.current_task.update_state = Mock()
        task_input = {
            'features': [
                'id', 'username', 'name', 'email', 'language', 'location',
                'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
                'goals'
            ]
        }
        with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task
            result = upload_students_csv(None, None, self.course.id, task_input, 'calculated')
        # This assertion simply confirms that the generation completed with no errors
        num_students = len(students)
        self.assertDictContainsSubset({'attempted': num_students, 'succeeded': num_students, 'failed': 0}, result)


@ddt.ddt
class TestListMayEnroll(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that generation of CSV files containing information about
    students who may enroll in a given course (but have not signed up
    for it yet) works.
    """
    def _create_enrollment(self, email):
        "Factory method for creating CourseEnrollmentAllowed objects."
        return CourseEnrollmentAllowed.objects.create(
            email=email, course_id=self.course.id
        )

    def setUp(self):
        super(TestListMayEnroll, self).setUp()
        self.course = CourseFactory.create()

    def test_success(self):
        self._create_enrollment('user@example.com')
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_may_enroll_csv(None, None, self.course.id, task_input, 'calculated')
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        links = report_store.links_for(self.course.id)

        self.assertEquals(len(links), 1)
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)

    def test_unicode_email_addresses(self):
        """
        Test handling of unicode characters in email addresses of students
        who may enroll in a course.
        """
        enrollments = [u'student@example.com', u'ni\xf1o@example.com']
        for email in enrollments:
            self._create_enrollment(email)

        task_input = {'features': ['email']}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_may_enroll_csv(None, None, self.course.id, task_input, 'calculated')
        # This assertion simply confirms that the generation completed with no errors
        num_enrollments = len(enrollments)
        self.assertDictContainsSubset({'attempted': num_enrollments, 'succeeded': num_enrollments, 'failed': 0}, result)


class MockDefaultStorage(object):
    """Mock django's DefaultStorage"""
    def __init__(self):
        pass

    def open(self, file_name):
        """Mock out DefaultStorage.open with standard python open"""
        return open(file_name)


@patch('instructor_task.tasks_helper.DefaultStorage', new=MockDefaultStorage)
class TestCohortStudents(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that bulk student cohorting works.
    """
    def setUp(self):
        super(TestCohortStudents, self).setUp()

        self.course = CourseFactory.create()
        self.cohort_1 = CohortFactory(course_id=self.course.id, name='Cohort 1')
        self.cohort_2 = CohortFactory(course_id=self.course.id, name='Cohort 2')
        self.student_1 = self.create_student(username=u'student_1\xec', email='student_1@example.com')
        self.student_2 = self.create_student(username='student_2', email='student_2@example.com')
        self.csv_header_row = ['Cohort Name', 'Exists', 'Students Added', 'Students Not Found']

    def _cohort_students_and_upload(self, csv_data):
        """
        Call `cohort_students_and_upload` with a file generated from `csv_data`.
        """
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(csv_data.encode('utf-8'))
            temp_file.flush()
            with patch('instructor_task.tasks_helper._get_current_task'):
                return cohort_students_and_upload(None, None, self.course.id, {'file_name': temp_file.name}, 'cohorted')

    def test_username(self):
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,,Cohort 1\n'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_email(self):
        result = self._cohort_students_and_upload(
            'username,email,cohort\n'
            ',student_1@example.com,Cohort 1\n'
            ',student_2@example.com,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_username_and_email(self):
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,student_1@example.com,Cohort 1\n'
            u'student_2,student_2@example.com,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_prefer_email(self):
        """
        Test that `cohort_students_and_upload` greedily prefers 'email' over
        'username' when identifying the user.  This means that if a correct
        email is present, an incorrect or non-matching username will simply be
        ignored.
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,student_1@example.com,Cohort 1\n'  # valid username and email
            u'Invalid,student_2@example.com,Cohort 2'      # invalid username, valid email
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_non_existent_user(self):
        result = self._cohort_students_and_upload(
            'username,email,cohort\n'
            'Invalid,,Cohort 1\n'
            'student_2,also_fake@bad.com,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 0, 'failed': 2}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '0', 'Invalid'])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '0', 'also_fake@bad.com'])),
            ],
            verify_order=False
        )

    def test_non_existent_cohort(self):
        result = self._cohort_students_and_upload(
            'username,email,cohort\n'
            ',student_1@example.com,Does Not Exist\n'
            'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 1, 'failed': 1}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Does Not Exist', 'False', '0', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_too_few_commas(self):
        """
        A CSV file may be malformed and lack traling commas at the end of a row.
        In this case, those cells take on the value None by the CSV parser.
        Make sure we handle None values appropriately.

        i.e.:
            header_1,header_2,header_3
            val_1,val_2,val_3  <- good row
            val_1,,  <- good row
            val_1    <- bad row; no trailing commas to indicate empty rows
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,\n'
            u'student_2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 0, 'failed': 2}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['', 'False', '0', ''])),
            ],
            verify_order=False
        )

    def test_only_header_row(self):
        result = self._cohort_students_and_upload(
            u'username,email,cohort'
        )
        self.assertDictContainsSubset({'total': 0, 'attempted': 0, 'succeeded': 0, 'failed': 0}, result)
        self.verify_rows_in_csv([])

    def test_carriage_return(self):
        """
        Test that we can handle carriage returns in our file.
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\r'
            u'student_1\xec,,Cohort 1\r'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_carriage_return_line_feed(self):
        """
        Test that we can handle carriage returns and line feeds in our file.
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\r\n'
            u'student_1\xec,,Cohort 1\r\n'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_move_users_to_new_cohort(self):
        self.cohort_1.users.add(self.student_1)
        self.cohort_2.users.add(self.student_2)

        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,,Cohort 2\n'
            u'student_2,,Cohort 1'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_move_users_to_same_cohort(self):
        self.cohort_1.users.add(self.student_1)
        self.cohort_2.users.add(self.student_2)

        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,,Cohort 1\n'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'skipped': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '0', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '0', ''])),
            ],
            verify_order=False
        )


@ddt.ddt
@patch('instructor_task.tasks_helper.DefaultStorage', new=MockDefaultStorage)
class TestGradeReportEnrollmentAndCertificateInfo(TestReportMixin, InstructorTaskModuleTestCase):
    """
    Test that grade report has correct user enrolment, verification, and certificate information.
    """
    def setUp(self):
        super(TestGradeReportEnrollmentAndCertificateInfo, self).setUp()

        self.initialize_course()

        self.create_problem()

        self.columns_to_check = [
            'Enrollment Track',
            'Verification Status',
            'Certificate Eligible',
            'Certificate Delivered',
            'Certificate Type'
        ]

    def create_problem(self, problem_display_name='test_problem', parent=None):
        """
        Create a multiple choice response problem.
        """
        if parent is None:
            parent = self.problem_section

        factory = MultipleChoiceResponseXMLFactory()
        args = {'choices': [False, True, False]}
        problem_xml = factory.build_xml(**args)
        ItemFactory.create(
            parent_location=parent.location,
            parent=parent,
            category="problem",
            display_name=problem_display_name,
            data=problem_xml
        )

    def user_is_embargoed(self, user, is_embargoed):
        """
        Set a users emabargo state.
        """
        user_profile = UserFactory(username=user.username, email=user.email).profile
        user_profile.allow_certificate = not is_embargoed
        user_profile.save()

    def _verify_csv_data(self, username, expected_data):
        """
        Verify grade report data.
        """
        with patch('instructor_task.tasks_helper._get_current_task'):
            upload_grades_csv(None, None, self.course.id, None, 'graded')
            report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
            report_csv_filename = report_store.links_for(self.course.id)[0][0]
            with open(report_store.path_to(self.course.id, report_csv_filename)) as csv_file:
                for row in unicodecsv.DictReader(csv_file):
                    if row.get('username') == username:
                        csv_row_data = [row[column] for column in self.columns_to_check]
                        self.assertEqual(csv_row_data, expected_data)

    def _create_user_data(self,
                          user_enroll_mode,
                          has_passed,
                          whitelisted,
                          is_embargoed,
                          verification_status,
                          certificate_status,
                          certificate_mode):
        """
        Create user data to be used during grade report generation.
        """

        user = self.create_student('u1', mode=user_enroll_mode)

        if has_passed:
            self.submit_student_answer('u1', 'test_problem', ['choice_1'])

        CertificateWhitelistFactory.create(user=user, course_id=self.course.id, whitelist=whitelisted)

        self.user_is_embargoed(user, is_embargoed)

        if user_enroll_mode in CourseMode.VERIFIED_MODES:
            SoftwareSecurePhotoVerificationFactory.create(user=user, status=verification_status)

        GeneratedCertificateFactory.create(
            user=user,
            course_id=self.course.id,
            status=certificate_status,
            mode=certificate_mode
        )

        return user

    @ddt.data(
        (
            'verified', False, False, False, 'approved', 'notpassing', 'honor',
            ['verified', 'ID Verified', 'N', 'N', 'N/A']
        ),
        (
            'verified', False, True, False, 'approved', 'downloadable', 'verified',
            ['verified', 'ID Verified', 'Y', 'Y', 'verified']
        ),
        (
            'honor', True, True, True, 'approved', 'restricted', 'honor',
            ['honor', 'N/A', 'N', 'N', 'N/A']
        ),
        (
            'verified', True, True, False, 'must_retry', 'downloadable', 'honor',
            ['verified', 'Not ID Verified', 'Y', 'Y', 'honor']
        ),
    )
    @ddt.unpack
    def test_grade_report_enrollment_and_certificate_info(
            self,
            user_enroll_mode,
            has_passed,
            whitelisted,
            is_embargoed,
            verification_status,
            certificate_status,
            certificate_mode,
            expected_output
    ):

        user = self._create_user_data(
            user_enroll_mode,
            has_passed,
            whitelisted,
            is_embargoed,
            verification_status,
            certificate_status,
            certificate_mode
        )

        self._verify_csv_data(user.username, expected_output)


@override_settings(CERT_QUEUE='test-queue')
class TestCertificateGeneration(InstructorTaskModuleTestCase):
    """
    Test certificate generation task works.
    """
    def setUp(self):
        super(TestCertificateGeneration, self).setUp()
        self.initialize_course()

    def test_certificate_generation_for_students(self):
        """
        Verify that certificates generated for all eligible students enrolled in a course.
        """
        # create 10 students
        students = [self.create_student(username='student_{}'.format(i), email='student_{}@example.com'.format(i))
                    for i in xrange(1, 11)]

        # mark 2 students to have certificates generated already
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.downloadable,
                mode='honor'
            )

        # white-list 5 students
        for student in students[2:7]:
            CertificateWhitelistFactory.create(user=student, course_id=self.course.id, whitelist=True)

        current_task = Mock()
        current_task.update_state = Mock()
        with self.assertNumQueries(104):
            with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
                mock_current_task.return_value = current_task
                with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_queue:
                    mock_queue.return_value = (0, "Successfully queued")
                    result = generate_students_certificates(None, None, self.course.id, None, 'certificates generated')
        self.assertDictContainsSubset(
            {
                'action_name': 'certificates generated',
                'total': 10,
                'attempted': 8,
                'succeeded': 5,
                'failed': 3,
                'skipped': 2
            },
            result
        )
