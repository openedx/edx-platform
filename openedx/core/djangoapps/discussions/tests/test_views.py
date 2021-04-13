"""
Test app view logic
"""
# pylint: disable=test-inherits-tests
import unittest

from django.conf import settings
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from lms.djangoapps.courseware.tests.factories import StaffFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'URLs are only configured in LMS')
class ApiTest(APITestCase):
    """
    Test basic API operations
    """
    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:Test+Course+Configured')
        self.url = reverse(
            'discussions',
            kwargs={
                'course_key_string': str(self.course_key),
            }
        )
        self.password = 'password'
        self.user_student = UserFactory(username='dummy', password=self.password)
        self.user_staff_course = StaffFactory(course_key=self.course_key, password=self.password)
        self.user_staff_global = GlobalStaffFactory(password=self.password)


class UnauthorizedApiTest(ApiTest):
    """
    Logged-out users should _not_ have any access
    """

    expected_response_code = status.HTTP_401_UNAUTHORIZED

    def test_access_get(self):
        response = self.client.get(self.url)
        assert response.status_code == self.expected_response_code

    def test_access_patch(self):
        response = self.client.patch(self.url)
        assert response.status_code == self.expected_response_code

    def test_access_post(self):
        response = self.client.post(self.url)
        assert response.status_code == self.expected_response_code

    def test_access_put(self):
        response = self.client.put(self.url)
        assert response.status_code == self.expected_response_code


class AuthenticatedApiTest(UnauthorizedApiTest):
    """
    Logged-in users should _not_ have any access
    """

    expected_response_code = status.HTTP_403_FORBIDDEN

    def setUp(self):
        super().setUp()
        self._login()

    def _login(self):
        self.client.login(username=self.user_student.username, password=self.password)


class AuthorizedApiTest(AuthenticatedApiTest):
    """
    Global Staff should have access to all supported methods
    """

    expected_response_code = status.HTTP_200_OK

    def _login(self):
        self.client.login(username=self.user_staff_global.username, password=self.password)

    def test_access_patch(self):
        response = self.client.patch(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_access_put(self):
        response = self.client.put(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class CourseStaffAuthorizedTest(UnauthorizedApiTest):
    """
    Course Staff should have the same access as Global Staff

    TODO: This behavior should be changed to _allow_ access [1]
    - [1] https://openedx.atlassian.net/browse/TNL-8231
    """

    def _login(self):
        self.client.login(username=self.user_staff_course.username, password=self.password)
