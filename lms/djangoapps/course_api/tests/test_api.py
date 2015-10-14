"""
Test for course API
"""

from lettuce import world
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.test.client import RequestFactory
from rest_framework import status

from courseware.tests.helpers import get_request_for_user

from course_api.api import list_courses


class TestGetCourseList(ModuleStoreTestCase):

    def create_request(self, uname, email, password, is_staff):
        user = world.UserFactory(
            username=uname,
            email=email,
            password=password,
            is_staff=is_staff)

        self.request.user = user

    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/dummy-url')
        super(TestGetCourseList, self).setUp()

    def test_user_course_list_as_staff(self):
        self.create_request("staff", "staff@example.com", "edx", True)
        courses = list_courses(self.request, "staff")

        self.assertNotEqual(courses.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_course_list_as_honor(self):
        self.create_request("honor", "honor@example.com", "edx", False)
        courses = list_courses(self.request, "honor")

        self.assertNotEqual(courses.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_course_list_as_honor_staff(self):
        self.create_request("honor", "honor@example.com", "edx", False)
        courses = list_courses(self.request, "staff")

        self.assertEqual(courses.status_code, status.HTTP_403_FORBIDDEN)
