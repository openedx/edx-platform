"""
Tests for instructor.basic
"""

from django.test import TestCase
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import CourseRegistrationCode, RegistrationCodeRedemption, Order

from instructor_analytics.basic import enrolled_students_features, course_registration_features, AVAILABLE_FEATURES, STUDENT_FEATURES, PROFILE_FEATURES


class TestAnalyticsBasic(TestCase):
    """ Test basic analytics functions. """

    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('robot', 'course', 'id')
        self.users = tuple(UserFactory() for _ in xrange(30))
        self.ces = tuple(CourseEnrollment.enroll(user, self.course_key)
                         for user in self.users)

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

    def test_course_registration_features(self):
        query_features = ['code', 'course_id', 'transaction_group_name', 'created_by', 'redeemed_by']
        for i in range(5):
            course_code = CourseRegistrationCode(
                code="test_code{}".format(i), course_id=self.course_key.to_deprecated_string(),
                transaction_group_name='TestName', created_by=self.users[0]
            )
            course_code.save()

        order = Order(user=self.users[0], status='purchased')
        order.save()

        registration_code_redemption = RegistrationCodeRedemption(
            order=order, registration_code_id=1, redeemed_by=self.users[0]
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
                course_registration['transaction_group_name'],
                [registration_code.transaction_group_name for registration_code in registration_codes]
            )
