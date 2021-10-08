"""
Tests for ESG views
"""
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import StaffFactory
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory


class TestInitializeView(APITestCase):
    """
    Tests for the /initialize view, creating setup data for ESG
    """
    view_name = 'ora-staff-grader:initialize'
    api_url = reverse(view_name)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_key_str = 'course-v1:Hogwarts+Potions101+S1'
        cls.course_key = CourseKey.from_string(cls.course_key_str)
        cls.course = CourseFactory(key=cls.course_key_str)

        cls.password = 'password'
        cls.staff = StaffFactory(course_key=cls.course_key, password=cls.password)

    def log_in(self):
        """ Log in as staff """
        self.client.login(username=self.staff.username, password=self.password)

    def test_missing_ora_location(self):
        """ Missing ora_location param should return 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url)

        assert response.status_code == 400
        assert response.content.decode() == "Query must contain an ora_location param."

    def test_bad_ora_location(self):
        """ Bad ORA location should return a 404 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {'ora_location': 'not_a_real_location'})

        assert response.status_code == 404
        assert response.content.decode() == "Invalid ora_location."
