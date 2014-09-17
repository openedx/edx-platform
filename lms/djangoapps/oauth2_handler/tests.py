# pylint: disable=missing-docstring
from django.test.utils import override_settings
from django.test import TestCase

from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from lang_pref import LANGUAGE_KEY
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.models import anonymous_id_for_user
from student.roles import CourseStaffRole, CourseInstructorRole
from student.tests.factories import UserFactory, UserProfileFactory
from user_api.models import UserPreference

# Will also run default tests for IDTokens and UserInfo
from oauth2_provider.tests import IDTokenTestCase, UserInfoTestCase


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class BaseTestMixin(TestCase):
    profile = None

    def setUp(self):
        super(BaseTestMixin, self).setUp()

        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.course_id = unicode(self.course_key)

        self.user_factory = UserFactory
        self.set_user(self.make_user())

    def set_user(self, user):
        super(BaseTestMixin, self).set_user(user)
        self.profile = UserProfileFactory(user=self.user)


class IDTokenTest(BaseTestMixin, IDTokenTestCase):
    def test_sub_claim(self):
        scopes, claims = self.get_new_id_token_values('openid')
        self.assertIn('openid', scopes)

        sub = claims['sub']

        expected_sub = anonymous_id_for_user(self.user, None)
        self.assertEqual(sub, expected_sub)

    def test_user_without_locale_claim(self):
        scopes, claims = self.get_new_id_token_values('openid profile')
        self.assertIn('profile', scopes)
        self.assertNotIn('locale', claims)

    def test_user_wit_locale_claim(self):
        language = 'en'
        UserPreference.set_preference(self.user, LANGUAGE_KEY, language)
        scopes, claims = self.get_new_id_token_values('openid profile')

        self.assertIn('profile', scopes)

        locale = claims['locale']
        self.assertEqual(language, locale)

    def test_no_special_course_access(self):
        scopes, claims = self.get_new_id_token_values('openid course_instructor course_staff')

        self.assertNotIn('course_staff', scopes)
        self.assertNotIn('staff_courses', claims)

        self.assertNotIn('course_instructor', scopes)
        self.assertNotIn('instructor_courses', claims)

    def test_course_staff_courses(self):
        CourseStaffRole(self.course_key).add_users(self.user)

        scopes, claims = self.get_new_id_token_values('openid course_staff')

        self.assertIn('course_staff', scopes)
        self.assertNotIn('staff_courses', claims)  # should not return courses in id_token

    def test_course_instructor_courses(self):
        CourseInstructorRole(self.course_key).add_users(self.user)

        scopes, claims = self.get_new_id_token_values('openid course_instructor')

        self.assertIn('course_instructor', scopes)
        self.assertNotIn('instructor_courses', claims)   # should not return courses in id_token


class UserInfoTest(BaseTestMixin, UserInfoTestCase):
    def token_for_scope(self, scope):
        full_scope = 'openid %s' % scope
        self.set_access_token_scope(full_scope)

        token = self.access_token.token  # pylint: disable=no-member
        return full_scope, token

    def get_with_scope(self, scope):
        scope, token = self.token_for_scope(scope)
        result, claims = self.get_userinfo(token, scope)
        self.assertEqual(result.status_code, 200)

        return claims

    def get_with_claim_value(self, scope, claim, values):
        _full_scope, token = self.token_for_scope(scope)

        result, claims = self.get_userinfo(
            token,
            claims={claim: {'values': values}}
        )

        self.assertEqual(result.status_code, 200)
        return claims

    def test_request_staff_courses_using_scope(self):
        CourseStaffRole(self.course_key).add_users(self.user)
        claims = self.get_with_scope('course_staff')

        courses = claims['staff_courses']
        self.assertIn(self.course_id, courses)
        self.assertEqual(len(courses), 1)

    def test_request_instructor_courses_using_scope(self):
        CourseInstructorRole(self.course_key).add_users(self.user)
        claims = self.get_with_scope('course_instructor')

        courses = claims['instructor_courses']
        self.assertIn(self.course_id, courses)
        self.assertEqual(len(courses), 1)

    def test_request_staff_courses_with_claims(self):
        CourseStaffRole(self.course_key).add_users(self.user)

        values = [self.course_id, 'some_invalid_course']
        claims = self.get_with_claim_value('course_staff', 'staff_courses', values)
        self.assertEqual(len(claims), 2)

        courses = claims['staff_courses']
        self.assertIn(self.course_id, courses)
        self.assertEqual(len(courses), 1)

    def test_request_instructor_courses_with_claims(self):
        CourseInstructorRole(self.course_key).add_users(self.user)

        values = ['edX/toy/TT_2012_Fall', self.course_id, 'invalid_course_id']
        claims = self.get_with_claim_value('course_instructor', 'instructor_courses', values)
        self.assertEqual(len(claims), 2)

        courses = claims['instructor_courses']
        self.assertIn(self.course_id, courses)
        self.assertEqual(len(courses), 1)
