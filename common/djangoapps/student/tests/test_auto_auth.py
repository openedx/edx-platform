from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django_comment_common.models import (
    Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_STUDENT)
from django_comment_common.utils import seed_permissions_roles
from student.models import CourseEnrollment, UserProfile
from util.testing import UrlResetMixin
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from mock import patch


class AutoAuthEnabledTestCase(UrlResetMixin, TestCase):
    """
    Tests for the Auto auth view that we have for load testing.
    """

    @patch.dict("django.conf.settings.FEATURES", {"AUTOMATIC_AUTH_FOR_TESTING": True})
    def setUp(self):
        # Patching the settings.FEATURES['AUTOMATIC_AUTH_FOR_TESTING']
        # value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(AutoAuthEnabledTestCase, self).setUp()
        self.url = '/auto_auth'
        self.client = Client()
        self.course_id = 'edX/Test101/2014_Spring'
        self.course_key = SlashSeparatedCourseKey.from_deprecated_string(self.course_id)

    def test_create_user(self):
        """
        Test that user gets created when visiting the page.
        """
        self._auto_auth()
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.all()[0].is_active)

    def test_create_same_user(self):
        self._auto_auth(username='test')
        self._auto_auth(username='test')
        self.assertEqual(User.objects.count(), 1)

    def test_create_multiple_users(self):
        """
        Test to make sure multiple users are created.
        """
        self._auto_auth()
        self._auto_auth()
        self.assertEqual(User.objects.all().count(), 2)

    def test_create_defined_user(self):
        """
        Test that the user gets created with the correct attributes
        when they are passed as parameters on the auto-auth page.
        """
        self._auto_auth(
            username='robot', password='test',
            email='robot@edx.org', full_name="Robot Name"
        )

        # Check that the user has the correct info
        user = User.objects.get(username='robot')
        self.assertEqual(user.username, 'robot')
        self.assertTrue(user.check_password('test'))
        self.assertEqual(user.email, 'robot@edx.org')

        # Check that the user has a profile
        user_profile = UserProfile.objects.get(user=user)
        self.assertEqual(user_profile.name, "Robot Name")

        # By default, the user should not be global staff
        self.assertFalse(user.is_staff)

    def test_create_staff_user(self):

        # Create a staff user
        self._auto_auth(username='test', staff='true')
        user = User.objects.get(username='test')
        self.assertTrue(user.is_staff)

        # Revoke staff privileges
        self._auto_auth(username='test', staff='false')
        user = User.objects.get(username='test')
        self.assertFalse(user.is_staff)

    def test_course_enrollment(self):

        # Create a user and enroll in a course
        self._auto_auth(username='test', course_id=self.course_id)

        # Check that a course enrollment was created for the user
        self.assertEqual(CourseEnrollment.objects.count(), 1)
        enrollment = CourseEnrollment.objects.get(course_id=self.course_key)
        self.assertEqual(enrollment.user.username, "test")

    def test_double_enrollment(self):

        # Create a user and enroll in a course
        self._auto_auth(username='test', course_id=self.course_id)

        # Make the same call again, re-enrolling the student in the same course
        self._auto_auth(username='test', course_id=self.course_id)

        # Check that only one course enrollment was created for the user
        self.assertEqual(CourseEnrollment.objects.count(), 1)
        enrollment = CourseEnrollment.objects.get(course_id=self.course_key)
        self.assertEqual(enrollment.user.username, "test")

    def test_set_roles(self):
        seed_permissions_roles(self.course_key)
        course_roles = dict((r.name, r) for r in Role.objects.filter(course_id=self.course_key))
        self.assertEqual(len(course_roles), 4)  # sanity check

        # Student role is assigned by default on course enrollment.
        self._auto_auth(username='a_student', course_id=self.course_id)
        user = User.objects.get(username='a_student')
        user_roles = user.roles.all()
        self.assertEqual(len(user_roles), 1)
        self.assertEqual(user_roles[0], course_roles[FORUM_ROLE_STUDENT])

        self._auto_auth(username='a_moderator', course_id=self.course_id, roles='Moderator')
        user = User.objects.get(username='a_moderator')
        user_roles = user.roles.all()
        self.assertEqual(
            set(user_roles),
            set([course_roles[FORUM_ROLE_STUDENT],
                course_roles[FORUM_ROLE_MODERATOR]]))

        # check multiple roles work.
        self._auto_auth(username='an_admin', course_id=self.course_id,
                        roles='{},{}'.format(FORUM_ROLE_MODERATOR, FORUM_ROLE_ADMINISTRATOR))
        user = User.objects.get(username='an_admin')
        user_roles = user.roles.all()
        self.assertEqual(
            set(user_roles),
            set([course_roles[FORUM_ROLE_STUDENT],
                course_roles[FORUM_ROLE_MODERATOR],
                course_roles[FORUM_ROLE_ADMINISTRATOR]]))

    def _auto_auth(self, **params):
        """
        Make a request to the auto-auth end-point and check
        that the response is successful.
        """
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)

        # Check that session and CSRF are set in the response
        for cookie in ['csrftoken', 'sessionid']:
            self.assertIn(cookie, response.cookies)  # pylint: disable=E1103
            self.assertTrue(response.cookies[cookie].value)  # pylint: disable=E1103


class AutoAuthDisabledTestCase(UrlResetMixin, TestCase):
    """
    Test that the page is inaccessible with default settings
    """

    @patch.dict("django.conf.settings.FEATURES", {"AUTOMATIC_AUTH_FOR_TESTING": False})
    def setUp(self):
        # Patching the settings.FEATURES['AUTOMATIC_AUTH_FOR_TESTING']
        # value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(AutoAuthDisabledTestCase, self).setUp()
        self.url = '/auto_auth'
        self.client = Client()

    def test_auto_auth_disabled(self):
        """
        Make sure automatic authentication is disabled.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
