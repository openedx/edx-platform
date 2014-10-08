"""
Tests for instructor.basic
"""

from django.test import TestCase
from student.models import CourseEnrollment
from django.core.urlresolvers import reverse
from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import CourseRegistrationCode, RegistrationCodeRedemption, Order, Invoice, Coupon

from instructor_analytics.basic import (
    sale_record_features, enrolled_students_features, course_registration_features, coupon_codes_features,
    AVAILABLE_FEATURES, STUDENT_FEATURES, PROFILE_FEATURES
)
from courseware.tests.factories import InstructorFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TestAnalyticsBasic(TestCase):
    """ Test basic analytics functions. """

    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('robot', 'course', 'id')
        self.users = tuple(UserFactory() for _ in xrange(30))
        self.ces = tuple(CourseEnrollment.enroll(user, self.course_key)
                         for user in self.users)
        self.instructor = InstructorFactory(course_key=self.course_key)

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
        userreports = enrolled_students_features(self.course_key, query_features)
        self.assertEqual(len(userreports), len(self.users))
        for userreport in userreports:
            self.assertEqual(set(userreport.keys()), set(query_features))
            self.assertIn(userreport['username'], [user.username for user in self.users])
            self.assertIn(userreport['email'], [user.email for user in self.users])
            self.assertIn(userreport['name'], [user.profile.name for user in self.users])

    def test_available_features(self):
        self.assertEqual(len(AVAILABLE_FEATURES), len(STUDENT_FEATURES + PROFILE_FEATURES))
        self.assertEqual(set(AVAILABLE_FEATURES), set(STUDENT_FEATURES + PROFILE_FEATURES))


class TestCourseSaleRecordsAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic course sale records analytics functions. """
    def setUp(self):
        """
        Fixtures.
        """
        self.course = CourseFactory.create()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def test_course_sale_features(self):

        query_features = [
            'company_name', 'company_contact_name', 'company_contact_email', 'total_codes', 'total_used_codes',
            'total_amount', 'created_at', 'customer_reference_number', 'recipient_name', 'recipient_email',
            'created_by', 'internal_reference', 'invoice_number', 'codes', 'course_id'
        ]

        #create invoice
        sale_invoice = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName',
            company_contact_email='test@company.com', recipient_name='Testw_1', recipient_email='test2@test.com',
            customer_reference_number='2Fwe23S', internal_reference="ABC", course_id=self.course.id
        )
        for i in range(5):
            course_code = CourseRegistrationCode(
                code="test_code{}".format(i), course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor, invoice=sale_invoice
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


class TestCourseRegistrationCodeAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic course registration codes analytics functions. """
    def setUp(self):
        """
        Fixtures.
        """
        self.course = CourseFactory.create()
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 12, 'company_name': 'Test Group', 'sale_price': 122.45,
            'company_contact_name': 'TestName', 'company_contact_email': 'test@company.com', 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street', 'address_line_2': '',
            'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

    def test_course_registration_features(self):
        query_features = [
            'code', 'course_id', 'company_name', 'created_by',
            'redeemed_by', 'invoice_id', 'purchaser', 'customer_reference_number', 'internal_reference'
        ]
        order = Order(user=self.instructor, status='purchased')
        order.save()

        registration_code_redemption = RegistrationCodeRedemption(
            order=order, registration_code_id=1, redeemed_by=self.instructor
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
                [getattr(registration_code.invoice, 'company_name') for registration_code in registration_codes]
            )
            self.assertIn(
                course_registration['invoice_id'],
                [registration_code.invoice_id for registration_code in registration_codes]
            )

    def test_coupon_codes_features(self):
        query_features = [
            'course_id', 'percentage_discount', 'code_redeemed_count', 'description'
        ]
        for i in range(10):
            coupon = Coupon(
                code='test_code{0}'.format(i), description='test_description', course_id=self.course.id,
                percentage_discount='{0}'.format(i), created_by=self.instructor, is_active=True
            )
            coupon.save()
        active_coupons = Coupon.objects.filter(course_id=self.course.id, is_active=True)
        active_coupons_list = coupon_codes_features(query_features, active_coupons)
        self.assertEqual(len(active_coupons_list), len(active_coupons))
        for active_coupon in active_coupons_list:
            self.assertEqual(set(active_coupon.keys()), set(query_features))
            self.assertIn(active_coupon['percentage_discount'], [coupon.percentage_discount for coupon in active_coupons])
            self.assertIn(active_coupon['description'], [coupon.description for coupon in active_coupons])
            self.assertIn(
                active_coupon['course_id'],
                [coupon.course_id.to_deprecated_string() for coupon in active_coupons]
            )
