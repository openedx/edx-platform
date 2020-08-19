"""
Tests for APPSEMBLER_MULTI_TENANT_EMAILS in Studio login.
"""

from mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from student.roles import CourseCreatorRole, CourseAccessRole

from student.tests.factories import UserFactory


@patch.dict('django.conf.settings.FEATURES', {'APPSEMBLER_MULTI_TENANT_EMAILS': True})
class MultiTenantStudioLoginTestCase(TestCase):
    """
    Testing the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio.
    """

    BLUE = 'blue1'
    EMAIL = 'customer@example.com'
    PASSWORD = 'xyz'

    def setUp(self):
        super(MultiTenantStudioLoginTestCase, self).setUp()
        self.url = reverse('login_post')  # CMS login endpoint.
        self.customer = UserFactory.create(email=self.EMAIL, password=self.PASSWORD)
        CourseAccessRole.objects.create(user=self.customer, role=CourseCreatorRole.ROLE)

    def test_login(self):
        """
        Test the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio.
        """
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['success']

    def test_login_no_course_creator(self):
        """
        Test that users without CourseCreatorRole cannot login into Studio.
        """
        CourseAccessRole.objects.filter(user=self.customer).delete()  # Remove CourseCreatorRole
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert not response.json()['success']
        assert response.json()['value'] == 'Email or password is incorrect.'

    def test_failed_login(self):
        """
        Test a failed login when the APPSEMBLER_MULTI_TENANT_EMAILS feature in Studio.
        """
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': 'wrong_password',
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert not response.json()['success']
        assert response.json()['value'] == 'Email or password is incorrect.'
