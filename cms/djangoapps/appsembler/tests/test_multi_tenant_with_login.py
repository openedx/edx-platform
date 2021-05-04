"""
Tests for APPSEMBLER_MULTI_TENANT_EMAILS in Studio login.

Special note:

This test module needs to patch `cms.urls.urlpatterns` to include urlpatterns
from `cms.djangoapps.appsembler.urls`. This works by overriding the
`doango.conf.settings.ROOT_URLCONF` with `django.test.utils.override_settings`
at the TestCase class level with the `urlpatterns` list declared in the module
containing the TestCase class.

For this test module, we've added a `urlpatterns` module level variable and
assigned it the value of `cms.urls.urlpatterns` then appended the conditionally
included urlpatterns we need to run the tests.

Then we add `@override_settings(ROOT_URLCONF=__name__)` to the TestClass

There are other ways to do this. However, this is simple and does not require
our code to explicitly hack  `sys.modules` reloading
"""

import ddt
from django.conf.urls import include, url
from django.urls import reverse
from bs4 import BeautifulSoup as soup
from mock import patch
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import status

from student.roles import CourseAccessRole, CourseCreatorRole, CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory

import cms.urls
from cms.djangoapps.appsembler.views import LoginView


# Set the urlpatterns we want to use for our tests in this module only
urlpatterns = cms.urls.urlpatterns + [
    url(r'', include('cms.djangoapps.appsembler.urls'))
]


@ddt.ddt
@override_settings(ROOT_URLCONF=__name__)  # the module that contains `urlpatterns`
@patch.dict('django.conf.settings.FEATURES', {'APPSEMBLER_MULTI_TENANT_EMAILS': True})
@patch.dict('django.conf.settings.FEATURES', {'TAHOE_STUDIO_LOCAL_LOGIN': True})
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
        self.url = reverse('login')
        self.customer = UserFactory.create(email=self.EMAIL, password=self.PASSWORD)

    def get_error_message_text(self, response):
        return soup(response.content,
                    'html.parser').find(id='login_error').p.get_text()

    def test_login_no_course_creator(self):
        """
        Test that users without CourseCreatorRole cannot login into Studio.
        """
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        # Assert we do NOT have a logged-in session (authorized user)
        self.assertNotIn('_auth_user_id', self.client.session)
        assert response['Content-Type'] == 'text/html; charset=utf-8'
        error_message = self.get_error_message_text(response)
        assert error_message == LoginView.error_messages['invalid_login']

    @ddt.data(CourseStaffRole.ROLE, CourseInstructorRole.ROLE, CourseCreatorRole.ROLE)
    def test_login_for_course_access_role(self, course_role_name):
        """
        Test the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio
        for Course{Instructor,Staff}Role's.
        """
        CourseAccessRole.objects.create(user=self.customer, role=course_role_name)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_302_FOUND, response.content
        assert not response.content
        new_url = response.url
        response = self.client.get(new_url)
        assert response.status_code == status.HTTP_200_OK
        # Assert we DO have a logged-in session (authorized user)
        self.assertIn('_auth_user_id', self.client.session)
        assert response['Content-Type'] == 'text/html; charset=utf-8'

    @patch('cms.djangoapps.appsembler.views.logger')
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

        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_200_OK, response.content
        # Assert we do NOT have a logged-in session (authorized user)
        self.assertNotIn('_auth_user_id', self.client.session)
        assert response['Content-Type'] == 'text/html; charset=utf-8'
        error_message = self.get_error_message_text(response)
        assert error_message == LoginView.error_messages['multiple_users_found']

    def test_login_for_course_staff_but_learner_on_another_site_original(self):
        """
        Test the login for a learner in a site but a staff in another.

        When APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio
        """
        # Add a learner with the same email.
        UserFactory.create(email=self.EMAIL, password='another_password')

        CourseAccessRole.objects.create(user=self.customer, role=CourseStaffRole.ROLE)
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'password': self.PASSWORD,
        })
        assert response.status_code == status.HTTP_302_FOUND, response.content
        assert not response.content
        new_url = response.url
        response = self.client.get(new_url)
        assert response.status_code == status.HTTP_200_OK
        # Assert we DO have a logged-in session (authorized user)
        self.assertIn('_auth_user_id', self.client.session)
        assert response['Content-Type'] == 'text/html; charset=utf-8'

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
        assert response.status_code == status.HTTP_302_FOUND, response.content
        assert not response.content
        new_url = response.url
        response = self.client.get(new_url)
        assert response.status_code == status.HTTP_200_OK
        # Assert we DO have a logged-in session (authorized user)
        self.assertIn('_auth_user_id', self.client.session)
        assert response['Content-Type'] == 'text/html; charset=utf-8'

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
        # Assert we do NOT have a logged-in session (authorized user)
        self.assertNotIn('_auth_user_id', self.client.session)
        assert response['Content-Type'] == 'text/html; charset=utf-8'
        error_message = self.get_error_message_text(response)
        assert error_message == LoginView.error_messages['invalid_login']
