# -*- coding: utf-8 -*-

"""
Unit tests for LMS instructor-initiated background tasks helper functions.

- Tests that CSV grade report generation works with unicode emails.
- Tests all of the existing reports.

"""

import os
import shutil
from datetime import datetime
import urllib

import ddt
from freezegun import freeze_time
from mock import Mock, patch, MagicMock
from nose.plugins.attrib import attr
import tempfile
import unicodecsv
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from certificates.models import CertificateStatuses, GeneratedCertificate
from certificates.tests.factories import GeneratedCertificateFactory, CertificateWhitelistFactory
from course_modes.models import CourseMode
from courseware.tests.factories import InstructorFactory
from lms.djangoapps.instructor_task.tests.test_base import (
    InstructorTaskCourseTestCase,
    TestReportMixin,
    InstructorTaskModuleTestCase
)
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup, CohortMembership
from django.conf import settings
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from pytz import UTC

from student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
import openedx.core.djangoapps.user_api.course_tag.api as course_tag_api
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from shoppingcart.models import Order, PaidCourseRegistration, CourseRegistrationCode, Invoice, \
    CourseRegistrationCodeInvoiceItem, InvoiceTransaction, Coupon
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment, CourseEnrollmentAllowed, ManualEnrollmentAudit, ALLOWEDTOENROLL_TO_ENROLLED
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition
from lms.djangoapps.instructor_task.models import ReportStore
from survey.models import SurveyForm, SurveyAnswer
from lms.djangoapps.instructor_task.tasks_helper import (
    cohort_students_and_upload,
    upload_problem_responses_csv,
    upload_grades_csv,
    upload_problem_grade_report,
    upload_students_csv,
    upload_may_enroll_csv,
    upload_enrollment_report,
    upload_exec_summary_report,
    upload_course_survey_report,
    generate_students_certificates,
    upload_ora2_data,
    UPDATE_STATUS_FAILED,
    UPDATE_STATUS_SUCCEEDED,
)
from instructor_analytics.basic import UNAVAILABLE
from openedx.core.djangoapps.util.testing import ContentGroupTestCase, TestConditionalContent
from teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory


class InstructorGradeReportTestCase(TestReportMixin, InstructorTaskCourseTestCase):
    """ Base class for grade report tests. """

    def _verify_cell_data_for_user(self, username, course_id, column_header, expected_cell_content):
        """
        Verify cell data in the grades CSV for a particular user.
        """
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_grades_csv(None, None, course_id, None, 'graded')
            self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
            report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
            report_csv_filename = report_store.links_for(course_id)[0][0]
            report_path = report_store.path_to(course_id, report_csv_filename)
            with report_store.storage.open(report_path) as csv_file:
                for row in unicodecsv.DictReader(csv_file):
                    if row.get('username') == username:
                        self.assertEqual(row[column_header], expected_cell_content)


@ddt.ddt
class TestInstructorGradeReport(InstructorGradeReportTestCase):
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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task
            result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        num_students = len(emails)
        self.assertDictContainsSubset({'attempted': num_students, 'succeeded': num_students, 'failed': 0}, result)

    @patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task')
    @patch('lms.djangoapps.grades.new.course_grade.CourseGradeFactory.iter')
    def test_grading_failure(self, mock_grades_iter, _mock_current_task):
        """
        Test that any grading errors are properly reported in the
        progress dict and uploaded to the report store.
        """
        mock_grades_iter.return_value = [
            (self.create_student('username', 'student@example.com'), None, 'Cannot grade student')
        ]
        result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 0, 'failed': 1}, result)

        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        self.assertTrue(any('grade_report_err' in item[0] for item in report_store.links_for(self.course.id)))

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
        membership1 = CohortMembership(course_user_group=cohort1, user=user1)
        membership1.save()
        membership2 = CohortMembership(course_user_group=cohort2, user=user2)
        membership2.save()

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
            u'Default Group',
        )

    @patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task')
    @patch('lms.djangoapps.grades.new.course_grade.CourseGradeFactory.iter')
    def test_unicode_in_csv_header(self, mock_grades_iter, _mock_current_task):
        """
        Tests that CSV grade report works if unicode in headers.
        """
        mock_course_grade = MagicMock()
        mock_course_grade.summary = {'section_breakdown': [{'label': u'\u8282\u540e\u9898 01'}]}
        mock_course_grade.letter_grade = None
        mock_course_grade.percent = 0
        mock_grades_iter.return_value = [
            (
                self.create_student('username', 'student@example.com'),
                mock_course_grade,
                '',
            )
        ]
        result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)


class TestTeamGradeReport(InstructorGradeReportTestCase):
    """ Test that teams appear correctly in the grade report when it is enabled for the course. """

    def setUp(self):
        super(TestTeamGradeReport, self).setUp()
        self.course = CourseFactory.create(teams_configuration={
            'max_size': 2, 'topics': [{'topic-id': 'topic', 'name': 'Topic', 'description': 'A Topic'}]
        })
        self.student1 = UserFactory.create()
        CourseEnrollment.enroll(self.student1, self.course.id)
        self.student2 = UserFactory.create()
        CourseEnrollment.enroll(self.student2, self.course.id)

    def test_team_in_grade_report(self):
        self._verify_cell_data_for_user(self.student1.username, self.course.id, 'Team Name', '')

    def test_correct_team_name_in_grade_report(self):
        team1 = CourseTeamFactory.create(course_id=self.course.id)
        CourseTeamMembershipFactory.create(team=team1, user=self.student1)
        team2 = CourseTeamFactory.create(course_id=self.course.id)
        CourseTeamMembershipFactory.create(team=team2, user=self.student2)
        self._verify_cell_data_for_user(self.student1.username, self.course.id, 'Team Name', team1.name)
        self._verify_cell_data_for_user(self.student2.username, self.course.id, 'Team Name', team2.name)

    def test_team_deleted(self):
        team1 = CourseTeamFactory.create(course_id=self.course.id)
        membership1 = CourseTeamMembershipFactory.create(team=team1, user=self.student1)
        team2 = CourseTeamFactory.create(course_id=self.course.id)
        CourseTeamMembershipFactory.create(team=team2, user=self.student2)

        team1.delete()
        membership1.delete()

        self._verify_cell_data_for_user(self.student1.username, self.course.id, 'Team Name', '')
        self._verify_cell_data_for_user(self.student2.username, self.course.id, 'Team Name', team2.name)


class TestProblemResponsesReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that generation of CSV files listing student answers to a
    given problem works.
    """
    def setUp(self):
        super(TestProblemResponsesReport, self).setUp()
        self.course = CourseFactory.create()

    def test_success(self):
        task_input = {'problem_location': ''}
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            with patch('lms.djangoapps.instructor_task.tasks_helper.list_problem_responses') as patched_data_source:
                patched_data_source.return_value = [
                    {'username': 'user0', 'state': u'state0'},
                    {'username': 'user1', 'state': u'state1'},
                    {'username': 'user2', 'state': u'state2'},
                ]
                result = upload_problem_responses_csv(None, None, self.course.id, task_input, 'calculated')
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        links = report_store.links_for(self.course.id)

        self.assertEquals(len(links), 1)
        self.assertDictContainsSubset({'attempted': 3, 'succeeded': 3, 'failed': 0}, result)


@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class TestInstructorDetailedEnrollmentReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV detailed enrollment generation works.
    """
    def setUp(self):
        super(TestInstructorDetailedEnrollmentReport, self).setUp()
        self.course = CourseFactory.create()
        CourseModeFactory.create(
            course_id=self.course.id,
            min_price=50,
            mode_slug=CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG
        )

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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_enrollment_report(None, None, self.course.id, task_input, 'generating_enrollment_report')

        enrollment_source = u'manually enrolled by username: {username}'.format(
            username=self.instructor.username)
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)
        self._verify_cell_data_in_csv(student.username, 'Enrollment Source', enrollment_source)
        self._verify_cell_data_in_csv(
            student.username,
            'Manual (Un)Enrollment Reason',
            'manually enrolling unenrolled user'
        )
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
        self.assertIn('Activate Course Enrollment', response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        task_input = {'features': []}
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
            mode_slug=CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG
        )
        course_registration_code.save()

        redeem_url = reverse('register_code_redemption', args=['abcde'])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        task_input = {'features': []}
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
            mode_slug=CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG
        )
        course_registration_code.save()

        redeem_url = reverse('register_code_redemption', args=['abcde'])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        task_input = {'features': []}
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        report_path = report_store.path_to(self.course.id, report_csv_filename)
        with report_store.storage.open(report_path) as csv_file:
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
        self.csv_header_row = [u'Student ID', u'Email', u'Username', u'Grade']

    @patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task')
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

    @patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task')
    def test_single_problem(self, _get_current_task):
        vertical = ItemFactory.create(
            parent_location=self.problem_section.location,
            category='vertical',
            metadata={'graded': True},
            display_name='Problem Vertical'
        )
        self.define_option_problem(u'Problem1', parent=vertical)

        self.submit_student_answer(self.student_1.username, u'Problem1', ['Option 1'])
        result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'action_name': 'graded', 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        problem_name = u'Homework 1: Subsection - Problem1'
        header_row = self.csv_header_row + [problem_name + ' (Earned)', problem_name + ' (Possible)']
        self.verify_rows_in_csv([
            dict(zip(
                header_row,
                [
                    unicode(self.student_1.id),
                    self.student_1.email,
                    self.student_1.username,
                    '0.01', '1.0', '2.0',
                ]
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.student_2.id),
                    self.student_2.email,
                    self.student_2.username,
                    '0.0', u'Not Attempted', '2.0',
                ]
            ))
        ])

    @patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task')
    @patch('lms.djangoapps.grades.new.course_grade.CourseGradeFactory.iter')
    @ddt.data(u'Cannot grade student', '')
    def test_grading_failure(self, error_message, mock_grades_iter, _mock_current_task):
        """
        Test that any grading errors are properly reported in the progress
        dict and uploaded to the report store.
        """
        student = self.create_student(u'username', u'student@example.com')
        mock_grades_iter.return_value = [
            (student, None, error_message)
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


@attr(shard=3)
class TestProblemReportSplitTestContent(TestReportMixin, TestConditionalContent, InstructorTaskModuleTestCase):
    """
    Test the problem report on a course that has split tests.
    """

    OPTION_1 = 'Option 1'
    OPTION_2 = 'Option 2'

    def setUp(self):
        super(TestProblemReportSplitTestContent, self).setUp()
        self.problem_a_url = u'problem_a_url'
        self.problem_b_url = u'problem_b_url'
        self.define_option_problem(self.problem_a_url, parent=self.vertical_a)
        self.define_option_problem(self.problem_b_url, parent=self.vertical_b)

    def test_problem_grade_report(self):
        """
        Test that we generate the correct grade report when dealing with A/B tests.

        In order to verify that the behavior of the grade report is correct, we submit answers for problems
        that the student won't have access to. A/B tests won't restrict access to the problems, but it should
        not show up in that student's course tree when generating the grade report, hence the Not Accessible's
        in the grade report.
        """
        # student A will get 100%, student B will get 50% because
        # OPTION_1 is the correct option, and OPTION_2 is the
        # incorrect option
        self.submit_student_answer(self.student_a.username, self.problem_a_url, [self.OPTION_1, self.OPTION_1])
        self.submit_student_answer(self.student_a.username, self.problem_b_url, [self.OPTION_1, self.OPTION_1])

        self.submit_student_answer(self.student_b.username, self.problem_a_url, [self.OPTION_1, self.OPTION_2])
        self.submit_student_answer(self.student_b.username, self.problem_b_url, [self.OPTION_1, self.OPTION_2])

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
            self.assertDictContainsSubset(
                {'action_name': 'graded', 'attempted': 2, 'succeeded': 2, 'failed': 0}, result
            )

        problem_names = [u'Homework 1: Subsection - problem_a_url', u'Homework 1: Subsection - problem_b_url']
        header_row = [u'Student ID', u'Email', u'Username', u'Grade']
        for problem in problem_names:
            header_row += [problem + ' (Earned)', problem + ' (Possible)']

        self.verify_rows_in_csv([
            dict(zip(
                header_row,
                [
                    unicode(self.student_a.id),
                    self.student_a.email,
                    self.student_a.username,
                    u'1.0', u'2.0', u'2.0', u'Not Accessible', u'Not Accessible'
                ]
            )),
            dict(zip(
                header_row,
                [
                    unicode(self.student_b.id),
                    self.student_b.email,
                    self.student_b.username, u'0.5', u'Not Accessible', u'Not Accessible', u'1.0', u'2.0'
                ]
            ))
        ])

    def test_problem_grade_report_valid_columns_order(self):
        """
        Test that in the CSV grade report columns are placed in the proper order
        """
        grader_num = 7

        self.course = CourseFactory.create(
            grading_policy={
                "GRADER": [{
                    "type": "Homework %d" % i,
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "HW %d" % i,
                    "weight": 1.0
                } for i in xrange(1, grader_num)]
            }
        )

        # Create users
        self.student_a = UserFactory.create(username='student_a', email='student_a@example.com')
        CourseEnrollmentFactory.create(user=self.student_a, course_id=self.course.id)
        self.student_b = UserFactory.create(username='student_b', email='student_b@example.com')
        CourseEnrollmentFactory.create(user=self.student_b, course_id=self.course.id)

        problem_vertical_list = []

        for i in xrange(1, grader_num):
            chapter_name = 'Chapter %d' % i
            problem_section_name = 'Problem section %d' % i
            problem_section_format = 'Homework %d' % i
            problem_vertical_name = 'Problem Unit %d' % i

            chapter = ItemFactory.create(parent_location=self.course.location,
                                         display_name=chapter_name)

            # Add a sequence to the course to which the problems can be added
            problem_section = ItemFactory.create(parent_location=chapter.location,
                                                 category='sequential',
                                                 metadata={'graded': True,
                                                           'format': problem_section_format},
                                                 display_name=problem_section_name)

            # Create a vertical
            problem_vertical = ItemFactory.create(
                parent_location=problem_section.location,
                category='vertical',
                display_name=problem_vertical_name
            )
            problem_vertical_list.append(problem_vertical)

        problem_names = []
        for i in xrange(1, grader_num):
            problem_url = 'test_problem_%d' % i
            self.define_option_problem(problem_url, parent=problem_vertical_list[i - 1])
            title = 'Homework %d 1: Problem section %d - %s' % (i, i, problem_url)
            problem_names.append(title)

        header_row = [u'Student ID', u'Email', u'Username', u'Grade']
        for problem in problem_names:
            header_row += [problem + ' (Earned)', problem + ' (Possible)']

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            upload_problem_grade_report(None, None, self.course.id, None, 'graded')
        self.assertEquals(self.get_csv_row_with_headers(), header_row)


class TestProblemReportCohortedContent(TestReportMixin, ContentGroupTestCase, InstructorTaskModuleTestCase):
    """
    Test the problem report on a course that has cohorted content.
    """
    def setUp(self):
        super(TestProblemReportCohortedContent, self).setUp()
        # construct cohorted problems to work on.
        self.add_course_content()
        vertical = ItemFactory.create(
            parent_location=self.problem_section.location,
            category='vertical',
            metadata={'graded': True},
            display_name='Problem Vertical'
        )
        self.define_option_problem(
            u"Problem0",
            parent=vertical,
            group_access={self.course.user_partitions[0].id: [self.course.user_partitions[0].groups[0].id]}
        )
        self.define_option_problem(
            u"Problem1",
            parent=vertical,
            group_access={self.course.user_partitions[0].id: [self.course.user_partitions[0].groups[1].id]}
        )

    def _format_user_grade(self, header_row, user, grade):
        """
        Helper method that format the user grade
        Args:
            header_row(list): header row of csv containing Student ID, Email, Username etc
            user(object): Django user object
            grade(list): Users' grade list
        """
        return dict(zip(
            header_row,
            [
                unicode(user.id),
                user.email,
                user.username,
            ] + grade
        ))

    def test_cohort_content(self):
        self.submit_student_answer(self.alpha_user.username, u'Problem0', ['Option 1', 'Option 1'])
        resp = self.submit_student_answer(self.alpha_user.username, u'Problem1', ['Option 1', 'Option 1'])
        self.assertEqual(resp.status_code, 404)

        resp = self.submit_student_answer(self.beta_user.username, u'Problem0', ['Option 1', 'Option 2'])
        self.assertEqual(resp.status_code, 404)
        self.submit_student_answer(self.beta_user.username, u'Problem1', ['Option 1', 'Option 2'])

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_problem_grade_report(None, None, self.course.id, None, 'graded')
            self.assertDictContainsSubset(
                {'action_name': 'graded', 'attempted': 4, 'succeeded': 4, 'failed': 0}, result
            )
        problem_names = [u'Homework 1: Subsection - Problem0', u'Homework 1: Subsection - Problem1']
        header_row = [u'Student ID', u'Email', u'Username', u'Grade']
        for problem in problem_names:
            header_row += [problem + ' (Earned)', problem + ' (Possible)']

        user_grades = [
            {
                'user': self.staff_user,
                'grade': [u'0.0', u'Not Accessible', u'Not Accessible', u'Not Accessible', u'Not Accessible'],
            },
            {
                'user': self.alpha_user,
                'grade': [u'1.0', u'2.0', u'2.0', u'Not Accessible', u'Not Accessible'],
            },
            {
                'user': self.beta_user,
                'grade': [u'0.5', u'Not Accessible', u'Not Accessible', u'1.0', u'2.0'],
            },
            {
                'user': self.non_cohorted_user,
                'grade': [u'0.0', u'Not Accessible', u'Not Accessible', u'Not Accessible', u'Not Accessible'],
            },
        ]

        # Verify generated grades and expected grades match
        expected_grades = [self._format_user_grade(header_row, **user_grade) for user_grade in user_grades]
        self.verify_rows_in_csv(expected_grades)


@ddt.ddt
class TestExecutiveSummaryReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that Executive Summary report generation works.
    """
    def setUp(self):
        super(TestExecutiveSummaryReport, self).setUp()
        self.course = CourseFactory.create()
        CourseModeFactory.create(
            course_id=self.course.id,
            min_price=50,
            mode_slug=CourseMode.DEFAULT_SHOPPINGCART_MODE_SLUG
        )

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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        self.assertIn('Activate Course Enrollment', response.content)

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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        report_path = report_store.path_to(self.course.id, report_html_filename)
        with report_store.storage.open(report_path) as html_file:
            html_file_data = html_file.read()
            for data in expected_data:
                self.assertIn(data, html_file_data)


@ddt.ddt
class TestCourseSurveyReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that Course Survey report generation works.
    """
    def setUp(self):
        super(TestCourseSurveyReport, self).setUp()
        self.course = CourseFactory.create()

        self.question1 = "question1"
        self.question2 = "question2"
        self.question3 = "question3"
        self.answer1 = "answer1"
        self.answer2 = "answer2"
        self.answer3 = "answer3"

        self.student1 = UserFactory()
        self.student2 = UserFactory()

        self.test_survey_name = 'TestSurvey'
        self.test_form = '<input name="field1"></input>'
        self.survey_form = SurveyForm.create(self.test_survey_name, self.test_form)

        self.survey1 = SurveyAnswer.objects.create(user=self.student1, form=self.survey_form, course_key=self.course.id,
                                                   field_name=self.question1, field_value=self.answer1)
        self.survey2 = SurveyAnswer.objects.create(user=self.student1, form=self.survey_form, course_key=self.course.id,
                                                   field_name=self.question2, field_value=self.answer2)
        self.survey3 = SurveyAnswer.objects.create(user=self.student2, form=self.survey_form, course_key=self.course.id,
                                                   field_name=self.question1, field_value=self.answer3)
        self.survey4 = SurveyAnswer.objects.create(user=self.student2, form=self.survey_form, course_key=self.course.id,
                                                   field_name=self.question2, field_value=self.answer2)
        self.survey5 = SurveyAnswer.objects.create(user=self.student2, form=self.survey_form, course_key=self.course.id,
                                                   field_name=self.question3, field_value=self.answer1)

    def test_successfully_generate_course_survey_report(self):
        """
        Test that successfully generates the course survey report.
        """
        task_input = {'features': []}
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_course_survey_report(
                None, None, self.course.id,
                task_input, 'generating course survey report'
            )
        self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_generate_course_survey_report(self):
        """
        test to generate course survey report
        and then test the report authenticity.
        """

        task_input = {'features': []}
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_course_survey_report(
                None, None, self.course.id,
                task_input, 'generating course survey report'
            )

        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        header_row = ",".join(['User ID', 'User Name', 'Email', self.question1, self.question2, self.question3])
        student1_row = ",".join([
            str(self.student1.id),  # pylint: disable=no-member
            self.student1.username,
            self.student1.email,
            self.answer1,
            self.answer2
        ])
        student2_row = ",".join([
            str(self.student2.id),  # pylint: disable=no-member
            self.student2.username,
            self.student2.email,
            self.answer3,
            self.answer2,
            self.answer1
        ])
        expected_data = [header_row, student1_row, student2_row]

        self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self._verify_csv_file_report(report_store, expected_data)

    def _verify_csv_file_report(self, report_store, expected_data):
        """
        Verify course survey data.
        """
        report_csv_filename = report_store.links_for(self.course.id)[0][0]
        report_path = report_store.path_to(self.course.id, report_csv_filename)
        with report_store.storage.open(report_path) as csv_file:
            csv_file_data = csv_file.read()
            for data in expected_data:
                self.assertIn(data, csv_file_data)


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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task
            result = upload_students_csv(None, None, self.course.id, task_input, 'calculated')
        # This assertion simply confirms that the generation completed with no errors
        num_students = len(students)
        self.assertDictContainsSubset({'attempted': num_students, 'succeeded': num_students, 'failed': 0}, result)


class TestTeamStudentReport(TestReportMixin, InstructorTaskCourseTestCase):
    "Test the student report when including teams information. "

    def setUp(self):
        super(TestTeamStudentReport, self).setUp()
        self.course = CourseFactory.create(teams_configuration={
            'max_size': 2, 'topics': [{'topic-id': 'topic', 'name': 'Topic', 'description': 'A Topic'}]
        })
        self.student1 = UserFactory.create()
        CourseEnrollment.enroll(self.student1, self.course.id)
        self.student2 = UserFactory.create()
        CourseEnrollment.enroll(self.student2, self.course.id)

    def _generate_and_verify_teams_column(self, username, expected_team):
        """ Run the upload_students_csv task and verify that the correct team was added to the CSV. """
        current_task = Mock()
        current_task.update_state = Mock()
        task_input = {
            'features': [
                'id', 'username', 'name', 'email', 'language', 'location',
                'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
                'goals', 'team'
            ]
        }
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = current_task
            result = upload_students_csv(None, None, self.course.id, task_input, 'calculated')
            self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
            report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
            report_csv_filename = report_store.links_for(self.course.id)[0][0]
            report_path = report_store.path_to(self.course.id, report_csv_filename)
            with report_store.storage.open(report_path) as csv_file:
                for row in unicodecsv.DictReader(csv_file):
                    if row.get('username') == username:
                        self.assertEqual(row['team'], expected_team)

    def test_team_column_no_teams(self):
        self._generate_and_verify_teams_column(self.student1.username, UNAVAILABLE)
        self._generate_and_verify_teams_column(self.student2.username, UNAVAILABLE)

    def test_team_column_with_teams(self):
        team1 = CourseTeamFactory.create(course_id=self.course.id)
        CourseTeamMembershipFactory.create(team=team1, user=self.student1)
        team2 = CourseTeamFactory.create(course_id=self.course.id)
        CourseTeamMembershipFactory.create(team=team2, user=self.student2)
        self._generate_and_verify_teams_column(self.student1.username, team1.name)
        self._generate_and_verify_teams_column(self.student2.username, team2.name)

    def test_team_column_with_deleted_team(self):
        team1 = CourseTeamFactory.create(course_id=self.course.id)
        membership1 = CourseTeamMembershipFactory.create(team=team1, user=self.student1)
        team2 = CourseTeamFactory.create(course_id=self.course.id)
        CourseTeamMembershipFactory.create(team=team2, user=self.student2)

        team1.delete()
        membership1.delete()

        self._generate_and_verify_teams_column(self.student1.username, UNAVAILABLE)
        self._generate_and_verify_teams_column(self.student2.username, team2.name)


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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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


@patch('lms.djangoapps.instructor_task.tasks_helper.DefaultStorage', new=MockDefaultStorage)
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
            with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
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
        membership1 = CohortMembership(course_user_group=self.cohort_1, user=self.student_1)
        membership1.save()
        membership2 = CohortMembership(course_user_group=self.cohort_2, user=self.student_2)
        membership2.save()

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
        membership1 = CohortMembership(course_user_group=self.cohort_1, user=self.student_1)
        membership1.save()
        membership2 = CohortMembership(course_user_group=self.cohort_2, user=self.student_2)
        membership2.save()

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


@patch('lms.djangoapps.instructor_task.tasks_helper.DefaultStorage', new=MockDefaultStorage)
class TestGradeReport(TestReportMixin, InstructorTaskModuleTestCase):
    """
    Test that grade report has correct grade values.
    """
    def setUp(self):
        super(TestGradeReport, self).setUp()
        self.create_course()
        self.student = self.create_student(u'üser_1')

    def create_course(self):
        """
        Creates a course with various subsections for testing
        """
        self.course = CourseFactory.create(
            grading_policy={
                "GRADER": [
                    {
                        "type": "Homework",
                        "min_count": 4,
                        "drop_count": 0,
                        "weight": 1.0
                    },
                ],
            },
        )
        self.chapter = ItemFactory.create(parent=self.course, category='chapter')

        self.problem_section = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            metadata={'graded': True, 'format': 'Homework'},
            display_name='Subsection'
        )
        self.define_option_problem(u'Problem1', parent=self.problem_section, num_responses=1)
        self.hidden_section = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            metadata={'graded': True, 'format': 'Homework'},
            visible_to_staff_only=True,
            display_name='Hidden',
        )
        self.define_option_problem(u'Problem2', parent=self.hidden_section)
        self.unattempted_section = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            metadata={'graded': True, 'format': 'Homework'},
            display_name='Unattempted',
        )
        self.define_option_problem(u'Problem3', parent=self.unattempted_section)
        self.empty_section = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            metadata={'graded': True, 'format': 'Homework'},
            display_name='Empty',
        )

    def test_grade_report(self):
        self.submit_student_answer(self.student.username, u'Problem1', ['Option 1'])

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            result = upload_grades_csv(None, None, self.course.id, None, 'graded')
            self.assertDictContainsSubset(
                {'action_name': 'graded', 'attempted': 1, 'succeeded': 1, 'failed': 0},
                result,
            )
            self.verify_rows_in_csv(
                [
                    {
                        u'Student ID': unicode(self.student.id),
                        u'Email': self.student.email,
                        u'Username': self.student.username,
                        u'Grade': '0.13',
                        u'Homework 1: Subsection': '0.5',
                        u'Homework 2: Hidden': u'Not Accessible',
                        u'Homework 3: Unattempted': u'Not Attempted',
                        u'Homework 4: Empty': u'Not Accessible',
                        u'Homework (Avg)': '0.125',
                    },
                ],
                ignore_other_columns=True,
            )


@ddt.ddt
@patch('lms.djangoapps.instructor_task.tasks_helper.DefaultStorage', new=MockDefaultStorage)
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
        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task'):
            upload_grades_csv(None, None, self.course.id, None, 'graded')
            report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
            report_csv_filename = report_store.links_for(self.course.id)[0][0]
            report_path = report_store.path_to(self.course.id, report_csv_filename)
            with report_store.storage.open(report_path) as csv_file:
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


@attr(shard=3)
@ddt.ddt
@override_settings(CERT_QUEUE='test-queue')
class TestCertificateGeneration(InstructorTaskModuleTestCase):
    """
    Test certificate generation task works.
    """

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        super(TestCertificateGeneration, self).setUp()
        self.initialize_course()

    def test_certificate_generation_for_students(self):
        """
        Verify that certificates generated for all eligible students enrolled in a course.
        """
        # create 10 students
        students = self._create_students(10)

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

        task_input = {'student_set': None}
        expected_results = {
            'action_name': 'certificates generated',
            'total': 10,
            'attempted': 8,
            'succeeded': 5,
            'failed': 3,
            'skipped': 2
        }
        with self.assertNumQueries(166):
            self.assertCertificatesGenerated(task_input, expected_results)

        expected_results = {
            'action_name': 'certificates generated',
            'total': 10,
            'attempted': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 10
        }
        with self.assertNumQueries(3):
            self.assertCertificatesGenerated(task_input, expected_results)

    @ddt.data(
        CertificateStatuses.downloadable,
        CertificateStatuses.generating,
        CertificateStatuses.notpassing,
        CertificateStatuses.audit_passing,
    )
    def test_certificate_generation_all_whitelisted(self, status):
        """
        Verify that certificates are generated for all white-listed students,
        whether or not they already had certs generated for them.
        """
        students = self._create_students(5)

        # whitelist 3
        for student in students[:3]:
            CertificateWhitelistFactory.create(
                user=student, course_id=self.course.id, whitelist=True
            )

        # generate certs for 2
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=status,
            )

        task_input = {'student_set': 'all_whitelisted'}
        # only certificates for the 3 whitelisted students should have been run
        expected_results = {
            'action_name': 'certificates generated',
            'total': 3,
            'attempted': 3,
            'succeeded': 3,
            'failed': 0,
            'skipped': 0
        }
        self.assertCertificatesGenerated(task_input, expected_results)

        # the first 3 students (who were whitelisted) have passing
        # certificate statuses
        for student in students[:3]:
            self.assertIn(
                GeneratedCertificate.certificate_for_student(student, self.course.id).status,
                CertificateStatuses.PASSED_STATUSES
            )

        # The last 2 students still don't have certs
        for student in students[3:]:
            self.assertIsNone(
                GeneratedCertificate.certificate_for_student(student, self.course.id)
            )

    @ddt.data(
        (CertificateStatuses.downloadable, 2),
        (CertificateStatuses.generating, 2),
        (CertificateStatuses.notpassing, 4),
        (CertificateStatuses.audit_passing, 4),
    )
    @ddt.unpack
    def test_certificate_generation_whitelisted_not_generated(self, status, expected_certs):
        """
        Verify that certificates are generated only for those students
        who do not have `downloadable` or `generating` certificates.
        """
        # create 5 students
        students = self._create_students(5)

        # mark 2 students to have certificates generated already
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=status,
            )

        # white-list 4 students
        for student in students[:4]:
            CertificateWhitelistFactory.create(
                user=student, course_id=self.course.id, whitelist=True
            )

        task_input = {'student_set': 'whitelisted_not_generated'}

        # certificates should only be generated for the whitelisted students
        # who do not yet have passing certificates.
        expected_results = {
            'action_name': 'certificates generated',
            'total': expected_certs,
            'attempted': expected_certs,
            'succeeded': expected_certs,
            'failed': 0,
            'skipped': 0
        }
        self.assertCertificatesGenerated(
            task_input,
            expected_results
        )

        # the first 4 students have passing certificate statuses since
        # they either were whitelisted or had one before
        for student in students[:4]:
            self.assertIn(
                GeneratedCertificate.certificate_for_student(student, self.course.id).status,
                CertificateStatuses.PASSED_STATUSES
            )

        # The last student still doesn't have a cert
        self.assertIsNone(
            GeneratedCertificate.certificate_for_student(students[4], self.course.id)
        )

    def test_certificate_generation_specific_student(self):
        """
        Tests generating a certificate for a specific student.
        """
        student = self.create_student(username="Hamnet", email="ham@ardenforest.co.uk")
        CertificateWhitelistFactory.create(user=student, course_id=self.course.id, whitelist=True)
        task_input = {
            'student_set': 'specific_student',
            'specific_student_id': student.id
        }
        expected_results = {
            'action_name': 'certificates generated',
            'total': 1,
            'attempted': 1,
            'succeeded': 1,
            'failed': 0,
            'skipped': 0,
        }
        self.assertCertificatesGenerated(task_input, expected_results)

    def test_specific_student_not_enrolled(self):
        """
        Tests generating a certificate for a specific student if that student
        is not enrolled in the course.
        """
        student = self.create_student(username="jacques", email="antlers@ardenforest.co.uk")
        task_input = {
            'student_set': 'specific_student',
            'specific_student_id': student.id
        }
        expected_results = {
            'action_name': 'certificates generated',
            'total': 1,
            'attempted': 1,
            'succeeded': 0,
            'failed': 1,
            'skipped': 0,
        }
        self.assertCertificatesGenerated(task_input, expected_results)

    def test_certificate_regeneration_for_statuses_to_regenerate(self):
        """
        Verify that certificates are regenerated for all eligible students enrolled in a course whose generated
        certificate statuses lies in the list 'statuses_to_regenerate' given in task_input.
        """
        # create 10 students
        students = self._create_students(10)

        # mark 2 students to have certificates generated already
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.downloadable,
                mode='honor'
            )

        # mark 3 students to have certificates generated with status 'error'
        for student in students[2:5]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.error,
                mode='honor'
            )

        # mark 6th students to have certificates generated with status 'deleted'
        for student in students[5:6]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.deleted,
                mode='honor'
            )

        # white-list 7 students
        for student in students[:7]:
            CertificateWhitelistFactory.create(user=student, course_id=self.course.id, whitelist=True)

        # Certificates should be regenerated for students having generated certificates with status
        # 'downloadable' or 'error' which are total of 5 students in this test case
        task_input = {'statuses_to_regenerate': [CertificateStatuses.downloadable, CertificateStatuses.error]}

        expected_results = {
            'action_name': 'certificates generated',
            'total': 10,
            'attempted': 5,
            'succeeded': 5,
            'failed': 0,
            'skipped': 5
        }

        self.assertCertificatesGenerated(
            task_input,
            expected_results
        )

    def test_certificate_regeneration_with_expected_failures(self):
        """
        Verify that certificates are regenerated for all eligible students enrolled in a course whose generated
        certificate statuses lies in the list 'statuses_to_regenerate' given in task_input.
        """
        # Default grade for students
        default_grade = '-1'

        # create 10 students
        students = self._create_students(10)

        # mark 2 students to have certificates generated already
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.downloadable,
                mode='honor',
                grade=default_grade
            )

        # mark 3 students to have certificates generated with status 'error'
        for student in students[2:5]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.error,
                mode='honor',
                grade=default_grade
            )

        # mark 6th students to have certificates generated with status 'deleted'
        for student in students[5:6]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.deleted,
                mode='honor',
                grade=default_grade
            )

        # mark rest of the 4 students with having generated certificates with status 'generating'
        # These students are not added in white-list and they have not completed grades so certificate generation
        # for these students should fail other than the one student that has been added to white-list
        # so from these students 3 failures and 1 success
        for student in students[6:]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.generating,
                mode='honor',
                grade=default_grade
            )

        # white-list 7 students
        for student in students[:7]:
            CertificateWhitelistFactory.create(user=student, course_id=self.course.id, whitelist=True)

        # Regenerated certificates for students having generated certificates with status
        # 'deleted' or 'generating'
        task_input = {'statuses_to_regenerate': [CertificateStatuses.deleted, CertificateStatuses.generating]}

        expected_results = {
            'action_name': 'certificates generated',
            'total': 10,
            'attempted': 5,
            'succeeded': 2,
            'failed': 3,
            'skipped': 5
        }

        self.assertCertificatesGenerated(task_input, expected_results)

        generated_certificates = GeneratedCertificate.eligible_certificates.filter(
            user__in=students,
            course_id=self.course.id,
            mode='honor'
        )
        certificate_statuses = [generated_certificate.status for generated_certificate in generated_certificates]
        certificate_grades = [generated_certificate.grade for generated_certificate in generated_certificates]

        # Verify from results from database
        # Certificates are being generated for 2 white-listed students that had statuses in 'deleted'' and 'generating'
        self.assertEqual(certificate_statuses.count(CertificateStatuses.generating), 2)
        # 5 students are skipped that had Certificate Status 'downloadable' and 'error'
        self.assertEqual(certificate_statuses.count(CertificateStatuses.downloadable), 2)
        self.assertEqual(certificate_statuses.count(CertificateStatuses.error), 3)

        # grades will be '0.0' as students are either white-listed or ending in error
        self.assertEqual(certificate_grades.count('0.0'), 5)
        # grades will be '-1' for students that were skipped
        self.assertEqual(certificate_grades.count(default_grade), 5)

    def test_certificate_regeneration_with_existing_unavailable_status(self):
        """
        Verify that certificates are regenerated for all eligible students enrolled in a course whose generated
        certificate status lies in the list 'statuses_to_regenerate' given in task_input. but the 'unavailable'
        status is not touched if it is not in the 'statuses_to_regenerate' list.
        """
        # Default grade for students
        default_grade = '-1'

        # create 10 students
        students = self._create_students(10)

        # mark 2 students to have certificates generated already
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.downloadable,
                mode='honor',
                grade=default_grade
            )

        # mark 3 students to have certificates generated with status 'error'
        for student in students[2:5]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.error,
                mode='honor',
                grade=default_grade
            )

        # mark 2 students to have generated certificates with status 'unavailable'
        for student in students[5:7]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.unavailable,
                mode='honor',
                grade=default_grade
            )

        # mark 3 students to have generated certificates with status 'generating'
        for student in students[7:]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.generating,
                mode='honor',
                grade=default_grade
            )

        # white-list all students
        for student in students[:]:
            CertificateWhitelistFactory.create(user=student, course_id=self.course.id, whitelist=True)

        # Regenerated certificates for students having generated certificates with status
        # 'downloadable', 'error' or 'generating'
        task_input = {
            'statuses_to_regenerate': [
                CertificateStatuses.downloadable,
                CertificateStatuses.error,
                CertificateStatuses.generating
            ]
        }

        expected_results = {
            'action_name': 'certificates generated',
            'total': 10,
            'attempted': 8,
            'succeeded': 8,
            'failed': 0,
            'skipped': 2
        }

        self.assertCertificatesGenerated(
            task_input,
            expected_results
        )

        generated_certificates = GeneratedCertificate.eligible_certificates.filter(
            user__in=students,
            course_id=self.course.id,
            mode='honor'
        )
        certificate_statuses = [generated_certificate.status for generated_certificate in generated_certificates]
        certificate_grades = [generated_certificate.grade for generated_certificate in generated_certificates]

        # Verify from results from database
        # Certificates are being generated for 8 students that had statuses in 'downloadable', 'error' and 'generating'
        self.assertEqual(certificate_statuses.count(CertificateStatuses.generating), 8)
        # 2 students are skipped that had Certificate Status 'unavailable'
        self.assertEqual(certificate_statuses.count(CertificateStatuses.unavailable), 2)

        # grades will be '0.0' as students are white-listed and have not completed any tasks
        self.assertEqual(certificate_grades.count('0.0'), 8)
        # grades will be '-1' for students that have not been processed
        self.assertEqual(certificate_grades.count(default_grade), 2)

        # Verify that students with status 'unavailable were skipped
        unavailable_certificates = \
            [cert for cert in generated_certificates
             if cert.status == CertificateStatuses.unavailable and cert.grade == default_grade]

        self.assertEquals(len(unavailable_certificates), 2)

    def test_certificate_regeneration_for_students(self):
        """
        Verify that certificates are regenerated for all students passed in task_input.
        """
        # create 10 students
        students = self._create_students(10)

        # mark 2 students to have certificates generated already
        for student in students[:2]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.downloadable,
                mode='honor'
            )

        # mark 3 students to have certificates generated with status 'error'
        for student in students[2:5]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.error,
                mode='honor'
            )

        # mark 6th students to have certificates generated with status 'deleted'
        for student in students[5:6]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.deleted,
                mode='honor'
            )

        # mark 7th students to have certificates generated with status 'norpassing'
        for student in students[6:7]:
            GeneratedCertificateFactory.create(
                user=student,
                course_id=self.course.id,
                status=CertificateStatuses.notpassing,
                mode='honor'
            )

        # white-list 7 students
        for student in students[:7]:
            CertificateWhitelistFactory.create(user=student, course_id=self.course.id, whitelist=True)

        # Certificates should be regenerated for students having generated certificates with status
        # 'downloadable' or 'error' which are total of 5 students in this test case
        task_input = {'student_set': "all_whitelisted"}

        expected_results = {
            'action_name': 'certificates generated',
            'total': 7,
            'attempted': 7,
            'succeeded': 7,
            'failed': 0,
            'skipped': 0,
        }

        self.assertCertificatesGenerated(task_input, expected_results)

    def assertCertificatesGenerated(self, task_input, expected_results):
        """
        Generate certificates for the given task_input and compare with expected_results.
        """
        current_task = Mock()
        current_task.update_state = Mock()

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = current_task
            with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_queue:
                mock_queue.return_value = (0, "Successfully queued")
                result = generate_students_certificates(
                    None, None, self.course.id, task_input, 'certificates generated'
                )

        self.assertDictContainsSubset(
            expected_results,
            result
        )

    def _create_students(self, number_of_students):
        """
        Create Students for course.
        """
        return [
            self.create_student(
                username='student_{}'.format(index),
                email='student_{}@example.com'.format(index)
            )
            for index in xrange(number_of_students)
        ]


class TestInstructorOra2Report(SharedModuleStoreTestCase):
    """
    Tests that ORA2 response report generation works.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorOra2Report, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorOra2Report, self).setUp()

        self.current_task = Mock()
        self.current_task.update_state = Mock()

    def tearDown(self):
        super(TestInstructorOra2Report, self).tearDown()
        if os.path.exists(settings.GRADES_DOWNLOAD['ROOT_PATH']):
            shutil.rmtree(settings.GRADES_DOWNLOAD['ROOT_PATH'])

    def test_report_fails_if_error(self):
        with patch(
            'lms.djangoapps.instructor_task.tasks_helper.OraAggregateData.collect_ora2_data'
        ) as mock_collect_data:
            mock_collect_data.side_effect = KeyError

            with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_current_task:
                mock_current_task.return_value = self.current_task

                response = upload_ora2_data(None, None, self.course.id, None, 'generated')
                self.assertEqual(response, UPDATE_STATUS_FAILED)

    @freeze_time('2001-01-01 00:00:00')
    def test_report_stores_results(self):
        test_header = ['field1', 'field2']
        test_rows = [['row1_field1', 'row1_field2'], ['row2_field1', 'row2_field2']]

        with patch('lms.djangoapps.instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task

            with patch(
                'lms.djangoapps.instructor_task.tasks_helper.OraAggregateData.collect_ora2_data'
            ) as mock_collect_data:
                mock_collect_data.return_value = (test_header, test_rows)

                with patch(
                    'lms.djangoapps.instructor_task.models.DjangoStorageReportStore.store_rows'
                ) as mock_store_rows:
                    return_val = upload_ora2_data(None, None, self.course.id, None, 'generated')

                    # pylint: disable=maybe-no-member
                    timestamp_str = datetime.now(UTC).strftime('%Y-%m-%d-%H%M')
                    course_id_string = urllib.quote(self.course.id.to_deprecated_string().replace('/', '_'))
                    filename = u'{}_ORA_data_{}.csv'.format(course_id_string, timestamp_str)

                    self.assertEqual(return_val, UPDATE_STATUS_SUCCEEDED)
                    mock_store_rows.assert_called_once_with(self.course.id, filename, [test_header] + test_rows)
