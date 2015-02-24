"""
Tests for users sharing preferences
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from openedx.core.djangoapps.user_api.api import account as account_api
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class StudentProfileViewTest(ModuleStoreTestCase, TestCase):
    """ Tests for the student profile views. """

    USERNAME = u'bnotions'
    PASSWORD = u'horse'
    EMAIL = u'horse@bnotions.com'
    FULL_NAME = u'bnotions horse'

    def setUp(self):
        super(StudentProfileViewTest, self).setUp()
        # Create/activate a new account
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.activate_account(activation_key)
        # Login
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

    def test_set_preferences_to_true(self):
        url = reverse('preferences')
        response = self.client.post(url, {'share_with_facebook_friends': 'True'})
        self.assertTrue('share_with_facebook_friends' in response.data)
        self.assertTrue('True' in response.data['share_with_facebook_friends'])

    def test_set_preferences_to_false(self):
        url = reverse('preferences')
        response = self.client.post(url, {'share_with_facebook_friends': 'False'})
        self.assertTrue('share_with_facebook_friends' in response.data)
        self.assertTrue('False' in response.data['share_with_facebook_friends'])

    def test_set_preferences_no_parameters(self):
        # Note that if no value is given it will default to True
        url = reverse('preferences')
        response = self.client.post(url, {})
        self.assertTrue('share_with_facebook_friends' in response.data)
        self.assertTrue('True' in response.data['share_with_facebook_friends'])

    def test_set_preferences_invalid_parameters(self):
        # Note that if no value is given it will default to True
        # also in the case of invalid parameters
        url = reverse('preferences')
        response = self.client.post(url, {'bad_param': 'False'})
        self.assertTrue('share_with_facebook_friends' in response.data)
        self.assertTrue('True' in response.data['share_with_facebook_friends'])

    def test_get_preferences_with_setting_them(self):
        # If no value is given it will default to True
        url = reverse('preferences')
        boolean = 'False'
        # Set the preference
        response = self.client.post(url, {'share_with_facebook_friends': boolean})
        self.assertTrue('share_with_facebook_friends' in response.data)
        self.assertTrue(boolean in response.data['share_with_facebook_friends'])  # pylint: disable=E1101
        # Get the preference
        response = self.client.get(url)
        self.assertTrue('share_with_facebook_friends' in response.data)  # pylint: disable=E1101
        self.assertTrue(boolean in response.data['share_with_facebook_friends'])  # pylint: disable=E1101

    def test_get_preferences_without_setting_them(self):
        # If no value is given it will default to True
        url = reverse('preferences')
        # Get the preference
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # pylint: disable=E1101
        self.assertEqual(response.data, {})  # pylint: disable=E1101
