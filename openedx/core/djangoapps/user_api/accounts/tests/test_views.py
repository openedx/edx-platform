import unittest
import ddt

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from rest_framework.test import APITestCase, APIClient

from student.tests.factories import UserFactory
from student.models import UserProfile

TEST_PASSWORD = "test"

@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestAccountAPI(APITestCase):
    USERNAME = "Christina"
    EMAIL = "christina@example.com"
    PASSWORD = TEST_PASSWORD

    BAD_USERNAME = "Bad"
    BAD_EMAIL = "bad@example.com"
    BAD_PASSWORD = TEST_PASSWORD

    STAFF_USERNAME = "Staff"
    STAFF_EMAIL = "staff@example.com"
    STAFF_PASSWORD = TEST_PASSWORD

    def setUp(self):
        super(TestAccountAPI, self).setUp()

        self.anonymous_client = APIClient()

        self.bad_user = UserFactory.create(password=TEST_PASSWORD)
        self.bad_client = APIClient()

        self.staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        self.staff_client = APIClient()

        self.user = UserFactory.create(password=TEST_PASSWORD)
        # Create some test profile values.
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        legacy_profile.city = "Indi"
        legacy_profile.country = "US"
        legacy_profile.year_of_birth = 1900
        legacy_profile.level_of_education = "m"
        legacy_profile.goals = "world peace"
        legacy_profile.mailing_address = "North Pole"
        legacy_profile.save()
        
        self.accounts_base_uri = reverse("accounts_api", kwargs={'username': self.user.username})

    def test_get_account_anonymous_user(self):
        response = self.anonymous_client.get(self.accounts_base_uri)
        self.assert_status_code(401, response)

    def test_get_account_bad_user(self):
        self.bad_client.login(username=self.bad_user.username, password=TEST_PASSWORD)
        response = self.bad_client.get(self.accounts_base_uri)
        self.assert_status_code(404, response)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_account(self, api_client, user):
        client = self.login_client(api_client, user)

        response = client.get(self.accounts_base_uri)
        self.assert_status_code(200, response)
        data = response.data
        self.assertEqual(12, len(data))
        self.assertEqual(self.user.username, data["username"])
        # TODO: should we rename this "full_name"?
        self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
        self.assertEqual("Indi", data["city"])
        self.assertEqual("US", data["country"])
        # TODO: what should the format of this be?
        self.assertEqual("", data["language"])
        self.assertEqual("m", data["gender"])
        self.assertEqual(1900, data["year_of_birth"])
        self.assertEqual("m", data["level_of_education"])
        self.assertEqual("world peace", data["goals"])
        self.assertEqual("North Pole", data['mailing_address'])
        self.assertEqual(self.user.email, data["email"])
        self.assertIsNotNone(data["date_joined"])

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_patch_account(self, api_client, user):
        client = self.login_client(api_client, user)
        response = client.patch(self.accounts_base_uri, data={"usernamae": "willbeignored", "gender": "f"})
        self.assert_status_code(200, response)
        data = response.data
        # Note that username is read-only, so passing it in patch is ignored. We want to change this behavior so it throws an exception.
        self.assertEqual(self.user.username, data["username"])
        self.assertEqual("f", data["gender"])

    def assert_status_code(self, expected_status_code, response):
        """Assert that the given response has the expected status code"""
        self.assertEqual(expected_status_code, response.status_code)

    def login_client(self, api_client, user):
        client = getattr(self, api_client)
        user = getattr(self, user)
        client.login(username=user.username, password=TEST_PASSWORD)
        return client
