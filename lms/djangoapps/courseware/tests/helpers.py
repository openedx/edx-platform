import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from student.models import Registration

from django.test import TestCase


def get_request_for_user(user):
    """Create a request object for user."""

    request = RequestFactory()
    request.user = user
    request.COOKIES = {}
    request.META = {}
    request.is_secure = lambda: True
    request.get_host = lambda: "edx.org"
    request.method = 'GET'
    return request


class LoginEnrollmentTestCase(TestCase):
    """
    Provides support for user creation,
    activation, login, and course enrollment.
    """
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
        url = reverse('change_enrollment')
        request_data = {
            'enrollment_action': 'unenroll',
            'course_id': course.id.to_deprecated_string(),
        }
        self.assert_request_status_code(200, url, method="POST", data=request_data)
