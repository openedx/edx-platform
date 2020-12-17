"""
All tests for applications views
"""
from django.test import Client, TestCase
from django.test.client import RequestFactory

from openedx.adg.lms.applications.test.factories import ExtendedUserProfileFactory
from openedx.adg.lms.applications.views import ContactInformationView
from student.tests.factories import UserFactory


class ContactInformationViewTest(TestCase):
    """
    Test cases for the ContactInformationView
    """

    def setUp(self):
        """
        Create a new user and logged in to access the view
        """
        self.client = Client()
        self.user = UserFactory()

        extended_profile = ExtendedUserProfileFactory()
        extended_profile.user = self.user
        extended_profile.save()

        self.client.login(username=self.user.username, pasword=self.user.password)

    def test_initial_data(self):
        """
        Verify the context data when user GET the view
        """
        factory = RequestFactory()
        request = factory.get('/application/contact')
        request.user = self.user
        response = ContactInformationView.as_view()(request)
        print(response.context_data['form'].initial)
        self.assertIsInstance(response.context_data['form'].initial, dict)
        self.assertEqual(response.context_data['form'].initial['name'], self.user.profile.name)
        self.assertEqual(response.context_data['form'].initial['email'], self.user.email)
        self.assertEqual(response.context_data['form'].initial['city'], self.user.profile.city)
        self.assertEqual(response.context_data['form'].initial['saudi_national'],
                         self.user.extended_profile.saudi_national)
