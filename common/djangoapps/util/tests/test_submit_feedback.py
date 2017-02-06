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

TEST_SUPPORT_EMAIL = "support@example.com"
TEST_ZENDESK_CUSTOM_FIELD_CONFIG = {"course_id": 1234, "enrollment_mode": 5678}
TEST_REQUEST_HEADERS = {
    "HTTP_REFERER": "test_referer",
    "HTTP_USER_AGENT": "test_user_agent",
    "REMOTE_ADDR": "1.2.3.4",
    "SERVER_NAME": "test_server",
}


def fake_support_backend_values(name, default=None):  # pylint: disable=unused-argument
    """
    Method for getting configuration override values for support email.
    """
    config_dict = {
        "CONTACT_FORM_SUBMISSION_BACKEND": "email",
        "email_from_address": TEST_SUPPORT_EMAIL,
    }
    return config_dict[name]


@ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_FEEDBACK_SUBMISSION": True})
@override_settings(
    DEFAULT_FROM_EMAIL=TEST_SUPPORT_EMAIL,
    ZENDESK_URL="dummy",
    ZENDESK_USER="dummy",
    ZENDESK_API_KEY="dummy",
    ZENDESK_CUSTOM_FIELDS={}
)
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
            HTTP_REFERER=TEST_REQUEST_HEADERS["HTTP_REFERER"],
            HTTP_USER_AGENT=TEST_REQUEST_HEADERS["HTTP_USER_AGENT"],
            REMOTE_ADDR=TEST_REQUEST_HEADERS["REMOTE_ADDR"],
            SERVER_NAME=TEST_REQUEST_HEADERS["SERVER_NAME"],
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

    def _build_zendesk_ticket(self, recipient, name, email, subject, details, tags, custom_fields=None):
        """
        Build a Zendesk ticket that can be used in assertions to verify that the correct
        data was submitted to create a Zendesk ticket.
        """
        ticket = {
            "ticket": {
                "recipient": recipient,
                "requester": {"name": name, "email": email},
                "subject": subject,
                "comment": {"body": details},
                "tags": tags
            }
        }

        if custom_fields is not None:
            ticket["ticket"]["custom_fields"] = custom_fields

        return ticket

    def _build_zendesk_ticket_update(self, request_headers, username=None):
        """
        Build a Zendesk ticket update that can be used in assertions to verify that the correct
        data was submitted to update a Zendesk ticket.
        """
        body = []
        if username:
            body.append("username: {}".format(username))

        # FIXME the tests rely on the body string being built in this specific order, which doesn't seem
        # reliable given that the view builds the string by iterating over a dictionary.
        header_text_mapping = [
            ("Client IP", "REMOTE_ADDR"),
            ("Host", "SERVER_NAME"),
            ("Page", "HTTP_REFERER"),
            ("Browser", "HTTP_USER_AGENT")
        ]

        for text, header in header_text_mapping:
            body.append("{}: {}".format(text, request_headers[header]))

        body = "Additional information:\n\n" + "\n".join(body)
        return {"ticket": {"comment": {"public": False, "body": body}}}

    def _assert_zendesk_called(self, zendesk_mock, ticket_id, ticket, ticket_update):
        """Assert that Zendesk was called with the correct ticket and ticket_update."""
        expected_zendesk_calls = [mock.call.create_ticket(ticket), mock.call.update_ticket(ticket_id, ticket_update)]
        self.assertEqual(zendesk_mock.mock_calls, expected_zendesk_calls)

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
        user = self._anon_user
        fields = self._anon_fields

        ticket_id = 42
        zendesk_mock_instance.create_ticket.return_value = ticket_id

        ticket = self._build_zendesk_ticket(
            recipient=TEST_SUPPORT_EMAIL,
            name=fields["name"],
            email=fields["email"],
            subject=fields["subject"],
            details=fields["details"],
            tags=[fields["issue_type"], "LMS"]
        )

        ticket_update = self._build_zendesk_ticket_update(TEST_REQUEST_HEADERS)

        self._test_success(user, fields)
        self._assert_zendesk_called(zendesk_mock_instance, ticket_id, ticket, ticket_update)
        self._assert_datadog_called(datadog_mock, ["issue_type:{}".format(fields["issue_type"])])

    @mock.patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    def test_valid_request_anon_user_configuration_override(self, zendesk_mock_class, datadog_mock):
        """
        Test a valid request from an anonymous user to a mocked out site with configuration override

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API with the additional
        tag that will come from site configuration override.
        """
        zendesk_mock_instance = zendesk_mock_class.return_value
        user = self._anon_user
        fields = self._anon_fields

        ticket_id = 42
        zendesk_mock_instance.create_ticket.return_value = ticket_id

        ticket = self._build_zendesk_ticket(
            recipient=fake_get_value("email_from_address"),
            name=fields["name"],
            email=fields["email"],
            subject=fields["subject"],
            details=fields["details"],
            tags=[fields["issue_type"], "LMS", "whitelabel_{}".format(fake_get_value("course_org_filter"))]
        )

        ticket_update = self._build_zendesk_ticket_update(TEST_REQUEST_HEADERS)

        self._test_success(user, fields)
        self._assert_zendesk_called(zendesk_mock_instance, ticket_id, ticket, ticket_update)
        self._assert_datadog_called(datadog_mock, ["issue_type:{}".format(fields["issue_type"])])

    @data("course-v1:testOrg+testCourseNumber+testCourseRun", "", None)
    @override_settings(ZENDESK_CUSTOM_FIELDS=TEST_ZENDESK_CUSTOM_FIELD_CONFIG)
    def test_valid_request_anon_user_with_custom_fields(self, course_id, zendesk_mock_class, datadog_mock):
        """
        Test a valid request from an anonymous user when configured to use Zendesk Custom Fields.

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API. When course_id is
        present, it should be sent to Zendesk via a custom field. When course_id is blank or missing,
        the request should still be processed successfully.
        """
        zendesk_mock_instance = zendesk_mock_class.return_value
        user = self._anon_user

        fields = self._anon_fields.copy()
        if course_id is not None:
            fields["course_id"] = course_id

        ticket_id = 42
        zendesk_mock_instance.create_ticket.return_value = ticket_id

        zendesk_tags = [fields["issue_type"], "LMS"]
        datadog_tags = ["issue_type:{}".format(fields["issue_type"])]
        zendesk_custom_fields = None
        if course_id:
            # FIXME the tests rely on the tags being in this specific order, which doesn't seem
            # reliable given that the view builds the list by iterating over a dictionary.
            zendesk_tags.insert(0, course_id)
            datadog_tags.insert(0, "course_id:{}".format(course_id))
            zendesk_custom_fields = [
                {"id": TEST_ZENDESK_CUSTOM_FIELD_CONFIG["course_id"], "value": course_id}
            ]

        ticket = self._build_zendesk_ticket(
            recipient=TEST_SUPPORT_EMAIL,
            name=fields["name"],
            email=fields["email"],
            subject=fields["subject"],
            details=fields["details"],
            tags=zendesk_tags,
            custom_fields=zendesk_custom_fields
        )

        ticket_update = self._build_zendesk_ticket_update(TEST_REQUEST_HEADERS)

        self._test_success(user, fields)
        self._assert_zendesk_called(zendesk_mock_instance, ticket_id, ticket, ticket_update)
        self._assert_datadog_called(datadog_mock, datadog_tags)

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
        user = self._auth_user
        fields = self._auth_fields

        ticket_id = 42
        zendesk_mock_instance.create_ticket.return_value = ticket_id

        ticket = self._build_zendesk_ticket(
            recipient=TEST_SUPPORT_EMAIL,
            name=user.profile.name,
            email=user.email,
            subject=fields["subject"],
            details=fields["details"],
            tags=["LMS"]
        )

        ticket_update = self._build_zendesk_ticket_update(TEST_REQUEST_HEADERS, user.username)

        self._test_success(user, fields)
        self._assert_zendesk_called(zendesk_mock_instance, ticket_id, ticket, ticket_update)
        self._assert_datadog_called(datadog_mock, [])

    @data(
        ("course-v1:testOrg+testCourseNumber+testCourseRun", True),
        ("course-v1:testOrg+testCourseNumber+testCourseRun", False),
        ("", None),
        (None, None)
    )
    @unpack
    @override_settings(ZENDESK_CUSTOM_FIELDS=TEST_ZENDESK_CUSTOM_FIELD_CONFIG)
    def test_valid_request_auth_user_with_custom_fields(self, course_id, enrolled, zendesk_mock_class, datadog_mock):
        """
        Test a valid request from an authenticated user when configured to use Zendesk Custom Fields.

        The response should have a 200 (success) status code, and a ticket with
        the given information should have been submitted via the Zendesk API. When course_id is
        present, it should be sent to Zendesk via a custom field, along with the enrollment mode
        if the user has an active enrollment for that course. When course_id is blank or missing,
        the request should still be processed successfully.
        """
        zendesk_mock_instance = zendesk_mock_class.return_value
        user = self._auth_user

        fields = self._auth_fields.copy()
        if course_id is not None:
            fields["course_id"] = course_id

        ticket_id = 42
        zendesk_mock_instance.create_ticket.return_value = ticket_id

        zendesk_tags = ["LMS"]
        datadog_tags = []
        zendesk_custom_fields = None
        if course_id:
            # FIXME the tests rely on the tags being in this specific order, which doesn't seem
            # reliable given that the view builds the list by iterating over a dictionary.
            zendesk_tags.insert(0, course_id)
            datadog_tags.insert(0, "course_id:{}".format(course_id))
            zendesk_custom_fields = [
                {"id": TEST_ZENDESK_CUSTOM_FIELD_CONFIG["course_id"], "value": course_id}
            ]
            if enrolled is not None:
                enrollment = CourseEnrollmentFactory.create(
                    user=user,
                    course_id=course_id,
                    is_active=enrolled
                )
                if enrollment.is_active:
                    zendesk_custom_fields.append(
                        {"id": TEST_ZENDESK_CUSTOM_FIELD_CONFIG["enrollment_mode"], "value": enrollment.mode}
                    )

        ticket = self._build_zendesk_ticket(
            recipient=TEST_SUPPORT_EMAIL,
            name=user.profile.name,
            email=user.email,
            subject=fields["subject"],
            details=fields["details"],
            tags=zendesk_tags,
            custom_fields=zendesk_custom_fields
        )

        ticket_update = self._build_zendesk_ticket_update(TEST_REQUEST_HEADERS, user.username)

        self._test_success(user, fields)
        self._assert_zendesk_called(zendesk_mock_instance, ticket_id, ticket, ticket_update)
        self._assert_datadog_called(datadog_mock, datadog_tags)

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
        self._assert_datadog_called(datadog_mock, ["issue_type:{}".format(self._anon_fields["issue_type"])])

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
        self._assert_datadog_called(datadog_mock, ["issue_type:{}".format(self._anon_fields["issue_type"])])

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
