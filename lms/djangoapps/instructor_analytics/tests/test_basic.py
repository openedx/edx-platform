"""
Tests for instructor.basic
"""

from django.test import TestCase
from student.models import CourseEnrollment
from django.core.urlresolvers import reverse
from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import CourseRegistrationCode, RegistrationCodeRedemption, Order

from instructor_analytics.basic import enrolled_students_features, course_registration_features, AVAILABLE_FEATURES, STUDENT_FEATURES, PROFILE_FEATURES
from courseware.tests.factories import InstructorFactory
from xmodule.modulestore.tests.factories import CourseFactory


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


class TestCourseRegistrationCodeAnalyticsBasic(TestCase):
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
            'total-registration-codes': 12, 'company_name': 'Test Group', 'sale_price': 122.45,
            'contact_name': 'Test123', 'contact_email': 'test@123.com',
            'tax': '123A23F', 'reference': '', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data, **{'HTTP_HOST': 'localhost'})
        self.assertEqual(response.status_code, 200, response.content)

    def test_course_registration_features(self):
        query_features = [
            'code', 'course_id', 'company_name', 'created_by',
            'redeemed_by', 'invoice_id', 'purchaser', 'company_reference', 'internal_reference'
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
