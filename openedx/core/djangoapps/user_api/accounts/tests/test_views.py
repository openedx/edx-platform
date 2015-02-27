import unittest
import ddt
import json
from datetime import datetime

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

    def setUp(self):
        super(TestAccountAPI, self).setUp()
        self.anonymous_client = APIClient()
        self.different_user = UserFactory.create(password=TEST_PASSWORD)
        self.different_client = APIClient()
        self.staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        self.staff_client = APIClient()
        self.user = UserFactory.create(password=TEST_PASSWORD)
        self.url = reverse("accounts_api", kwargs={'username': self.user.username})

    def test_get_account_anonymous_user(self):
        """
        Test that an anonymous client (not logged in) cannot call get.
        """
        self.send_get(self.anonymous_client, expected_status=401)

    def test_get_account_different_user(self):
        """
        Test that a client (logged in) cannot get the account information for a different client.
        """
        self.different_client.login(username=self.different_user.username, password=TEST_PASSWORD)
        self.send_get(self.different_client, expected_status=404)

    def test_get_account_default(self):
        """
        Test that a client (logged in) can get her own account information (using default legacy profile information,
        as created by the test UserFactory).
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.send_get(self.client)
        data = response.data
        self.assertEqual(11, len(data))
        self.assertEqual(self.user.username, data["username"])
        self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
        for empty_field in ("year_of_birth", "level_of_education", "mailing_address"):
            self.assertIsNone(data[empty_field])
        self.assertIsNone(data["country"])
        # TODO: what should the format of this be?
        self.assertEqual("", data["language"])
        self.assertEqual("m", data["gender"])
        self.assertEqual("World domination", data["goals"])
        self.assertEqual(self.user.email, data["email"])
        self.assertIsNotNone(data["date_joined"])

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_account(self, api_client, user):
        """
        Test that a client (logged in) can get her own account information. Also verifies that a "is_staff"
        user can get the account information for other users.
        """
        # Create some test profile values.
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        legacy_profile.country = "US"
        legacy_profile.level_of_education = "m"
        legacy_profile.year_of_birth = 1900
        legacy_profile.goals = "world peace"
        legacy_profile.mailing_address = "Park Ave"
        legacy_profile.save()

        client = self.login_client(api_client, user)
        response = self.send_get(client)
        data = response.data
        self.assertEqual(11, len(data))
        self.assertEqual(self.user.username, data["username"])
        self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
        self.assertEqual("US", data["country"])
        self.assertEqual("", data["language"])
        self.assertEqual("m", data["gender"])
        self.assertEqual(1900, data["year_of_birth"])
        self.assertEqual("m", data["level_of_education"])
        self.assertEqual("world peace", data["goals"])
        self.assertEqual("Park Ave", data['mailing_address'])
        self.assertEqual(self.user.email, data["email"])
        self.assertIsNotNone(data["date_joined"])

    def test_get_account_empty_string(self):
        """
        Test the conversion of empty strings to None for certain fields.
        """
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        legacy_profile.country = ""
        legacy_profile.level_of_education = ""
        legacy_profile.gender = ""
        legacy_profile.save()

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.send_get(self.client)
        for empty_field in ("level_of_education", "gender", "country"):
            self.assertIsNone(response.data[empty_field])

    @ddt.data(
        (
            "client", "user", "gender", "f", "not a gender",
            "Select a valid choice. not a gender is not one of the available choices."
        ),
        (
            "client", "user", "level_of_education", "none", "x",
            "Select a valid choice. x is not one of the available choices."
        ),
        ("client", "user", "country", "GB", "XY", "Select a valid choice. XY is not one of the available choices."),
        ("client", "user", "year_of_birth", 2009, "not_an_int", "Enter a whole number."),
        ("client", "user", "language", "Creole"),
        ("client", "user", "goals", "Smell the roses"),
        ("client", "user", "mailing_address", "Sesame Street"),
        # All of the fields can be edited by is_staff, but iterating through all of them again seems like overkill.
        # Just test a representative field.
        ("staff_client", "staff_user", "goals", "Smell the roses"),
    )
    @ddt.unpack
    def test_patch_account(
            self, api_client, user, field, value, fails_validation_value=None, developer_validation_message=None
    ):
        """
        Test the behavior of patch, when using the correct content_type.
        """
        client = self.login_client(api_client, user)
        self.send_patch(client, {field: value})

        get_response = self.send_get(client)
        self.assertEqual(value, get_response.data[field])

        if fails_validation_value:
            error_response = self.send_patch(client, {field: fails_validation_value}, expected_status=400)
            self.assertEqual(
                "Value '{0}' is not valid for field '{1}'.".format(fails_validation_value, field),
                error_response.data["field_errors"][field]["user_message"]
            )
            self.assertEqual(
                developer_validation_message,
                error_response.data["field_errors"][field]["developer_message"]
            )
        else:
            # If there are no values that would fail validation, then empty string should be supported.
            self.send_patch(client, {field: ""})

            get_response = self.send_get(client)
            self.assertEqual("", get_response.data[field])

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_patch_account_noneditable(self, api_client, user):
        """
        Tests the behavior of patch when a read-only field is attempted to be edited.
        """
        client = self.login_client(api_client, user)

        def verify_error_response(field_name, data):
            self.assertEqual(
                "This field is not editable via this API", data["field_errors"][field_name]["developer_message"]
            )
            self.assertEqual(
                "Field '{0}' cannot be edited.".format(field_name), data["field_errors"][field_name]["user_message"]
            )

        for field_name in ["username", "email", "date_joined", "name"]:
            response = self.send_patch(client, {field_name: "will_error", "gender": "f"}, expected_status=400)
            verify_error_response(field_name, response.data)

        # Make sure that gender did not change.
        response = self.send_get(client)
        self.assertEqual("m", response.data["gender"])

        # Test error message with multiple read-only items
        response = self.send_patch(client, {"username": "will_error", "email": "xx"}, expected_status=400)
        self.assertEqual(2, len(response.data["field_errors"]))
        verify_error_response("username", response.data)
        verify_error_response("email", response.data)

    def test_patch_bad_content_type(self):
        """
        Test the behavior of patch when an incorrect content_type is specified.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.send_patch(self.client, {}, content_type="application/json", expected_status=415)
        self.send_patch(self.client, {}, content_type="application/xml", expected_status=415)

    def test_patch_account_empty_string(self):
        """
        Tests the behavior of patch when attempting to set fields with a select list of options to the empty string.
        Also verifies the behaviour when setting to None.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        for field_name in ["gender", "level_of_education", "country"]:
            self.send_patch(self.client, {field_name: ""})
            response = self.send_get(self.client)
            # Although throwing a 400 might be reasonable, the default DRF behavior with ModelSerializer
            # is to convert to None, which also seems acceptable (and is difficult to override).
            self.assertIsNone(response.data[field_name])

            # Verify that the behavior is the same for sending None.
            self.send_patch(self.client, {field_name: ""})
            response = self.send_get(self.client)
            self.assertIsNone(response.data[field_name])

    def login_client(self, api_client, user):
        """Helper method for getting the client and user and logging in. Returns client. """
        client = getattr(self, api_client)
        user = getattr(self, user)
        client.login(username=user.username, password=TEST_PASSWORD)
        return client

    def send_patch(self, client, json_data, content_type="application/merge-patch+json", expected_status=204):
        """
        Helper method for sending a patch to the server, defaulting to application/merge-patch+json content_type.
        Verifies the expected status and returns the response.
        """
        response = client.patch(self.url, data=json.dumps(json_data), content_type=content_type)
        self.assertEqual(expected_status, response.status_code)
        return response

    def send_get(self, client, expected_status=200):
        """
        Helper method for sending a GET to the server. Verifies the expected status and returns the response.
        """
        response = client.get(self.url)
        self.assertEqual(expected_status, response.status_code)
        return response
