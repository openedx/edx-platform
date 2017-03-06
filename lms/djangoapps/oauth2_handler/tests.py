# pylint: disable=missing-docstring
from django.core.cache import cache
from django.test.utils import override_settings
from lang_pref import LANGUAGE_KEY

from xmodule.modulestore.tests.factories import (check_mongo_calls, CourseFactory)
from student.models import anonymous_id_for_user
from student.models import UserProfile
from student.roles import (CourseInstructorRole, CourseStaffRole, GlobalStaff,
                           OrgInstructorRole, OrgStaffRole)
from student.tests.factories import UserFactory, UserProfileFactory
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


# Will also run default tests for IDTokens and UserInfo
from edx_oauth2_provider.tests import IDTokenTestCase, UserInfoTestCase


class BaseTestMixin(ModuleStoreTestCase):
    profile = None

    def setUp(self):
        super(BaseTestMixin, self).setUp()
        self.course_key = CourseFactory.create(emit_signals=True).id
        self.course_id = unicode(self.course_key)
        self.user_factory = UserFactory
        self.set_user(self.make_user())

    def set_user(self, user):
        super(BaseTestMixin, self).set_user(user)
        self.profile = UserProfileFactory(user=self.user)


class IDTokenTest(BaseTestMixin, IDTokenTestCase):
    def setUp(self):
        super(IDTokenTest, self).setUp()

        # CourseAccessHandler uses the application cache.
        cache.clear()

    def test_sub_claim(self):
        scopes, claims = self.get_id_token_values('openid')
        self.assertIn('openid', scopes)

        sub = claims['sub']

        expected_sub = anonymous_id_for_user(self.user, None)
        self.assertEqual(sub, expected_sub)

    def test_user_name_claim(self):
        _scopes, claims = self.get_id_token_values('openid profile')
        claim_name = claims['name']

        user_profile = UserProfile.objects.get(user=self.user)
        user_name = user_profile.name

        self.assertEqual(claim_name, user_name)

    @override_settings(LANGUAGE_CODE='en')
    def test_user_without_locale_claim(self):
        scopes, claims = self.get_id_token_values('openid profile')
        self.assertIn('profile', scopes)
        self.assertEqual(claims['locale'], 'en')

    def test_user_with_locale_claim(self):
        language = 'en'
        set_user_preference(self.user, LANGUAGE_KEY, language)
        scopes, claims = self.get_id_token_values('openid profile')

        self.assertIn('profile', scopes)

        locale = claims['locale']
        self.assertEqual(language, locale)

    def test_no_special_course_access(self):
        with check_mongo_calls(0):
            scopes, claims = self.get_id_token_values('openid course_instructor course_staff')
        self.assertNotIn('course_staff', scopes)
        self.assertNotIn('staff_courses', claims)

        self.assertNotIn('course_instructor', scopes)
        self.assertNotIn('instructor_courses', claims)

    def test_course_staff_courses(self):
        CourseStaffRole(self.course_key).add_users(self.user)
        with check_mongo_calls(0):
            scopes, claims = self.get_id_token_values('openid course_staff')

        self.assertIn('course_staff', scopes)
        self.assertNotIn('staff_courses', claims)  # should not return courses in id_token

    def test_course_instructor_courses(self):
        with check_mongo_calls(0):
            CourseInstructorRole(self.course_key).add_users(self.user)

        scopes, claims = self.get_id_token_values('openid course_instructor')

        self.assertIn('course_instructor', scopes)
        self.assertNotIn('instructor_courses', claims)  # should not return courses in id_token

    def test_course_staff_courses_with_claims(self):
        CourseStaffRole(self.course_key).add_users(self.user)

        course_id = unicode(self.course_key)

        nonexistent_course_id = 'some/other/course'

        claims = {
            'staff_courses': {
                'values': [course_id, nonexistent_course_id],
                'essential': True,
            }
        }

        with check_mongo_calls(0):
            scopes, claims = self.get_id_token_values(scope='openid course_staff', claims=claims)

        self.assertIn('course_staff', scopes)
        self.assertIn('staff_courses', claims)
        self.assertEqual(len(claims['staff_courses']), 1)
        self.assertIn(course_id, claims['staff_courses'])
        self.assertNotIn(nonexistent_course_id, claims['staff_courses'])

    def test_permissions_scope(self):
        scopes, claims = self.get_id_token_values('openid profile permissions')
        self.assertIn('permissions', scopes)
        self.assertFalse(claims['administrator'])

        self.user.is_staff = True
        self.user.save()
        _scopes, claims = self.get_id_token_values('openid profile permissions')
        self.assertTrue(claims['administrator'])


class UserInfoTest(BaseTestMixin, UserInfoTestCase):
    def setUp(self):
        super(UserInfoTest, self).setUp()
        # create another course in the DB that only global staff have access to
        CourseFactory.create(emit_signals=True)

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

    def _assert_role_using_scope(self, scope, claim, assert_one_course=True):
        with check_mongo_calls(0):
            claims = self.get_with_scope(scope)
        self.assertEqual(len(claims), 2)
        courses = claims[claim]
        self.assertIn(self.course_id, courses)
        if assert_one_course:
            self.assertEqual(len(courses), 1)

    def test_request_global_staff_courses_using_scope(self):
        GlobalStaff().add_users(self.user)
        self._assert_role_using_scope('course_staff', 'staff_courses', assert_one_course=False)

    def test_request_org_staff_courses_using_scope(self):
        OrgStaffRole(self.course_key.org).add_users(self.user)
        self._assert_role_using_scope('course_staff', 'staff_courses')

    def test_request_org_instructor_courses_using_scope(self):
        OrgInstructorRole(self.course_key.org).add_users(self.user)
        self._assert_role_using_scope('course_instructor', 'instructor_courses')

    def test_request_staff_courses_using_scope(self):
        CourseStaffRole(self.course_key).add_users(self.user)
        self._assert_role_using_scope('course_staff', 'staff_courses')

    def test_request_instructor_courses_using_scope(self):
        CourseInstructorRole(self.course_key).add_users(self.user)
        self._assert_role_using_scope('course_instructor', 'instructor_courses')

    def _assert_role_using_claim(self, scope, claim):
        values = [self.course_id, 'some_invalid_course']
        with check_mongo_calls(0):
            claims = self.get_with_claim_value(scope, claim, values)
        self.assertEqual(len(claims), 2)

        courses = claims[claim]
        self.assertIn(self.course_id, courses)
        self.assertEqual(len(courses), 1)

    def test_request_global_staff_courses_with_claims(self):
        GlobalStaff().add_users(self.user)
        self._assert_role_using_claim('course_staff', 'staff_courses')

    def test_request_org_staff_courses_with_claims(self):
        OrgStaffRole(self.course_key.org).add_users(self.user)
        self._assert_role_using_claim('course_staff', 'staff_courses')

    def test_request_org_instructor_courses_with_claims(self):
        OrgInstructorRole(self.course_key.org).add_users(self.user)
        self._assert_role_using_claim('course_instructor', 'instructor_courses')

    def test_request_staff_courses_with_claims(self):
        CourseStaffRole(self.course_key).add_users(self.user)
        self._assert_role_using_claim('course_staff', 'staff_courses')

    def test_request_instructor_courses_with_claims(self):
        CourseInstructorRole(self.course_key).add_users(self.user)
        self._assert_role_using_claim('course_instructor', 'instructor_courses')

    def test_permissions_scope(self):
        claims = self.get_with_scope('permissions')
        self.assertIn('administrator', claims)
        self.assertFalse(claims['administrator'])

        self.user.is_staff = True
        self.user.save()
        claims = self.get_with_scope('permissions')
        self.assertTrue(claims['administrator'])
