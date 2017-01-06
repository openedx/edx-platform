"""Tests for the Zendesk"""

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from smtplib import SMTPException
from student.tests.factories import UserFactory
from util import views
from zendesk import ZendeskError
import json
import mock
from ddt import ddt, data, unpack

from student.tests.test_configuration_overrides import fake_get_value
from student.tests.factories import CourseEnrollmentFactory


def fake_support_backend_values(name, default=None):  # pylint: disable=unused-argument
    """
    Method for getting configuration override values for support email.
    """
    config_dict = {
        "CONTACT_FORM_SUBMISSION_BACKEND": "email",
        "email_from_address": "support_from@example.com",
    }
    return config_dict[name]


@ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_FEEDBACK_SUBMISSION": True})
@override_settings(ZENDESK_URL="dummy", ZENDESK_USER="dummy", ZENDESK_API_KEY="dummy", ZENDESK_CUSTOM_FIELDS={})
@mock.patch("util.views.dog_stats_api")
@mock.patch("util.views._ZendeskApi", autospec=True)
class SubmitFeedbackTest(TestCase):
    """
    Class to test the submit_feedback function in views.
    """
    def setUp(self):
        """Set up data for the test case"""
        super(SubmitFeedbackTest, self).setUp()
        self._request_factory = RequestFactory()
        self._anon_user = AnonymousUser()
        self._auth_user = UserFactory.create(
            email="test@edx.org",
            username="test",
            profile__name="Test User"
        )
        self._anon_fields = {
            "email": "test@edx.org",
            "name": "Test User",
            "subject": "a subject",
            "details": "some details",
            "issue_type": "test_issue"
        }
        # This does not contain issue_type nor course_id to ensure that they are optional
        self._auth_fields = {"subject": "a subject", "details": "some details"}

    def _build_and_run_request(self, user, fields):
        """
        Generate a request and invoke the view, returning the response.

        The request will be a POST request from the given `user`, with the given
        `fields` in the POST body.
        """
        req = self._request_factory.post(
            "/submit_feedback",
            data=fields,
            HTTP_REFERER="test_referer",
            HTTP_USER_AGENT="test_user_agent",
            REMOTE_ADDR="1.2.3.4",
            SERVER_NAME="test_server",
        )
        req.user = user
        return views.submit_feedback(req)

    def _assert_bad_request(self, response, field, zendesk_mock_class, datadog_mock):
        """
        Assert that the given `response` contains correct failure data.

        It should have a 400 status code, and its content should be a JSON
        object containing the specified `field` and an `error`.
        """
        self.assertEqual(response.status_code, 400)
        resp_json = json.loads(response.content)
        self.assertIn("field", resp_json)
        self.assertEqual(resp_json["field"], field)
        self.assertIn("error", resp_json)
        # There should be absolutely no interaction with Zendesk
        self.assertFalse(zendesk_mock_class.return_value.mock_calls)
        self.assertFalse(datadog_mock.mock_calls)

    def _test_bad_request_omit_field(self, user, fields, omit_field, zendesk_mock_class, datadog_mock):
        """
        Invoke the view with a request missing a field and assert correctness.

        The request will be a POST request from the given `user`, with POST
        fields taken from `fields` minus the entry specified by `omit_field`.
        The response should have a 400 (bad request) status code and specify
        the invalid field and an error message, and the Zendesk API should not
        have been invoked.
        """
        filtered_fields = {k: v for (k, v) in fields.items() if k != omit_field}
        resp = self._build_and_run_request(user, filtered_fields)
        self._assert_bad_request(resp, omit_field, zendesk_mock_class, datadog_mock)

    def _test_bad_request_empty_field(self, user, fields, empty_field, zendesk_mock_class, datadog_mock):
        """
        Invoke the view with an empty field and assert correctness.

        The request will be a POST request from the given `user`, with POST
        fields taken from `fields`, replacing the entry specified by
        `empty_field` with the empty string. The response should have a 400
        (bad request) status code and specify the invalid field and an error
        message, and the Zendesk API should not have been invoked.
        """
        altered_fields = fields.copy()
        altered_fields[empty_field] = ""
        resp = self._build_and_run_request(user, altered_fields)
        self._assert_bad_request(resp, empty_field, zendesk_mock_class, datadog_mock)

    def _test_success(self, user, fields):
        """
        Generate a request, invoke the view, and assert success.

        The request will be a POST request from the given `user`, with the given
        `fields` in the POST body. The response should have a 200 (success)
        status code.
        """
        resp = self._build_and_run_request(user, fields)
        self.assertEqual(resp.status_code, 200)

    def _assert_datadog_called(self, datadog_mock, tags):
        """Assert that datadog was called with the correct tags."""
        expected_datadog_calls = [mock.call.increment(views.DATADOG_FEEDBACK_METRIC, tags=tags)]
        self.assertEqual(datadog_mock.mock_calls, expected_datadog_calls)

    def test_bad_request_anon_user_no_name(self, zendesk_mock_class, datadog_mock):
        """Test a request from an anonymous user not specifying `name`."""
        self._test_bad_request_omit_field(self._anon_user, self._anon_fields, "name", zendesk_mock_class, datadog_mock)
        self._test_bad_request_empty_field(self._anon_user, self._anon_fields, "name", zendesk_mock_class, datadog_mock)

    def test_bad_request_anon_user_no_email(self, zendesk_mock_class, datadog_mock):
        """Test a request from an anonymous user not specifying `email`."""
        self._test_bad_request_omit_field(self._anon_user, self._anon_fields, "email", zendesk_mock_class, datadog_mock)
        self._test_bad_request_empty_field(self._anon_user, self._anon_fields, "email", zendesk_mock_class, datadog_mock)

    def test_bad_request_anon_user_invalid_email(self, zendesk_mock_class, datadog_mock):
        """Test a request from an anonymous user specifying an invalid `email`."""
        fields = self._anon_fields.copy()
        fields["email"] = "This is not a valid email address!"
        resp = self._build_and_run_request(self._anon_user, fields)
        self._assert_bad_request(resp, "email", zendesk_mock_class, datadog_mock)

    def test_bad_request_anon_user_no_subject(self, zendesk_mock_class, datadog_mock):
        """Test a request from an anonymous user not specifying `subject`."""
        self._test_bad_request_omit_field(self._anon_user, self._anon_fields, "subject", zendesk_mock_class, datadog_mock)
        self._test_bad_request_empty_field(self._anon_user, self._anon_fields, "subject", zendesk_mock_class, datadog_mock)

    def test_bad_request_anon_user_no_details(self, zendesk_mock_class, datadog_mock):
        """Test a request from an anonymous user not specifying `details`."""
        self._test_bad_request_omit_field(self._anon_user, self._anon_fields, "details", zendesk_mock_class, datadog_mock)
        self._test_bad_request_empty_field(self._anon_user, self._anon_fields, "details", zendesk_mock_class, datadog_mock)

    def test_valid_request_anon_user(self, zendesk_mock_class, datadog_mock):
        """
        Test a valid request from an anonymous user.

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API.
        """
        zendesk_mock_instance = zendesk_mock_class.return_value
        zendesk_mock_instance.create_ticket.return_value = 42
        self._test_success(self._anon_user, self._anon_fields)
        expected_zendesk_calls = [
            mock.call.create_ticket(
                {
                    "ticket": {
                        "recipient": "registration@example.com",
                        "requester": {"name": "Test User", "email": "test@edx.org"},
                        "subject": "a subject",
                        "comment": {"body": "some details"},
                        "tags": ["test_issue", "LMS"]
                    }
                }
            ),
            mock.call.update_ticket(
                42,
                {
                    "ticket": {
                        "comment": {
                            "public": False,
                            "body":
                            "Additional information:\n\n"
                            "Client IP: 1.2.3.4\n"
                            "Host: test_server\n"
                            "Page: test_referer\n"
                            "Browser: test_user_agent"
                        }
                    }
                }
            )
        ]
        self.assertEqual(zendesk_mock_instance.mock_calls, expected_zendesk_calls)
        self._assert_datadog_called(datadog_mock, ["issue_type:test_issue"])

    @mock.patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    def test_valid_request_anon_user_configuration_override(self, zendesk_mock_class, datadog_mock):
        """
        Test a valid request from an anonymous user to a mocked out site with configuration override

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API with the additional
        tag that will come from site configuration override.
        """
        zendesk_mock_instance = zendesk_mock_class.return_value
        zendesk_mock_instance.create_ticket.return_value = 42
        self._test_success(self._anon_user, self._anon_fields)
        expected_zendesk_calls = [
            mock.call.create_ticket(
                {
                    "ticket": {
                        "recipient": "no-reply@fakeuniversity.com",
                        "requester": {"name": "Test User", "email": "test@edx.org"},
                        "subject": "a subject",
                        "comment": {"body": "some details"},
                        "tags": ["test_issue", "LMS", "whitelabel_fakeorg"]
                    }
                }
            ),
            mock.call.update_ticket(
                42,
                {
                    "ticket": {
                        "comment": {
                            "public": False,
                            "body":
                            "Additional information:\n\n"
                            "Client IP: 1.2.3.4\n"
                            "Host: test_server\n"
                            "Page: test_referer\n"
                            "Browser: test_user_agent"
                        }
                    }
                }
            )
        ]
        self.assertEqual(zendesk_mock_instance.mock_calls, expected_zendesk_calls)
        self._assert_datadog_called(datadog_mock, ["issue_type:test_issue"])

    @data("course-v1:testOrg+testCourseNumber+testCourseRun", "", None)
    @override_settings(ZENDESK_CUSTOM_FIELDS={"course_id": 1234, "enrollment_mode": 5678})
    def test_valid_request_anon_user_with_custom_fields(self, course_id, zendesk_mock, datadog_mock):
        """
        Test a valid request from an anonymous user when configured to use Zendesk Custom Fields.

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API. When course_id is
        present, it should be sent to Zendesk via a custom field. When course_id is blank or missing,
        the request should still be processed successfully.
        """
        zendesk_mock_instance = zendesk_mock.return_value
        zendesk_mock_instance.create_ticket.return_value = 42

        fields = self._anon_fields.copy()
        if course_id is not None:
            fields["course_id"] = course_id

        expected_zendesk_tags = None
        expected_datadog_tags = None
        expected_custom_fields = None
        if course_id:
            expected_zendesk_tags = [course_id, "test_issue", "LMS"]
            expected_datadog_tags = ["course_id:{}".format(course_id), "issue_type:test_issue"]
            expected_custom_fields = [{"id": 1234, "value": fields["course_id"]}]
        else:
            expected_zendesk_tags = ["test_issue", "LMS"]
            expected_datadog_tags = ["issue_type:test_issue"]

        expected_create_ticket_request = {
            "ticket": {
                "recipient": "registration@example.com",
                "requester": {"name": "Test User", "email": "test@edx.org"},
                "subject": "a subject",
                "comment": {"body": "some details"},
                "tags": expected_zendesk_tags
            }
        }

        if expected_custom_fields:
            expected_create_ticket_request["ticket"]["custom_fields"] = expected_custom_fields

        expected_update_ticket_request = {
            "ticket": {
                "comment": {
                    "public": False,
                    "body":
                    "Additional information:\n\n"
                    "Client IP: 1.2.3.4\n"
                    "Host: test_server\n"
                    "Page: test_referer\n"
                    "Browser: test_user_agent"
                }
            }
        }

        self._test_success(self._anon_user, fields)
        expected_zendesk_calls = [
            mock.call.create_ticket(expected_create_ticket_request),
            mock.call.update_ticket(42, expected_update_ticket_request)
        ]
        self.assertEqual(zendesk_mock_instance.mock_calls, expected_zendesk_calls)
        self._assert_datadog_called(datadog_mock, expected_datadog_tags)

    def test_bad_request_auth_user_no_subject(self, zendesk_mock_class, datadog_mock):
        """Test a request from an authenticated user not specifying `subject`."""
        self._test_bad_request_omit_field(self._auth_user, self._auth_fields, "subject", zendesk_mock_class, datadog_mock)
        self._test_bad_request_empty_field(self._auth_user, self._auth_fields, "subject", zendesk_mock_class, datadog_mock)

    def test_bad_request_auth_user_no_details(self, zendesk_mock_class, datadog_mock):
        """Test a request from an authenticated user not specifying `details`."""
        self._test_bad_request_omit_field(self._auth_user, self._auth_fields, "details", zendesk_mock_class, datadog_mock)
        self._test_bad_request_empty_field(self._auth_user, self._auth_fields, "details", zendesk_mock_class, datadog_mock)

    def test_valid_request_auth_user(self, zendesk_mock_class, datadog_mock):
        """
        Test a valid request from an authenticated user.

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API.
        """
        zendesk_mock_instance = zendesk_mock_class.return_value
        zendesk_mock_instance.create_ticket.return_value = 42
        self._test_success(self._auth_user, self._auth_fields)
        expected_zendesk_calls = [
            mock.call.create_ticket(
                {
                    "ticket": {
                        "recipient": "registration@example.com",
                        "requester": {"name": "Test User", "email": "test@edx.org"},
                        "subject": "a subject",
                        "comment": {"body": "some details"},
                        "tags": ["LMS"]
                    }
                }
            ),
            mock.call.update_ticket(
                42,
                {
                    "ticket": {
                        "comment": {
                            "public": False,
                            "body":
                            "Additional information:\n\n"
                            "username: test\n"
                            "Client IP: 1.2.3.4\n"
                            "Host: test_server\n"
                            "Page: test_referer\n"
                            "Browser: test_user_agent"
                        }
                    }
                }
            )
        ]
        self.assertEqual(zendesk_mock_instance.mock_calls, expected_zendesk_calls)
        self._assert_datadog_called(datadog_mock, [])

    @data(
        ("course-v1:testOrg+testCourseNumber+testCourseRun", True),
        ("course-v1:testOrg+testCourseNumber+testCourseRun", False),
        ("", None),
        (None, None)
    )
    @unpack
    @override_settings(ZENDESK_CUSTOM_FIELDS={"course_id": 1234, "enrollment_mode": 5678})
    def test_valid_request_auth_user_with_custom_fields(self, course_id, enrollment_state, zendesk_mock, datadog_mock):
        """
        Test a valid request from an authenticated user when configured to use Zendesk Custom Fields.

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API. When course_id is
        present, it should be sent to Zendesk via a custom field, along with the enrollment mode
        if the user has an active enrollment for that course. When course_id is blank or missing,
        the request should still be processed successfully.
        """
        zendesk_mock_instance = zendesk_mock.return_value
        zendesk_mock_instance.create_ticket.return_value = 42

        fields = self._auth_fields.copy()
        if course_id is not None:
            fields["course_id"] = course_id

        expected_zendesk_tags = None
        expected_datadog_tags = None
        expected_custom_fields = None
        if course_id:
            expected_zendesk_tags = [course_id, "LMS"]
            expected_datadog_tags = ["course_id:{}".format(course_id)]
            expected_custom_fields = [{"id": 1234, "value": course_id}]
            if enrollment_state is not None:
                enrollment = CourseEnrollmentFactory.create(
                    user=self._auth_user,
                    course_id=course_id,
                    is_active=enrollment_state
                )
                if enrollment.is_active:
                    expected_custom_fields.append({"id": 5678, "value": enrollment.mode})
        else:
            expected_zendesk_tags = ["LMS"]
            expected_datadog_tags = []

        expected_create_ticket_request = {
            "ticket": {
                "recipient": "registration@example.com",
                "requester": {"name": "Test User", "email": "test@edx.org"},
                "subject": "a subject",
                "comment": {"body": "some details"},
                "tags": expected_zendesk_tags
            }
        }

        if expected_custom_fields:
            expected_create_ticket_request["ticket"]["custom_fields"] = expected_custom_fields

        expected_update_ticket_request = {
            "ticket": {
                "comment": {
                    "public": False,
                    "body":
                    "Additional information:\n\n"
                    "username: test\n"
                    "Client IP: 1.2.3.4\n"
                    "Host: test_server\n"
                    "Page: test_referer\n"
                    "Browser: test_user_agent",
                }
            }
        }

        self._test_success(self._auth_user, fields)
        expected_zendesk_calls = [
            mock.call.create_ticket(expected_create_ticket_request),
            mock.call.update_ticket(42, expected_update_ticket_request)
        ]
        self.assertEqual(zendesk_mock_instance.mock_calls, expected_zendesk_calls)
        self._assert_datadog_called(datadog_mock, expected_datadog_tags)

    def test_get_request(self, zendesk_mock_class, datadog_mock):
        """Test that a GET results in a 405 even with all required fields"""
        req = self._request_factory.get("/submit_feedback", data=self._anon_fields)
        req.user = self._anon_user
        resp = views.submit_feedback(req)
        self.assertEqual(resp.status_code, 405)
        self.assertIn("Allow", resp)
        self.assertEqual(resp["Allow"], "POST")
        # There should be absolutely no interaction with Zendesk
        self.assertFalse(zendesk_mock_class.mock_calls)
        self.assertFalse(datadog_mock.mock_calls)

    def test_zendesk_error_on_create(self, zendesk_mock_class, datadog_mock):
        """
        Test Zendesk returning an error on ticket creation.

        We should return a 500 error with no body
        """
        err = ZendeskError(msg="", error_code=404)
        zendesk_mock_instance = zendesk_mock_class.return_value
        zendesk_mock_instance.create_ticket.side_effect = err
        resp = self._build_and_run_request(self._anon_user, self._anon_fields)
        self.assertEqual(resp.status_code, 500)
        self.assertFalse(resp.content)
        self._assert_datadog_called(datadog_mock, ["issue_type:test_issue"])

    def test_zendesk_error_on_update(self, zendesk_mock_class, datadog_mock):
        """
        Test for Zendesk returning an error on ticket update.

        If Zendesk returns any error on ticket update, we return a 200 to the
        browser because the update contains additional information that is not
        necessary for the user to have submitted their feedback.
        """
        err = ZendeskError(msg="", error_code=500)
        zendesk_mock_instance = zendesk_mock_class.return_value
        zendesk_mock_instance.update_ticket.side_effect = err
        resp = self._build_and_run_request(self._anon_user, self._anon_fields)
        self.assertEqual(resp.status_code, 200)
        self._assert_datadog_called(datadog_mock, ["issue_type:test_issue"])

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_FEEDBACK_SUBMISSION": False})
    def test_not_enabled(self, zendesk_mock_class, datadog_mock):
        """
        Test for Zendesk submission not enabled in `settings`.

        We should raise Http404.
        """
        with self.assertRaises(Http404):
            self._build_and_run_request(self._anon_user, self._anon_fields)

    def test_zendesk_not_configured(self, zendesk_mock_class, datadog_mock):
        """
        Test for Zendesk not fully configured in `settings`.

        For each required configuration parameter, test that setting it to
        `None` causes an otherwise valid request to return a 500 error.
        """
        def test_case(missing_config):
            with mock.patch(missing_config, None):
                with self.assertRaises(Exception):
                    self._build_and_run_request(self._anon_user, self._anon_fields)

        test_case("django.conf.settings.ZENDESK_URL")
        test_case("django.conf.settings.ZENDESK_USER")
        test_case("django.conf.settings.ZENDESK_API_KEY")

    @mock.patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_support_backend_values)
    def test_valid_request_over_email(self, zendesk_mock_class, datadog_mock):  # pylint: disable=unused-argument
        with mock.patch("util.views.send_mail") as patched_send_email:
            resp = self._build_and_run_request(self._anon_user, self._anon_fields)
            self.assertEqual(patched_send_email.call_count, 1)
            self.assertIn(self._anon_fields["email"], str(patched_send_email.call_args))
        self.assertEqual(resp.status_code, 200)

    @mock.patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_support_backend_values)
    def test_exception_request_over_email(self, zendesk_mock_class, datadog_mock):  # pylint: disable=unused-argument
        with mock.patch("util.views.send_mail", side_effect=SMTPException) as patched_send_email:
            resp = self._build_and_run_request(self._anon_user, self._anon_fields)
            self.assertEqual(patched_send_email.call_count, 1)
            self.assertIn(self._anon_fields["email"], str(patched_send_email.call_args))
        self.assertEqual(resp.status_code, 500)
