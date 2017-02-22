"""
Helpers for courseware tests.
"""
import crum
import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory

from courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import Registration


class LoginEnrollmentTestCase(TestCase):
    """
    Provides support for user creation,
    activation, login, and course enrollment.
    """
    user = None

    def setup_user(self):
        """
        Create a user account, activate, and log in.
        """
        self.email = 'foo@test.com'
        self.password = 'bar'
        self.username = 'test'
        self.user = self.create_account(
            self.username,
            self.email,
            self.password,
        )
        # activate_user re-fetches and returns the activated user record
        self.user = self.activate_user(self.email)
        self.login(self.email, self.password)

    def assert_request_status_code(self, status_code, url, method="GET", **kwargs):
        make_request = getattr(self.client, method.lower())
        response = make_request(url, **kwargs)
        self.assertEqual(
            response.status_code, status_code,
            "{method} request to {url} returned status code {actual}, "
            "expected status code {expected}".format(
                method=method, url=url,
                actual=response.status_code, expected=status_code
            )
        )
        return response

    # ============ User creation and login ==============

    def login(self, email, password):
        """
        Login, check that the corresponding view's response has a 200 status code.
        """
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': password})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['success'])

    def logout(self):
        """
        Logout; check that the HTTP response code indicates redirection
        as expected.
        """
        # should redirect
        self.assert_request_status_code(302, reverse('logout'))

    def create_account(self, username, email, password):
        """
        Create the account and check that it worked.
        """
        url = reverse('create_account')
        request_data = {
            'username': username,
            'email': email,
            'password': password,
            'name': 'username',
            'terms_of_service': 'true',
            'honor_code': 'true',
        }
        resp = self.assert_request_status_code(200, url, method="POST", data=request_data)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], True)
        # Check both that the user is created, and inactive
        user = User.objects.get(email=email)
        self.assertFalse(user.is_active)
        return user

    def activate_user(self, email):
        """
        Look up the activation key for the user, then hit the activate view.
        No error checking.
        """
        activation_key = Registration.objects.get(user__email=email).activation_key
        # and now we try to activate
        url = reverse('activate', kwargs={'key': activation_key})
        self.assert_request_status_code(200, url)
        # Now make sure that the user is now actually activated
        user = User.objects.get(email=email)
        self.assertTrue(user.is_active)
        # And return the user we fetched.
        return user

    def enroll(self, course, verify=False):
        """
        Try to enroll and return boolean indicating result.
        `course` is an instance of CourseDescriptor.
        `verify` is an optional boolean parameter specifying whether we
        want to verify that the student was successfully enrolled
        in the course.
        """
        resp = self.client.post(reverse('change_enrollment'), {
            'enrollment_action': 'enroll',
            'course_id': course.id.to_deprecated_string(),
            'check_access': True,
        })
        result = resp.status_code == 200
        if verify:
            self.assertTrue(result)
        return result

    def unenroll(self, course):
        """
        Unenroll the currently logged-in user, and check that it worked.
        `course` is an instance of CourseDescriptor.
        """
        url = reverse('change_enrollment')
        request_data = {
            'enrollment_action': 'unenroll',
            'course_id': course.id.to_deprecated_string(),
        }
        self.assert_request_status_code(200, url, method="POST", data=request_data)


class CourseAccessTestMixin(TestCase):
    """
    Utility mixin for asserting access (or lack thereof) to courses.
    If relevant, also checks access for courses' corresponding CourseOverviews.
    """

    def assertCanAccessCourse(self, user, action, course):
        """
        Assert that a user has access to the given action for a given course.

        Test with both the given course and with a CourseOverview of the given
        course.

        Arguments:
            user (User): a user.
            action (str): type of access to test.
            course (CourseDescriptor): a course.
        """
        self.assertTrue(has_access(user, action, course))
        self.assertTrue(has_access(user, action, CourseOverview.get_from_id(course.id)))

    def assertCannotAccessCourse(self, user, action, course):
        """
        Assert that a user lacks access to the given action the given course.

        Test with both the given course and with a CourseOverview of the given
        course.

        Arguments:
            user (User): a user.
            action (str): type of access to test.
            course (CourseDescriptor): a course.

        Note:
            It may seem redundant to have one method for testing access
            and another method for testing lack thereof (why not just combine
            them into one method with a boolean flag?), but it makes reading
            stack traces of failed tests easier to understand at a glance.
        """
        self.assertFalse(has_access(user, action, course))
        self.assertFalse(has_access(user, action, CourseOverview.get_from_id(course.id)))
