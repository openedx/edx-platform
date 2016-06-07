"""
Test for User Creation from Micro-Sites
"""
from django.test import TestCase
from student.models import UserSignupSource
import mock
import json
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

FAKE_MICROSITE = {
    "SITE_NAME": "openedx.localhost",
    "university": "fakeuniversity",
    "course_org_filter": "fakeorg",
    "platform_name": "Fake University",
    "email_from_address": "no-reply@fakeuniversity.com",
    "REGISTRATION_EXTRA_FIELDS": {
        "address1": "required",
        "city": "required",
        "state": "required",
        "country": "required",
        "company": "required",
        "title": "required"
    },
    "extended_profile_fields": [
        "address1", "state", "company", "title"
    ]
}


def fake_site_name(name, default=None):
    """
    create a fake microsite site name
    """
    if name == 'SITE_NAME':
        return 'openedx.localhost'
    else:
        return default


def fake_microsite_get_value(name, default=None):
    """
    create a fake microsite site name
    """
    return FAKE_MICROSITE.get(name, default)


class TestMicrosite(TestCase):
    """Test for Account Creation from a white labeled Micro-Sites"""
    def setUp(self):
        super(TestMicrosite, self).setUp()
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
        self.extended_params = dict(self.params.items() + {
            "address1": "foo",
            "city": "foo",
            "state": "foo",
            "country": "foo",
            "company": "foo",
            "title": "foo"
        }.items())

    @mock.patch("microsite_configuration.microsite.get_value", fake_site_name)
    def test_user_signup_source(self):
        """
        test to create a user form the microsite and see that it record has been
        saved in the UserSignupSource Table
        """
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(UserSignupSource.objects.filter(site='openedx.localhost')), 0)

    def test_user_signup_from_non_micro_site(self):
        """
        test to create a user form the non-microsite. The record should not be saved
        in the UserSignupSource Table
        """
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(UserSignupSource.objects.filter(site='openedx.localhost')), 0)

    @mock.patch("microsite_configuration.microsite.get_value", fake_microsite_get_value)
    def test_user_signup_missing_enhanced_profile(self):
        """
        test to create a user form the microsite but don't provide any of the microsite specific
        profile information
        """
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 400)

    @mock.patch("microsite_configuration.microsite.get_value", fake_microsite_get_value)
    def test_user_signup_including_enhanced_profile(self):
        """
        test to create a user form the microsite but don't provide any of the microsite specific
        profile information
        """
        response = self.client.post(self.url, self.extended_params)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=self.username)
        meta = json.loads(user.profile.meta)
        self.assertEqual(meta['address1'], 'foo')
        self.assertEqual(meta['state'], 'foo')
        self.assertEqual(meta['company'], 'foo')
        self.assertEqual(meta['title'], 'foo')
