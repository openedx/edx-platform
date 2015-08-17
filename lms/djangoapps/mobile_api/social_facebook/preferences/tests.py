# pylint: disable=no-member
"""
Tests for users sharing preferences
"""
from django.core.urlresolvers import reverse
from ..test_utils import SocialFacebookTestCase


class StudentProfileViewTest(SocialFacebookTestCase):
    """ Tests for the student profile views. """

    USERNAME = u'bnotions'
    PASSWORD = u'horse'
    EMAIL = u'horse@bnotions.com'
    FULL_NAME = u'bnotions horse'

    def setUp(self):
        super(StudentProfileViewTest, self).setUp()
        self.user_create_and_signin(1)

    def assert_shared_value(self, response, expected_value='True'):
        """
        Tests whether the response is successful and whether the
        share_with_facebook_friends value is set to the expected value.
        """
        self.assertEqual(response.status_code, 200)
        self.assertTrue('share_with_facebook_friends' in response.data)
        self.assertTrue(expected_value in response.data['share_with_facebook_friends'])

    def test_set_preferences_to_true(self):
        url = reverse('preferences')
        response = self.client.post(url, {'share_with_facebook_friends': 'True'})
        self.assert_shared_value(response)

    def test_set_preferences_to_false(self):
        url = reverse('preferences')
        response = self.client.post(url, {'share_with_facebook_friends': 'False'})
        self.assert_shared_value(response, 'False')

    def test_set_preferences_no_parameters(self):
        # Note that if no value is given it will default to False
        url = reverse('preferences')
        response = self.client.post(url, {})
        self.assert_shared_value(response, 'False')

    def test_set_preferences_invalid_parameters(self):
        # Note that if no value is given it will default to False
        # also in the case of invalid parameters
        url = reverse('preferences')
        response = self.client.post(url, {'bad_param': 'False'})
        self.assert_shared_value(response, 'False')

    def test_get_preferences_after_setting_them(self):
        url = reverse('preferences')

        for boolean in ['True', 'False']:
            # Set the preference
            response = self.client.post(url, {'share_with_facebook_friends': boolean})
            self.assert_shared_value(response, boolean)
            # Get the preference
            response = self.client.get(url)
            self.assert_shared_value(response, boolean)

    def test_get_preferences_without_setting_them(self):
        url = reverse('preferences')
        # Get the preference
        response = self.client.get(url)
        self.assert_shared_value(response, 'False')
