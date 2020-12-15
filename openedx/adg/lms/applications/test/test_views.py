"""
All tests for applications views
"""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.test.client import RequestFactory

from openedx.adg.lms.applications.views import ContactInformationView
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from student.models import UserProfile


class ContactInformationViewTest(TestCase):
    """
    Test cases for the ContactInformationView
    """

    def setUp(self):
        """
        Create a new user and logged in to access the view
        """
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email='testuser@test.com',
            password='password',
            username='testuser'
        )
        UserProfile.objects.create(user=self.user, name='testuser', city='XYZ')
        ExtendedUserProfile.objects.create(user=self.user, saudi_national=False)
        self.client.login(username='testuser', password='password')

    def test_context(self):
        """
        Verify the context data when user GET the view
        """
        factory = RequestFactory()
        request = factory.get('/application/contact')
        request.user = self.user
        response = ContactInformationView.as_view()(request)
        self.assertIsInstance(response.context_data, dict)
        self.assertEqual(response.context_data['name'], self.user.profile.name)
        self.assertEqual(response.context_data['email'], self.user.email)
        self.assertEqual(response.context_data['city'], self.user.profile.city)
        self.assertEqual(response.context_data['saudi_national'], self.user.extended_profile.saudi_national)
