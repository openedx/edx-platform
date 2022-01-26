"""
Tests that verify that the admin view loads.

This is not inside a django app because it is a global property of the system.
"""

from django.test import Client, TestCase
from django.urls import reverse
from common.djangoapps.student.tests.factories import UserFactory, TEST_PASSWORD


class TestAdminView(TestCase):
    """
    Tests of the admin view
    """
    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_admin_view_loads_for_is_staff(self):
        staff_user = UserFactory.create(is_staff=True)
        self.client.login(username=staff_user.username, password=TEST_PASSWORD)
        response = self.client.get(reverse('admin:index'))
        assert response.status_code == 200

    def test_admin_view_loads_for_is_superuser(self):
        superuser = UserFactory.create(is_superuser=True, is_staff=True)
        self.client.login(username=superuser.username, password=TEST_PASSWORD)
        response = self.client.get(reverse('admin:index'))
        assert response.status_code == 200

    def test_admin_view_doesnt_load_for_student(self):
        student = UserFactory.create()
        self.client.login(username=student.username, password=TEST_PASSWORD)
        response = self.client.get(reverse('admin:index'))
        assert response.status_code == 302

    def test_admin_login_redirect(self):
        """Admin login will redirect towards the site login page."""
        response = self.client.get(reverse('admin:login'))
        assert response.url == '/login?next=/admin'
        assert response.status_code == 302
