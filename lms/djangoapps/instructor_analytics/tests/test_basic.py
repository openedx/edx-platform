"""
Tests for instructor.basic
"""

from django.test import TestCase
from student.models import CourseEnrollment
from django.core.urlresolvers import reverse
from mock import patch
from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import (
    CourseRegistrationCode, RegistrationCodeRedemption, Order,
    Invoice, Coupon, CourseRegCodeItem, CouponRedemption
)
from course_modes.models import CourseMode
from instructor_analytics.basic import (
    sale_record_features, sale_order_record_features, enrolled_students_features, course_registration_features,
    coupon_codes_features, AVAILABLE_FEATURES, STUDENT_FEATURES, PROFILE_FEATURES
)
from course_groups.tests.helpers import CohortFactory
from course_groups.models import CourseUserGroup
from courseware.tests.factories import InstructorFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TestAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic analytics functions. """

    def setUp(self):
        super(TestAnalyticsBasic, self).setUp()
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
        with self.assertNumQueries(1):
            userreports = enrolled_students_features(self.course_key, query_features)
        self.assertEqual(len(userreports), len(self.users))
        for userreport in userreports:
            self.assertEqual(set(userreport.keys()), set(query_features))
            self.assertIn(userreport['username'], [user.username for user in self.users])
            self.assertIn(userreport['email'], [user.email for user in self.users])
            self.assertIn(userreport['name'], [user.profile.name for user in self.users])

    def test_enrolled_students_features_keys_cohorted(self):
        course = CourseFactory.create(course_key=self.course_key)
        course.cohort_config = {'cohorted': True, 'auto_cohort': True, 'auto_cohort_groups': ['cohort']}
        self.store.update_item(course, self.instructor.id)
        cohort = CohortFactory.create(name='cohort', course_id=course.id)
        cohorted_students = [UserFactory.create() for _ in xrange(10)]
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

    def test_sale_order_features(self):
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
            self.assertEqual(sale_order_record['total_used_codes'], order.registrationcoderedemption_set.all().count())
            self.assertEqual(sale_order_record['total_codes'], len(CourseRegistrationCode.objects.filter(order=order)))
            self.assertEqual(sale_order_record['unit_cost'], item.unit_cost)
            self.assertEqual(sale_order_record['list_price'], item.list_price)
            self.assertEqual(sale_order_record['status'], item.status)
            self.assertEqual(sale_order_record['coupon_code'], coupon_redemption[0].coupon.code)


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
                code='test_code{0}'.format(i),
                description='test_description',
                course_id=self.course.id, percentage_discount='{0}'.format(i),
                created_by=self.instructor,
                is_active=True
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
