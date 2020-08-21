"""
All tests for ondemand preferences views.
"""
import mock
from django.test import Client
from django.urls import reverse
from rest_framework import status

from lms.djangoapps.onboarding.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class OnDemandEmailPreferencesViews(ModuleStoreTestCase):
    """
    This class contains all tests for ondemand preferences views.
    """

    def setUp(self):
        super(OnDemandEmailPreferencesViews, self).setUp()
        self.user = UserFactory(password='password')
        self.client = Client()
        self.client.login(username=self.user.username, password='password')
        self.course = CourseFactory.create(display_name='test course', run='Testing_course')
        self.update_email_preferences_comp_path = reverse('update_email_preferences_component',
                                                          args=(str(self.course.id),))

    def test_unauthorization_redirection_on_get_email_preferences(self):
        """
        Get ondemand email preferences requires user to be logged in.
        """
        response = Client().get(self.update_email_preferences_comp_path)
        self.assertEqual(
            response.url,
            '{sign_in}?next={next_url}'.format(sign_in=reverse('signin_user'),
                                               next_url=self.update_email_preferences_comp_path)
        )

    @mock.patch('openedx.features.ondemand_email_preferences.views.get_email_pref_on_demand_course')
    def test_get_ondemand_email_preferences_with_logged_in_user(self, mock_get_email_pref_on_demand_course):
        """
        Test ondemand email preferences response with logged in user.
        """
        mock_get_email_pref_on_demand_course.return_value = True
        response = self.client.get(self.update_email_preferences_comp_path)
        expected_response = {
            'status': status.HTTP_200_OK,
            'email_preferences': True
        }
        self.assertJSONEqual(response.content, expected_response)
