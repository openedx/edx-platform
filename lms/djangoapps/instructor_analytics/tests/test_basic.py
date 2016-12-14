"""
Tests for instructor.basic
"""

import datetime
import json
import pytz
from mock import MagicMock, Mock, patch
from django.core.urlresolvers import reverse
from django.db.models import Q

from course_modes.models import CourseMode
from courseware.courses import get_course
from courseware.tests.factories import InstructorFactory
from courseware.tests.factories import StudentModuleFactory
from instructor_analytics.basic import (
    StudentModule, sale_record_features, sale_order_record_features, enrolled_students_features,
    course_registration_features, coupon_codes_features, get_proctored_exam_results, list_may_enroll,
    list_problem_responses, AVAILABLE_FEATURES, STUDENT_FEATURES, PROFILE_FEATURES
)
from instructor_analytics.basic import student_responses
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import Location
from opaque_keys.edx.locator import UsageKey
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from student.roles import CourseSalesAdminRole
from student.tests.factories import UserFactory, CourseModeFactory
from shoppingcart.models import (
    CourseRegistrationCode, RegistrationCodeRedemption, Order,
    Invoice, Coupon, CourseRegCodeItem, CouponRedemption, CourseRegistrationCodeInvoiceItem
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_GRADED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from edx_proctoring.api import create_exam
from edx_proctoring.models import ProctoredExamStudentAttempt
from xmodule.modulestore.django import modulestore


class TestAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic analytics functions. """

    def setUp(self):
        super(TestAnalyticsBasic, self).setUp()
        self.course_key = self.store.make_course_key('robot', 'course', 'id')
        self.users = tuple(UserFactory() for _ in xrange(30))
        self.ces = tuple(CourseEnrollment.enroll(user, self.course_key)
                         for user in self.users)
        self.instructor = InstructorFactory(course_key=self.course_key)
        for user in self.users:
            user.profile.meta = json.dumps({
                "position": "edX expert {}".format(user.id),
                "company": "Open edX Inc {}".format(user.id),
            })
            user.profile.save()
        self.students_who_may_enroll = list(self.users) + [UserFactory() for _ in range(5)]
        for student in self.students_who_may_enroll:
            CourseEnrollmentAllowed.objects.create(
                email=student.email, course_id=self.course_key
            )

    def test_list_problem_responses(self):
        def result_factory(result_id):
            """
            Return a dummy StudentModule object that can be queried for
            relevant info (student.username and state).
            """
            result = Mock(spec=['student', 'state'])
            result.student.username.return_value = u'user{}'.format(result_id)
            result.state.return_value = u'state{}'.format(result_id)
            return result

        # Ensure that UsageKey.from_string returns a problem key that list_problem_responses can work with
        # (even when called with a dummy location):
        mock_problem_key = Mock(return_value=u'')
        mock_problem_key.course_key = self.course_key
        with patch.object(UsageKey, 'from_string') as patched_from_string:
            patched_from_string.return_value = mock_problem_key

            # Ensure that StudentModule.objects.filter returns a result set that list_problem_responses can work with
            # (this keeps us from having to create fixtures for this test):
            mock_results = MagicMock(return_value=[result_factory(n) for n in range(5)])
            with patch.object(StudentModule, 'objects') as patched_manager:
                patched_manager.filter.return_value = mock_results

                mock_problem_location = ''
                problem_responses = list_problem_responses(self.course_key, problem_location=mock_problem_location)

                # Check if list_problem_responses called UsageKey.from_string to look up problem key:
                patched_from_string.assert_called_once_with(mock_problem_location)
                # Check if list_problem_responses called StudentModule.objects.filter to obtain relevant records:
                patched_manager.filter.assert_called_once_with(
                    course_id=self.course_key, module_state_key=mock_problem_key
                )

                # Check if list_problem_responses returned expected results:
                self.assertEqual(len(problem_responses), len(mock_results))
                for mock_result in mock_results:
                    self.assertTrue(
                        {'username': mock_result.student.username, 'state': mock_result.state} in
                        problem_responses
                    )

    def test_enrolled_students_features_username(self):
        self.assertIn('username', AVAILABLE_FEATURES)
        userreports = enrolled_students_features(self.course_key, ['username'])
        self.assertEqual(len(userreports), len(self.users))
        for userreport in userreports:
            self.assertEqual(userreport.keys(), ['username'])
            self.assertIn(userreport['username'], [user.username for user in self.users])

    def test_enrolled_students_features_keys(self):
        query_features = ('username', 'name', 'email')
        for feature in query_features:
            self.assertIn(feature, AVAILABLE_FEATURES)
        with self.assertNumQueries(1):
            userreports = enrolled_students_features(self.course_key, query_features)
        self.assertEqual(len(userreports), len(self.users))
        for userreport in userreports:
            self.assertEqual(set(userreport.keys()), set(query_features))
            self.assertIn(userreport['username'], [user.username for user in self.users])
            self.assertIn(userreport['email'], [user.email for user in self.users])
            self.assertIn(userreport['name'], [user.profile.name for user in self.users])

    def test_enrolled_students_meta_features_keys(self):
        """
        Assert that we can query individual fields in the 'meta' field in the UserProfile
        """
        query_features = ('meta.position', 'meta.company')
        with self.assertNumQueries(1):
            userreports = enrolled_students_features(self.course_key, query_features)
        self.assertEqual(len(userreports), len(self.users))
        for userreport in userreports:
            self.assertEqual(set(userreport.keys()), set(query_features))
            self.assertIn(userreport['meta.position'], ["edX expert {}".format(user.id) for user in self.users])
            self.assertIn(userreport['meta.company'], ["Open edX Inc {}".format(user.id) for user in self.users])

    def test_enrolled_students_features_keys_cohorted(self):
        course = CourseFactory.create(org="test", course="course1", display_name="run1")
        course.cohort_config = {'cohorted': True, 'auto_cohort': True, 'auto_cohort_groups': ['cohort']}
        self.store.update_item(course, self.instructor.id)
        cohorted_students = [UserFactory.create() for _ in xrange(10)]
        cohort = CohortFactory.create(name='cohort', course_id=course.id, users=cohorted_students)
        cohorted_usernames = [student.username for student in cohorted_students]
        non_cohorted_student = UserFactory.create()
        for student in cohorted_students:
            cohort.users.add(student)
            CourseEnrollment.enroll(student, course.id)
        CourseEnrollment.enroll(non_cohorted_student, course.id)
        instructor = InstructorFactory(course_key=course.id)
        self.client.login(username=instructor.username, password='test')

        query_features = ('username', 'cohort')
        # There should be a constant of 2 SQL queries when calling
        # enrolled_students_features.  The first query comes from the call to
        # User.objects.filter(...), and the second comes from
        # prefetch_related('course_groups').
        with self.assertNumQueries(2):
            userreports = enrolled_students_features(course.id, query_features)
        self.assertEqual(len([r for r in userreports if r['username'] in cohorted_usernames]), len(cohorted_students))
        self.assertEqual(len([r for r in userreports if r['username'] == non_cohorted_student.username]), 1)
        for report in userreports:
            self.assertEqual(set(report.keys()), set(query_features))
            if report['username'] in cohorted_usernames:
                self.assertEqual(report['cohort'], cohort.name)
            else:
                self.assertEqual(report['cohort'], '[unassigned]')

    def test_available_features(self):
        self.assertEqual(len(AVAILABLE_FEATURES), len(STUDENT_FEATURES + PROFILE_FEATURES))
        self.assertEqual(set(AVAILABLE_FEATURES), set(STUDENT_FEATURES + PROFILE_FEATURES))

    def test_list_may_enroll(self):
        may_enroll = list_may_enroll(self.course_key, ['email'])
        self.assertEqual(len(may_enroll), len(self.students_who_may_enroll) - len(self.users))
        email_adresses = [student.email for student in self.students_who_may_enroll]
        for student in may_enroll:
            self.assertEqual(student.keys(), ['email'])
            self.assertIn(student['email'], email_adresses)

    def test_get_student_exam_attempt_features(self):
        query_features = [
            'user_email',
            'exam_name',
            'allowed_time_limit_mins',
            'is_sample_attempt',
            'started_at',
            'completed_at',
            'status',
        ]

        proctored_exam_id = create_exam(self.course_key, 'Test Content', 'Test Exam', 1)
        ProctoredExamStudentAttempt.create_exam_attempt(
            proctored_exam_id, self.users[0].id, '', 1,
            'Test Code 1', True, False, 'ad13'
        )
        ProctoredExamStudentAttempt.create_exam_attempt(
            proctored_exam_id, self.users[1].id, '', 2,
            'Test Code 2', True, False, 'ad13'
        )
        ProctoredExamStudentAttempt.create_exam_attempt(
            proctored_exam_id, self.users[2].id, '', 3,
            'Test Code 3', True, False, 'asd'
        )

        proctored_exam_attempts = get_proctored_exam_results(self.course_key, query_features)
        self.assertEqual(len(proctored_exam_attempts), 3)
        for proctored_exam_attempt in proctored_exam_attempts:
            self.assertEqual(set(proctored_exam_attempt.keys()), set(query_features))


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class TestCourseSaleRecordsAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic course sale records analytics functions. """
    def setUp(self):
        """
        Fixtures.
        """
        super(TestCourseSaleRecordsAnalyticsBasic, self).setUp()
        self.course = CourseFactory.create()
        self.cost = 40
        self.course_mode = CourseMode(
            course_id=self.course.id, mode_slug="honor",
            mode_display_name="honor cert", min_price=self.cost
        )
        self.course_mode.save()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def test_course_sale_features(self):

        query_features = [
            'company_name', 'company_contact_name', 'company_contact_email', 'total_codes', 'total_used_codes',
            'total_amount', 'created', 'customer_reference_number', 'recipient_name', 'recipient_email',
            'created_by', 'internal_reference', 'invoice_number', 'codes', 'course_id'
        ]

        #create invoice
        sale_invoice = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName',
            company_contact_email='test@company.com', recipient_name='Testw_1', recipient_email='test2@test.com',
            customer_reference_number='2Fwe23S', internal_reference="ABC", course_id=self.course.id
        )
        invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=sale_invoice,
            qty=1,
            unit_price=1234.32,
            course_id=self.course.id
        )
        for i in range(5):
            course_code = CourseRegistrationCode(
                code="test_code{}".format(i), course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor, invoice=sale_invoice, invoice_item=invoice_item, mode_slug='honor'
            )
            course_code.save()

        course_sale_records_list = sale_record_features(self.course.id, query_features)

        for sale_record in course_sale_records_list:
            self.assertEqual(sale_record['total_amount'], sale_invoice.total_amount)
            self.assertEqual(sale_record['recipient_email'], sale_invoice.recipient_email)
            self.assertEqual(sale_record['recipient_name'], sale_invoice.recipient_name)
            self.assertEqual(sale_record['company_name'], sale_invoice.company_name)
            self.assertEqual(sale_record['company_contact_name'], sale_invoice.company_contact_name)
            self.assertEqual(sale_record['company_contact_email'], sale_invoice.company_contact_email)
            self.assertEqual(sale_record['internal_reference'], sale_invoice.internal_reference)
            self.assertEqual(sale_record['customer_reference_number'], sale_invoice.customer_reference_number)
            self.assertEqual(sale_record['invoice_number'], sale_invoice.id)
            self.assertEqual(sale_record['created_by'], self.instructor)
            self.assertEqual(sale_record['total_used_codes'], 0)
            self.assertEqual(sale_record['total_codes'], 5)

    def test_course_sale_no_codes(self):

        query_features = [
            'company_name', 'company_contact_name', 'company_contact_email', 'total_codes', 'total_used_codes',
            'total_amount', 'created', 'customer_reference_number', 'recipient_name', 'recipient_email',
            'created_by', 'internal_reference', 'invoice_number', 'codes', 'course_id'
        ]

        #create invoice
        sale_invoice = Invoice.objects.create(
            total_amount=0.00, company_name='Test1', company_contact_name='TestName',
            company_contact_email='test@company.com', recipient_name='Testw_1', recipient_email='test2@test.com',
            customer_reference_number='2Fwe23S', internal_reference="ABC", course_id=self.course.id
        )
        CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=sale_invoice,
            qty=0,
            unit_price=0.00,
            course_id=self.course.id
        )

        course_sale_records_list = sale_record_features(self.course.id, query_features)

        for sale_record in course_sale_records_list:
            self.assertEqual(sale_record['total_amount'], sale_invoice.total_amount)
            self.assertEqual(sale_record['recipient_email'], sale_invoice.recipient_email)
            self.assertEqual(sale_record['recipient_name'], sale_invoice.recipient_name)
            self.assertEqual(sale_record['company_name'], sale_invoice.company_name)
            self.assertEqual(sale_record['company_contact_name'], sale_invoice.company_contact_name)
            self.assertEqual(sale_record['company_contact_email'], sale_invoice.company_contact_email)
            self.assertEqual(sale_record['internal_reference'], sale_invoice.internal_reference)
            self.assertEqual(sale_record['customer_reference_number'], sale_invoice.customer_reference_number)
            self.assertEqual(sale_record['invoice_number'], sale_invoice.id)
            self.assertEqual(sale_record['created_by'], None)
            self.assertEqual(sale_record['total_used_codes'], 0)
            self.assertEqual(sale_record['total_codes'], 0)

    def test_sale_order_features_with_discount(self):
        """
         Test Order Sales Report CSV
        """
        query_features = [
            ('id', 'Order Id'),
            ('company_name', 'Company Name'),
            ('company_contact_name', 'Company Contact Name'),
            ('company_contact_email', 'Company Contact Email'),
            ('total_amount', 'Total Amount'),
            ('total_codes', 'Total Codes'),
            ('total_used_codes', 'Total Used Codes'),
            ('logged_in_username', 'Login Username'),
            ('logged_in_email', 'Login User Email'),
            ('purchase_time', 'Date of Sale'),
            ('customer_reference_number', 'Customer Reference Number'),
            ('recipient_name', 'Recipient Name'),
            ('recipient_email', 'Recipient Email'),
            ('bill_to_street1', 'Street 1'),
            ('bill_to_street2', 'Street 2'),
            ('bill_to_city', 'City'),
            ('bill_to_state', 'State'),
            ('bill_to_postalcode', 'Postal Code'),
            ('bill_to_country', 'Country'),
            ('order_type', 'Order Type'),
            ('status', 'Order Item Status'),
            ('coupon_code', 'Coupon Code'),
            ('unit_cost', 'Unit Price'),
            ('list_price', 'List Price'),
            ('codes', 'Registration Codes'),
            ('course_id', 'Course Id')
        ]
        # add the coupon code for the course
        coupon = Coupon(
            code='test_code',
            description='test_description',
            course_id=self.course.id,
            percentage_discount='10',
            created_by=self.instructor,
            is_active=True
        )
        coupon.save()
        order = Order.get_cart_for_user(self.instructor)
        order.order_type = 'business'
        order.save()
        order.add_billing_details(
            company_name='Test Company',
            company_contact_name='Test',
            company_contact_email='test@123',
            recipient_name='R1', recipient_email='',
            customer_reference_number='PO#23'
        )
        CourseRegCodeItem.add_to_order(order, self.course.id, 4)
        # apply the coupon code to the item in the cart
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': coupon.code})
        self.assertEqual(resp.status_code, 200)
        order.purchase()

        # get the updated item
        item = order.orderitem_set.all().select_subclasses()[0]
        # get the redeemed coupon information
        coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(order=order)

        db_columns = [x[0] for x in query_features]
        sale_order_records_list = sale_order_record_features(self.course.id, db_columns)

        for sale_order_record in sale_order_records_list:
            self.assertEqual(sale_order_record['recipient_email'], order.recipient_email)
            self.assertEqual(sale_order_record['recipient_name'], order.recipient_name)
            self.assertEqual(sale_order_record['company_name'], order.company_name)
            self.assertEqual(sale_order_record['company_contact_name'], order.company_contact_name)
            self.assertEqual(sale_order_record['company_contact_email'], order.company_contact_email)
            self.assertEqual(sale_order_record['customer_reference_number'], order.customer_reference_number)
            self.assertEqual(sale_order_record['unit_cost'], item.unit_cost)
            self.assertEqual(sale_order_record['list_price'], item.list_price)
            self.assertEqual(sale_order_record['status'], item.status)
            self.assertEqual(sale_order_record['coupon_code'], coupon_redemption[0].coupon.code)

    def test_sale_order_features_without_discount(self):
        """
         Test Order Sales Report CSV
        """
        query_features = [
            ('id', 'Order Id'),
            ('company_name', 'Company Name'),
            ('company_contact_name', 'Company Contact Name'),
            ('company_contact_email', 'Company Contact Email'),
            ('total_amount', 'Total Amount'),
            ('total_codes', 'Total Codes'),
            ('total_used_codes', 'Total Used Codes'),
            ('logged_in_username', 'Login Username'),
            ('logged_in_email', 'Login User Email'),
            ('purchase_time', 'Date of Sale'),
            ('customer_reference_number', 'Customer Reference Number'),
            ('recipient_name', 'Recipient Name'),
            ('recipient_email', 'Recipient Email'),
            ('bill_to_street1', 'Street 1'),
            ('bill_to_street2', 'Street 2'),
            ('bill_to_city', 'City'),
            ('bill_to_state', 'State'),
            ('bill_to_postalcode', 'Postal Code'),
            ('bill_to_country', 'Country'),
            ('order_type', 'Order Type'),
            ('status', 'Order Item Status'),
            ('coupon_code', 'Coupon Code'),
            ('unit_cost', 'Unit Price'),
            ('list_price', 'List Price'),
            ('codes', 'Registration Codes'),
            ('course_id', 'Course Id'),
            ('quantity', 'Quantity'),
            ('total_discount', 'Total Discount'),
            ('total_amount', 'Total Amount Paid'),
        ]
        # add the coupon code for the course
        order = Order.get_cart_for_user(self.instructor)
        order.order_type = 'business'
        order.save()
        order.add_billing_details(
            company_name='Test Company',
            company_contact_name='Test',
            company_contact_email='test@123',
            recipient_name='R1', recipient_email='',
            customer_reference_number='PO#23'
        )
        CourseRegCodeItem.add_to_order(order, self.course.id, 4)
        order.purchase()

        # get the updated item
        item = order.orderitem_set.all().select_subclasses()[0]

        db_columns = [x[0] for x in query_features]
        sale_order_records_list = sale_order_record_features(self.course.id, db_columns)

        for sale_order_record in sale_order_records_list:
            self.assertEqual(sale_order_record['recipient_email'], order.recipient_email)
            self.assertEqual(sale_order_record['recipient_name'], order.recipient_name)
            self.assertEqual(sale_order_record['company_name'], order.company_name)
            self.assertEqual(sale_order_record['company_contact_name'], order.company_contact_name)
            self.assertEqual(sale_order_record['company_contact_email'], order.company_contact_email)
            self.assertEqual(sale_order_record['customer_reference_number'], order.customer_reference_number)
            self.assertEqual(sale_order_record['unit_cost'], item.unit_cost)
            # Make sure list price is not None and matches the unit price since no discount was applied.
            self.assertIsNotNone(sale_order_record['list_price'])
            self.assertEqual(sale_order_record['list_price'], item.unit_cost)
            self.assertEqual(sale_order_record['status'], item.status)
            self.assertEqual(sale_order_record['coupon_code'], 'N/A')
            self.assertEqual(sale_order_record['total_amount'], item.unit_cost * item.qty)
            self.assertEqual(sale_order_record['total_discount'], 0)
            self.assertEqual(sale_order_record['quantity'], item.qty)


class TestCourseRegistrationCodeAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic course registration codes analytics functions. """

    def setUp(self):
        """
        Fixtures.
        """
        super(TestCourseRegistrationCodeAnalyticsBasic, self).setUp()
        self.course = CourseFactory.create()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')
        CourseSalesAdminRole(self.course.id).add_users(self.instructor)

        # Create a paid course mode.
        mode = CourseModeFactory.create()
        mode.course_id = self.course.id
        mode.min_price = 1
        mode.save()

        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 12, 'company_name': 'Test Group', 'unit_price': 122.45,
            'company_contact_name': 'TestName', 'company_contact_email': 'test@company.com', 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

    def test_course_registration_features(self):
        query_features = [
            'code', 'redeem_code_url', 'course_id', 'company_name', 'created_by',
            'redeemed_by', 'invoice_id', 'purchaser', 'customer_reference_number', 'internal_reference'
        ]
        order = Order(user=self.instructor, status='purchased')
        order.save()

        registration_code_redemption = RegistrationCodeRedemption(
            registration_code_id=1, redeemed_by=self.instructor
        )
        registration_code_redemption.save()
        registration_codes = CourseRegistrationCode.objects.all()
        course_registration_list = course_registration_features(query_features, registration_codes, csv_type='download')
        self.assertEqual(len(course_registration_list), len(registration_codes))
        for course_registration in course_registration_list:
            self.assertEqual(set(course_registration.keys()), set(query_features))
            self.assertIn(course_registration['code'], [registration_code.code for registration_code in registration_codes])
            self.assertIn(
                course_registration['course_id'],
                [registration_code.course_id.to_deprecated_string() for registration_code in registration_codes]
            )
            self.assertIn(
                course_registration['company_name'],
                [
                    registration_code.invoice_item.invoice.company_name
                    for registration_code in registration_codes
                ]
            )
            self.assertIn(
                course_registration['invoice_id'],
                [
                    registration_code.invoice_item.invoice_id
                    for registration_code in registration_codes
                ]
            )

    def test_coupon_codes_features(self):
        query_features = [
            'course_id', 'percentage_discount', 'code_redeemed_count', 'description', 'expiration_date',
            'total_discounted_amount', 'total_discounted_seats'
        ]
        for i in range(10):
            coupon = Coupon(
                code='test_code{0}'.format(i),
                description='test_description',
                course_id=self.course.id, percentage_discount='{0}'.format(i),
                created_by=self.instructor,
                is_active=True
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

        active_coupons = Coupon.objects.filter(
            Q(course_id=self.course.id),
            Q(is_active=True),
            Q(expiration_date__gt=datetime.datetime.now(pytz.UTC)) |
            Q(expiration_date__isnull=True)
        )
        active_coupons_list = coupon_codes_features(query_features, active_coupons, self.course.id)
        self.assertEqual(len(active_coupons_list), len(active_coupons))
        for active_coupon in active_coupons_list:
            self.assertEqual(set(active_coupon.keys()), set(query_features))
            self.assertIn(active_coupon['percentage_discount'], [coupon.percentage_discount for coupon in active_coupons])
            self.assertIn(active_coupon['description'], [coupon.description for coupon in active_coupons])
            if active_coupon['expiration_date']:
                self.assertIn(active_coupon['expiration_date'], [coupon.display_expiry_date for coupon in active_coupons])
            self.assertIn(
                active_coupon['course_id'],
                [coupon.course_id.to_deprecated_string() for coupon in active_coupons]
            )


class TestStudentResponsesAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic student responses analytics function. """
    MODULESTORE = TEST_DATA_MIXED_GRADED_MODULESTORE

    def create_student(self):
        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

    def test_empty_course(self):
        self.course = CourseFactory.create()
        self.create_student()

        datarows = list(student_responses(self.course))
        self.assertEqual(datarows, [])

    def test_full_course_no_students(self):
        self.course = get_course(CourseKey.from_string('edX/graded/2012_Fall'))

        datarows = list(student_responses(self.course))
        self.assertEqual(datarows, [])

    def test_invalid_module_state(self):
        self.course = get_course(CourseKey.from_string('edX/graded/2012_Fall'))
        self.problem_location = Location("edX", "graded", "2012_Fall", "problem", "H1P2")

        self.create_student()
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=self.problem_location,
            student=self.student,
            grade=0,
            state=u'{"student_answers":{"fake-problem":"No idea"}}}'
        )

        datarows = list(student_responses(self.course))
        #Invalid module state response will be skipped, so datarows should be empty
        self.assertEqual(len(datarows), 0)

    def test_problem_with_student_answer_and_answers(self):
        self.course = CourseFactory.create(
            display_name=u'test course',
        )
        section = ItemFactory.create(
            parent_location=self.course.location,
            category='chapter',
            display_name=u'test section',
        )
        sub_section = ItemFactory.create(
            parent_location=section.location,
            category='sequential',
            display_name=u'test subsection',
        )
        unit = ItemFactory.create(
            parent_location=sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u'test unit',
        )
        problem = ItemFactory.create(
            parent_location=unit.location,
            category='problem',
            display_name=u'test problem',
        )
        submit_and_compare_valid_state = ItemFactory.create(
            parent_location=unit.location,
            category='submit-and-compare',
            display_name=u'test submit_and_compare1',
        )
        submit_and_compare_invalid_state = ItemFactory.create(
            parent_location=unit.location,
            category='submit-and-compare',
            display_name=u'test submit_and_compare2',
        )
        content_library = ItemFactory.create(
            parent_location=unit.location,
            category='library_content',
            display_name=u'test content_library',
        )
        library_problem = ItemFactory.create(
            parent_location=content_library.location,
            category='problem',
        )

        self.create_student()

        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=problem.location,
            student=self.student,
            grade=0,
            state=u'{"student_answers":{"problem_id":"student response1"}}',
        )
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=submit_and_compare_valid_state.location,
            student=self.student,
            grade=1,
            state=u'{"student_answer": "student response2"}',
        )
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=submit_and_compare_invalid_state.location,
            student=self.student,
            grade=1,
            state=u'{"answer": {"problem_id": "123"}}',
        )
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=library_problem.location,
            student=self.student,
            grade=0,
            state=u'{"student_answers":{"problem_id":"content library response1"}}',
        )

        course_with_children = modulestore().get_course(self.course.id, depth=4)
        datarows = list(student_responses(course_with_children))
        self.assertEqual(datarows[0][-1], u'problem_id=student response1')
        self.assertEqual(datarows[1][-1], u'student response2')
        self.assertEqual(datarows[2][-1], None)
        self.assertEqual(datarows[3][-1], u'problem_id=content library response1')

    def test_problem_with_no_answer(self):
        self.course = get_course(CourseKey.from_string('edX/graded/2012_Fall'))
        problem_location = Location('edX', 'graded', '2012_Fall', 'problem', 'H1P2')

        self.create_student()
        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=problem_location,
            student=self.student,
            grade=0,
            state=u'{"answer": {"problem_id": "123"}}',
        )

        datarows = list(student_responses(self.course))
        self.assertEqual(datarows[0][-1], None)
