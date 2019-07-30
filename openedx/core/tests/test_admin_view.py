"""
Tests that verify that the admin view loads.

This is not inside a django app because it is a global property of the system.
"""

from django.test import TestCase, Client
from django.urls import reverse
from student.tests.factories import UserFactory, TEST_PASSWORD


class TestAdminView(TestCase):
    """
    Tests of the admin view
    """
    def setUp(self):
        super(TestAdminView, self).setUp()
        self.client = Client()
        self.staff_user = UserFactory.create(is_staff=True)
        self.client.login(username=self.staff_user.username, password=TEST_PASSWORD)

    def test_admin_view_loads(self):
        response = self.client.get(reverse('admin:index'))
        assert response.status_code == 200
