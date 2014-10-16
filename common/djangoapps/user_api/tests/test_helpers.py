"""
Tests for helper functions.
"""
import json
import mock
import ddt
from django.test import TestCase
from nose.tools import raises
from django.http import HttpRequest, HttpResponse
from user_api.helpers import (
    intercept_errors, shim_student_view,
    FormDescription, InvalidFieldError
)


class FakeInputException(Exception):
    """Fake exception that should be intercepted. """
    pass


class FakeOutputException(Exception):
    """Fake exception that should be raised. """
    pass


@intercept_errors(FakeOutputException, ignore_errors=[ValueError])
def intercepted_function(raise_error=None):
    """Function used to test the intercept error decorator.

    Keyword Arguments:
        raise_error (Exception): If provided, raise this exception.

    """
    if raise_error is not None:
        raise raise_error


class InterceptErrorsTest(TestCase):
    """
    Tests for the decorator that intercepts errors.
    """

    @raises(FakeOutputException)
    def test_intercepts_errors(self):
        intercepted_function(raise_error=FakeInputException)

    def test_ignores_no_error(self):
        intercepted_function()

    @raises(ValueError)
    def test_ignores_expected_errors(self):
        intercepted_function(raise_error=ValueError)

    @mock.patch('user_api.helpers.LOGGER')
    def test_logs_errors(self, mock_logger):
        expected_log_msg = (
            u"An unexpected error occurred when calling 'intercepted_function' "
            u"with arguments '()' and "
            u"keyword arguments '{'raise_error': <class 'user_api.tests.test_helpers.FakeInputException'>}': "
            u"FakeInputException()"
        )

        # Verify that the raised exception has the error message
        try:
            intercepted_function(raise_error=FakeInputException)
        except FakeOutputException as ex:
            self.assertEqual(ex.message, expected_log_msg)

        # Verify that the error logger is called
        # This will include the stack trace for the original exception
        # because it's called with log level "ERROR"
        mock_logger.exception.assert_called_once_with(expected_log_msg)


class FormDescriptionTest(TestCase):

    def test_to_json(self):
        desc = FormDescription("post", "/submit")
        desc.add_field(
            "name",
            label="label",
            field_type="text",
            default="default",
            placeholder="placeholder",
            instructions="instructions",
            required=True,
            restrictions={
                "min_length": 2,
                "max_length": 10
            }
        )

        self.assertEqual(desc.to_json(), json.dumps({
            "method": "post",
            "submit_url": "/submit",
            "fields": [
                {
                    "name": "name",
                    "label": "label",
                    "type": "text",
                    "default": "default",
                    "placeholder": "placeholder",
                    "instructions": "instructions",
                    "required": True,
                    "restrictions": {
                        "min_length": 2,
                        "max_length": 10,
                    }
                }
            ]
        }))

    def test_invalid_field_type(self):
        desc = FormDescription("post", "/submit")
        with self.assertRaises(InvalidFieldError):
            desc.add_field("invalid", field_type="invalid")

    def test_missing_options(self):
        desc = FormDescription("post", "/submit")
        with self.assertRaises(InvalidFieldError):
            desc.add_field("name", field_type="select")

    def test_invalid_restriction(self):
        desc = FormDescription("post", "/submit")
        with self.assertRaises(InvalidFieldError):
            desc.add_field("name", field_type="text", restrictions={"invalid": 0})


@ddt.ddt
class StudentViewShimTest(TestCase):

    def setUp(self):
        self.captured_request = None

    def test_strip_enrollment_action(self):
        view = self._shimmed_view(HttpResponse())
        request = HttpRequest()
        request.POST["enrollment_action"] = "enroll"
        request.POST["course_id"] = "edx/101/demo"
        view(request)

        # Expect that the enrollment action and course ID
        # were stripped out before reaching the wrapped view.
        self.assertNotIn("enrollment_action", self.captured_request.POST)
        self.assertNotIn("course_id", self.captured_request.POST)

    def test_non_json_response(self):
        view = self._shimmed_view(HttpResponse(content="Not a JSON dict"))
        response = view(HttpRequest())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "Not a JSON dict")

    @ddt.data("redirect", "redirect_url")
    def test_redirect_from_json(self, redirect_key):
        view = self._shimmed_view(
            HttpResponse(content=json.dumps({
                "success": True,
                redirect_key: "/redirect"
            }))
        )
        response = view(HttpRequest())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.content, "/redirect")

    def test_error_from_json(self):
        view = self._shimmed_view(
            HttpResponse(content=json.dumps({
                "success": False,
                "value": "Error!"
            }))
        )
        response = view(HttpRequest())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, "Error!")

    def test_preserve_headers(self):
        view_response = HttpResponse()
        view_response["test-header"] = "test"
        view = self._shimmed_view(view_response)
        response = view(HttpRequest())
        self.assertEqual(response["test-header"], "test")

    def _shimmed_view(self, response):
        def stub_view(request):
            self.captured_request = request
            return response
        return shim_student_view(stub_view)
