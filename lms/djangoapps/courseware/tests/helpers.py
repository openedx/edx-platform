import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from student.models import Registration

from django.test import TestCase


def check_for_get_code(self, code, url):
    """
    Check that we got the expected code when accessing url via GET.
    Returns the HTTP response.

    `self` is a class that subclasses TestCase.

    `code` is a status code for HTTP responses.

    `url` is a url pattern for which we have to test the response.
    """
    resp = self.client.get(url)
    self.assertEqual(resp.status_code, code,
                     "got code %d for url '%s'. Expected code %d"
                     % (resp.status_code, url, code))
    return resp


def check_for_post_code(self, code, url, data={}):
    """
    Check that we got the expected code when accessing url via POST.
    Returns the HTTP response.
    `self` is a class that subclasses TestCase.

    `code` is a status code for HTTP responses.

    `url` is a url pattern for which we want to test the response.
    """
    resp = self.client.post(url, data)
    self.assertEqual(resp.status_code, code,
                     "got code %d for url '%s'. Expected code %d"
                     % (resp.status_code, url, code))
    return resp


def get_request_for_user(user):
    """Create a request object for user."""

    request = RequestFactory()
    request.user = user
    request.META = {}
    request.is_secure = lambda: True
    request.get_host = lambda: "edx.org"
    return request


class LoginEnrollmentTestCase(TestCase):
    """
    Provides support for user creation,
    activation, login, and course enrollment.
    """
    def setUp(self):
        from django.conf import settings

    def setup_user(self):
        """
        Create a user account, activate, and log in.
        """
        self.email = 'foo@test.com'
        self.password = 'bar'
        self.username = 'test'
        self.user = self.create_account(self.username,
                            self.email, self.password)
        self.activate_user(self.email)
        self.login(self.email, self.password)

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
        check_for_get_code(self, 302, reverse('logout'))

    def create_account(self, username, email, password):
        """
        Create the account and check that it worked.
        """
        resp = check_for_post_code(self, 200, reverse('create_account'), {
            'username': username,
            'email': email,
            'password': password,
            'name': 'username',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
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
        check_for_get_code(self, 200, reverse('activate', kwargs={'key': activation_key}))
        # Now make sure that the user is now actually activated
        self.assertTrue(User.objects.get(email=email).is_active)

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
        check_for_post_code(self, 200, reverse('change_enrollment'), {
            'enrollment_action': 'unenroll',
            'course_id': course.id.to_deprecated_string()
        })
