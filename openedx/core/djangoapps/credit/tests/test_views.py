"""
Tests for credit app views.
"""
import unittest
import json
import datetime
import pytz

import ddt
from mock import patch
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from student.tests.factories import UserFactory
from util.testing import UrlResetMixin
from util.date_utils import to_timestamp
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.credit import api
from openedx.core.djangoapps.credit.signature import signature
from openedx.core.djangoapps.credit.models import (
    CreditCourse,
    CreditProvider,
    CreditRequirement,
    CreditRequirementStatus,
    CreditEligibility,
    CreditRequest,
)


TEST_CREDIT_PROVIDER_SECRET_KEY = "931433d583c84ca7ba41784bad3232e6"


@ddt.ddt
@override_settings(CREDIT_PROVIDER_SECRET_KEYS={
    "hogwarts": TEST_CREDIT_PROVIDER_SECRET_KEY
})
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CreditProviderViewTests(UrlResetMixin, TestCase):
    """
    Tests for HTTP end-points used to issue requests to credit providers
    and receive responses approving or denying requests.
    """

    USERNAME = "ron"
    USER_FULL_NAME = "Ron Weasley"
    PASSWORD = "password"
    PROVIDER_ID = "hogwarts"
    PROVIDER_URL = "https://credit.example.com/request"
    COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    FINAL_GRADE = 0.95

    @patch.dict(settings.FEATURES, {"ENABLE_CREDIT_API": True})
    def setUp(self):
        """
        Configure a credit course.
        """
        super(CreditProviderViewTests, self).setUp()

        # Create the test user and log in
        self.user = UserFactory(username=self.USERNAME, password=self.PASSWORD)
        self.user.profile.name = self.USER_FULL_NAME
        self.user.profile.save()

        success = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(success, msg="Could not log in")

        # Enable the course for credit
        credit_course = CreditCourse.objects.create(
            course_key=self.COURSE_KEY,
            enabled=True,
        )

        # Configure a credit provider for the course
        CreditProvider.objects.create(
            provider_id=self.PROVIDER_ID,
            enable_integration=True,
            provider_url=self.PROVIDER_URL,
        )

        # Add a single credit requirement (final grade)
        requirement = CreditRequirement.objects.create(
            course=credit_course,
            namespace="grade",
            name="grade",
        )

        # Mark the user as having satisfied the requirement
        # and eligible for credit.
        CreditRequirementStatus.objects.create(
            username=self.USERNAME,
            requirement=requirement,
            status="satisfied",
            reason={"final_grade": self.FINAL_GRADE}
        )
        CreditEligibility.objects.create(
            username=self.USERNAME,
            course=credit_course,
        )

    def test_credit_request_and_response(self):
        # Initiate a request
        response = self._create_credit_request(self.USERNAME, self.COURSE_KEY)
        self.assertEqual(response.status_code, 200)

        # Check that the user's request status is pending
        requests = api.get_credit_requests_for_user(self.USERNAME)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["status"], "pending")

        # Check request parameters
        content = json.loads(response.content)
        self.assertEqual(content["url"], self.PROVIDER_URL)
        self.assertEqual(content["method"], "POST")
        self.assertEqual(len(content["parameters"]["request_uuid"]), 32)
        self.assertEqual(content["parameters"]["course_org"], "edX")
        self.assertEqual(content["parameters"]["course_num"], "DemoX")
        self.assertEqual(content["parameters"]["course_run"], "Demo_Course")
        self.assertEqual(content["parameters"]["final_grade"], self.FINAL_GRADE)
        self.assertEqual(content["parameters"]["user_username"], self.USERNAME)
        self.assertEqual(content["parameters"]["user_full_name"], self.USER_FULL_NAME)
        self.assertEqual(content["parameters"]["user_mailing_address"], "")
        self.assertEqual(content["parameters"]["user_country"], "")

        # The signature is going to change each test run because the request
        # is assigned a different UUID each time.
        # For this reason, we use the signature function directly
        # (the "signature" parameter will be ignored when calculating the signature).
        # Other unit tests verify that the signature function is working correctly.
        self.assertEqual(
            content["parameters"]["signature"],
            signature(content["parameters"], TEST_CREDIT_PROVIDER_SECRET_KEY)
        )

        # Simulate a response from the credit provider
        response = self._credit_provider_callback(
            content["parameters"]["request_uuid"],
            "approved"
        )
        self.assertEqual(response.status_code, 200)

        # Check that the user's status is approved
        requests = api.get_credit_requests_for_user(self.USERNAME)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["status"], "approved")

    def test_request_credit_anonymous_user(self):
        self.client.logout()
        response = self._create_credit_request(self.USERNAME, self.COURSE_KEY)
        self.assertEqual(response.status_code, 403)

    def test_request_credit_for_another_user(self):
        response = self._create_credit_request("another_user", self.COURSE_KEY)
        self.assertEqual(response.status_code, 403)

    @ddt.data(
        # Invalid JSON
        "{",

        # Missing required parameters
        json.dumps({"username": USERNAME}),
        json.dumps({"course_key": unicode(COURSE_KEY)}),

        # Invalid course key format
        json.dumps({"username": USERNAME, "course_key": "invalid"}),
    )
    def test_create_credit_request_invalid_parameters(self, request_data):
        url = reverse("credit:create_request", args=[self.PROVIDER_ID])
        response = self.client.post(url, data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_credit_provider_callback_validates_signature(self):
        request_uuid = self._create_credit_request_and_get_uuid(self.USERNAME, self.COURSE_KEY)

        # Simulate a callback from the credit provider with an invalid signature
        # Since the signature is invalid, we respond with a 403 Not Authorized.
        response = self._credit_provider_callback(request_uuid, "approved", sig="invalid")
        self.assertEqual(response.status_code, 403)

    def test_credit_provider_callback_validates_timestamp(self):
        request_uuid = self._create_credit_request_and_get_uuid(self.USERNAME, self.COURSE_KEY)

        # Simulate a callback from the credit provider with a timestamp too far in the past
        # (slightly more than 15 minutes)
        # Since the message isn't timely, respond with a 403.
        timestamp = to_timestamp(datetime.datetime.now(pytz.UTC) - datetime.timedelta(0, 60 * 15 + 1))
        response = self._credit_provider_callback(request_uuid, "approved", timestamp=timestamp)
        self.assertEqual(response.status_code, 403)

    def test_credit_provider_callback_handles_string_timestamp(self):
        request_uuid = self._create_credit_request_and_get_uuid(self.USERNAME, self.COURSE_KEY)

        # Simulate a callback from the credit provider with a timestamp
        # encoded as a string instead of an integer.
        timestamp = str(to_timestamp(datetime.datetime.now(pytz.UTC)))
        response = self._credit_provider_callback(request_uuid, "approved", timestamp=timestamp)
        self.assertEqual(response.status_code, 200)

    def test_credit_provider_callback_is_idempotent(self):
        request_uuid = self._create_credit_request_and_get_uuid(self.USERNAME, self.COURSE_KEY)

        # Initially, the status should be "pending"
        self._assert_request_status(request_uuid, "pending")

        # First call sets the status to approved
        self._credit_provider_callback(request_uuid, "approved")
        self._assert_request_status(request_uuid, "approved")

        # Second call succeeds as well; status is still approved
        self._credit_provider_callback(request_uuid, "approved")
        self._assert_request_status(request_uuid, "approved")

    @ddt.data(
        # Invalid JSON
        "{",

        # Not a dictionary
        "4",

        # Invalid timestamp format
        json.dumps({
            "request_uuid": "557168d0f7664fe59097106c67c3f847",
            "status": "approved",
            "timestamp": "invalid",
            "signature": "7685ae1c8f763597ee7ce526685c5ac24353317dbfe087f0ed32a699daf7dc63",
        }),
    )
    def test_credit_provider_callback_invalid_parameters(self, request_data):
        url = reverse("credit:provider_callback", args=[self.PROVIDER_ID])
        response = self.client.post(url, data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_credit_provider_invalid_status(self):
        response = self._credit_provider_callback("557168d0f7664fe59097106c67c3f847", "invalid")
        self.assertEqual(response.status_code, 400)

    def test_credit_provider_key_not_configured(self):
        # Cannot initiate a request because we can't sign it
        with override_settings(CREDIT_PROVIDER_SECRET_KEYS={}):
            response = self._create_credit_request(self.USERNAME, self.COURSE_KEY)
            self.assertEqual(response.status_code, 400)

        # Create the request with the secret key configured
        request_uuid = self._create_credit_request_and_get_uuid(self.USERNAME, self.COURSE_KEY)

        # Callback from the provider is not authorized, because
        # the shared secret isn't configured.
        with override_settings(CREDIT_PROVIDER_SECRET_KEYS={}):
            response = self._credit_provider_callback(request_uuid, "approved")
            self.assertEqual(response.status_code, 403)

    def test_request_associated_with_another_provider(self):
        other_provider_id = "other_provider"
        other_provider_secret_key = "1d01f067a5a54b0b8059f7095a7c636d"

        # Create an additional credit provider
        CreditProvider.objects.create(provider_id=other_provider_id, enable_integration=True)

        # Initiate a credit request with the first provider
        request_uuid = self._create_credit_request_and_get_uuid(self.USERNAME, self.COURSE_KEY)

        # Attempt to update the request status for a different provider
        with override_settings(CREDIT_PROVIDER_SECRET_KEYS={other_provider_id: other_provider_secret_key}):
            response = self._credit_provider_callback(
                request_uuid,
                "approved",
                provider_id=other_provider_id,
                secret_key=other_provider_secret_key,
            )

        # Response should be a 404 to avoid leaking request UUID values to other providers.
        self.assertEqual(response.status_code, 404)

        # Request status should still be "pending"
        self._assert_request_status(request_uuid, "pending")

    def _create_credit_request(self, username, course_key):
        """
        Initiate a request for credit.
        """
        url = reverse("credit:create_request", args=[self.PROVIDER_ID])
        return self.client.post(
            url,
            data=json.dumps({
                "username": username,
                "course_key": unicode(course_key),
            }),
            content_type="application/json",
        )

    def _create_credit_request_and_get_uuid(self, username, course_key):
        """
        Initiate a request for credit and return the request UUID.
        """
        response = self._create_credit_request(username, course_key)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)["parameters"]["request_uuid"]

    def _credit_provider_callback(self, request_uuid, status, **kwargs):
        """
        Simulate a response from the credit provider approving
        or rejecting the credit request.

        Arguments:
            request_uuid (str): The UUID of the credit request.
            status (str): The status of the credit request.

        Keyword Arguments:
            provider_id (str): Identifier for the credit provider.
            secret_key (str): Shared secret key for signing messages.
            timestamp (datetime): Timestamp of the message.
            sig (str): Digital signature to use on messages.

        """
        provider_id = kwargs.get("provider_id", self.PROVIDER_ID)
        secret_key = kwargs.get("secret_key", TEST_CREDIT_PROVIDER_SECRET_KEY)
        timestamp = kwargs.get("timestamp", to_timestamp(datetime.datetime.now(pytz.UTC)))

        url = reverse("credit:provider_callback", args=[provider_id])

        parameters = {
            "request_uuid": request_uuid,
            "status": status,
            "timestamp": timestamp,
        }
        parameters["signature"] = kwargs.get("sig", signature(parameters, secret_key))

        return self.client.post(url, data=json.dumps(parameters), content_type="application/json")

    def _assert_request_status(self, uuid, expected_status):
        """
        Check the status of a credit request.
        """
        request = CreditRequest.objects.get(uuid=uuid)
        self.assertEqual(request.status, expected_status)
