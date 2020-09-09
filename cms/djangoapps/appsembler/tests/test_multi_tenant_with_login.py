"""
Tests for APPSEMBLER_MULTI_TENANT_EMAILS in Studio login.
"""

import ddt
import pytest
from unittest import skipIf
from django.core.exceptions import MultipleObjectsReturned
from mock import patch
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from student.roles import CourseAccessRole, CourseCreatorRole, CourseInstructorRole, CourseStaffRole

from student.tests.factories import UserFactory


@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'APPSEMBLER_MULTI_TENANT_EMAILS': True})
@skipIf(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in CMS')
class MultiTenantStudioLoginTestCase(TestCase):
    """
    Testing the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio.
    """

    BLUE = 'blue1'
    EMAIL = 'customer@example.com'
    PASSWORD = 'xyz'
    FAILURE_MESSAGE = (
        'Email or password is incorrect. '
        'Please ensure that you are a course staff in order to use Studio.'
    )

    def setUp(self):
        super(MultiTenantStudioLoginTestCase, self).setUp()
        self.url = reverse('login_post')  # CMS login endpoint.
        self.customer = UserFactory.create(email=self.EMAIL, password=self.PASSWORD)

    def test_login_with_course_creator_role(self):
        """
        Test the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio for CourseCreatorRole.
        """
        CourseAccessRole.objects.create(user=self.customer, role=CourseCreatorRole.ROLE)
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
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert not response.json()['success']
        assert response.json()['value'] == self.FAILURE_MESSAGE

    @ddt.data(CourseStaffRole.ROLE, CourseInstructorRole.ROLE)
    def test_login_for_course_staff(self, course_role_name):
        """
        Test the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio for Course{Instructor,Staff}Role's.
        """
        CourseAccessRole.objects.create(user=self.customer, role=course_role_name)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['success'], response.content

    @patch('student.views.login.log')
    def test_error_on_two_emails_found(self, mock_log):
        """
        Test that two users with CourseCreatorRole if found 500 shows up.

        Not fun but allows us to triage issues properly if enough issues
        were reported instead of a silent error.
        """
        CourseAccessRole.objects.create(user=self.customer, role=CourseCreatorRole.ROLE)

        # Add a CourseInstructorRole with the same email.
        customer_2 = UserFactory.create(email=self.EMAIL, password='another_password')
        CourseAccessRole.objects.create(user=customer_2, role=CourseInstructorRole.ROLE)

        assert not mock_log.exception.called, 'Not to be called yet'
        with pytest.raises(MultipleObjectsReturned):
            self.client.post(self.url, {
                'email': self.EMAIL,
                'password': self.PASSWORD,
            })
        assert mock_log.exception.called, 'Should be called to log our custom message'

    @ddt.data(CourseStaffRole.ROLE, CourseInstructorRole.ROLE)
    def test_login_for_course_staff(self, course_role_name):
        """
        Test the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio for Course{Instructor,Staff}Role's.
        """
        CourseAccessRole.objects.create(user=self.customer, role=course_role_name)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['success'], response.content

    def test_login_for_course_staff_but_learner_on_another_site(self):
        """
        Test the login for a learner in a site but a staff in another.

        When APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio
        """
        # Add a learner with the same email.
        _learner_2 = UserFactory.create(email=self.EMAIL, password='another_password')

        CourseAccessRole.objects.create(user=self.customer, role=CourseStaffRole.ROLE)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['success'], response.content

    def test_login_for_course_staff_in_two_courses(self):
        """
        Test the login for a course staff for two courses.

        When APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio.
        This is created to fix a Django ORM weirdness with MultipleObjectsReturned.
        """
        CourseAccessRole.objects.create(user=self.customer, role=CourseStaffRole.ROLE)
        CourseAccessRole.objects.create(user=self.customer, role=CourseInstructorRole.ROLE)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['success'], response.content

    def test_failed_login(self):
        """
        Test a failed login when the APPSEMBLER_MULTI_TENANT_EMAILS feature in Studio.
        """
        CourseAccessRole.objects.create(user=self.customer, role=CourseCreatorRole.ROLE)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': 'wrong_password',
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        assert not response.json()['success']
        assert response.json()['value'] == self.FAILURE_MESSAGE
