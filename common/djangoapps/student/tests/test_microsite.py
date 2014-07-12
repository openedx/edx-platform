"""
Test for User Creation from Micro-Sites
"""
from django.test import TestCase
from student.models import UserSignupSource
import mock
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

def fake_site_name(name, default=None):  # pylint: disable=W0613
    """
    create a fake microsite site name
    """
    if name == 'SITE_NAME':
        return 'openedx.localhost'
    else:
        return None


class TestMicrosite(TestCase):
    """Test for Account Creation from a white labeled Micro-Sites"""
    def setUp(self):
        self.username = "test_user"
        self.url = reverse("create_account")
        self.params = {
            "username": self.username,
            "email": "test@example.org",
            "password": "testpass",
            "name": "Test User",
            "honor_code": "true",
            "terms_of_service": "true",
        }

    @mock.patch("microsite_configuration.microsite.get_value", fake_site_name)
    def test_user_signup_source(self):
        """
        test to create a user form the microsite and see that it record has been
        saved in the UserSignupSource Table
        """
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(UserSignupSource.objects.filter(site='openedx.localhost')), 0)
        # check to see if the mailchimp synchronization will filter out this microsite user
        users = User.objects.raw('SELECT * FROM auth_user where id not in (SELECT user_id from student_usersignupsource)')
        self.assertEqual(len(list(users)), 0)

    def test_user_signup_from_non_micro_site(self):
        """
        test to create a user form the non-microsite. The record should not be saved
        in the UserSignupSource Table
        """
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(UserSignupSource.objects.filter(site='openedx.localhost')), 0)
        # check to see if the mailchimp synchronization will filter out this microsite user
        users = User.objects.raw('SELECT * FROM auth_user where id not in (SELECT user_id from student_usersignupsource)')
        self.assertEqual(len(list(users)), 1)
