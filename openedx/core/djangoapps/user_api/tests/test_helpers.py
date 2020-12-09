"""
Tests for helper functions.
"""


import json
import re

import ddt
import mock
import pytest
from django import forms
from django.test import TestCase
from six import text_type

from ..helpers import FormDescription, InvalidFieldError, intercept_errors


class FakeInputException(Exception):
    """Fake exception that should be intercepted."""
    pass


class FakeOutputException(Exception):
    """Fake exception that should be raised."""
    pass


@intercept_errors(FakeOutputException, ignore_errors=[ValueError])
def intercepted_function(raise_error=None):
    """Function used to test the intercept error decorator.

    Keyword Arguments:
        raise_error (Exception): If provided, raise this exception.

    """
    if raise_error is not None:
        raise raise_error                   # pylint: disable=raising-bad-type


class InterceptErrorsTest(TestCase):
    """Tests for the decorator that intercepts errors."""

    def test_intercepts_errors(self):
        with pytest.raises(FakeOutputException):
            intercepted_function(raise_error=FakeInputException)

    def test_ignores_no_error(self):
        intercepted_function()

    def test_ignores_expected_errors(self):
        with pytest.raises(ValueError):
            intercepted_function(raise_error=ValueError)

    @mock.patch('openedx.core.djangoapps.user_api.helpers.LOGGER')
    def test_logs_errors(self, mock_logger):
        self.maxDiff = None
        exception = 'openedx.core.djangoapps.user_api.tests.test_helpers.FakeInputException'
        expected_log_msg = (
            u"An unexpected error occurred when calling 'intercepted_function' with arguments '()' and "
            u"keyword arguments '{{'raise_error': <class '{}'>}}' "
            u"from File \"{}\", line XXX, in test_logs_errors\n"
            u"    intercepted_function(raise_error=FakeInputException): FakeInputException()"
        ).format(exception, __file__.rstrip('c'))

        # Verify that the raised exception has the error message
        try:
            intercepted_function(raise_error=FakeInputException)
        except FakeOutputException as ex:
            actual_message = re.sub(r'line \d+', 'line XXX', text_type(ex), flags=re.MULTILINE)
            self.assertEqual(actual_message, expected_log_msg)

        # Verify that the error logger is called
        # This will include the stack trace for the original exception
        # because it's called with log level "ERROR"
        calls = mock_logger.exception.mock_calls
        self.assertEqual(len(calls), 1)
        name, args, kwargs = calls[0]

        self.assertEqual(name, '')
        self.assertEqual(len(args), 1)
        self.assertEqual(kwargs, {})

        actual_message = re.sub(r'line \d+', 'line XXX', args[0], flags=re.MULTILINE)
        self.assertEqual(actual_message, expected_log_msg)


class FormDescriptionTest(TestCase):
    """Tests of helper functions which generate form descriptions."""
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
            },
            error_messages={
                "required": "You must provide a value!"
            },
            supplementalLink="",
            supplementalText="",
        )

        self.assertEqual(desc.to_json(), json.dumps({
            "method": "post",
            "submit_url": "/submit",
            "fields": [
                {
                    "name": "name",
                    "label": "label",
                    "type": "text",
                    "defaultValue": "default",
                    "placeholder": "placeholder",
                    "instructions": "instructions",
                    "required": True,
                    "restrictions": {
                        "min_length": 2,
                        "max_length": 10,
                    },
                    "errorMessages": {
                        "required": "You must provide a value!"
                    },
                    "supplementalLink": "",
                    "supplementalText": "",
                    "loginIssueSupportLink": "https://support.example.com/login-issue-help.html",
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

    def test_option_overrides(self):
        desc = FormDescription("post", "/submit")
        field = {
            "name": "country",
            "label": "Country",
            "field_type": "select",
            "default": "PK",
            "required": True,
            "error_messages": {
                "required": "You must provide a value!"
            },
            "options": [
                ("US", "United States of America"),
                ("PK", "Pakistan")
            ]
        }
        desc.override_field_properties(
            field["name"],
            default="PK"
        )
        desc.add_field(**field)
        self.assertEqual(
            desc.fields[0]["options"],
            [
                {
                    'default': False,
                    'name': 'United States of America',
                    'value': 'US'
                },
                {
                    'default': True,
                    'name': 'Pakistan',
                    'value': 'PK'
                }

            ]
        )


class DummyRegistrationExtensionModel(object):
    """
    Dummy registration object
    """
    user = None

    def save(self):
        """
        Dummy save method for dummy model.
        """
        return None


class TestCaseForm(forms.Form):
    """
    Test registration extension form.
    """
    DUMMY_STORAGE = {}

    MOVIE_MIN_LEN = 3
    MOVIE_MAX_LEN = 100

    FAVORITE_EDITOR = (
        ('vim', 'Vim'),
        ('emacs', 'Emacs'),
        ('np', 'Notepad'),
        ('cat', 'cat > filename')
    )

    favorite_movie = forms.CharField(
        label="Fav Flick", min_length=MOVIE_MIN_LEN, max_length=MOVIE_MAX_LEN, error_messages={
            "required": u"Please tell us your favorite movie.",
            "invalid": u"We're pretty sure you made that movie up."
        }
    )
    favorite_editor = forms.ChoiceField(label="Favorite Editor", choices=FAVORITE_EDITOR, required=False, initial='cat')

    def save(self, commit=None):  # pylint: disable=unused-argument
        """
        Store the result in the dummy storage dict.
        """
        self.DUMMY_STORAGE.update({
            'favorite_movie': self.cleaned_data.get('favorite_movie'),
            'favorite_editor': self.cleaned_data.get('favorite_editor'),
        })
        dummy_model = DummyRegistrationExtensionModel()
        return dummy_model

    class Meta(object):
        """
        Set options for fields which can't be conveyed in their definition.
        """
        serialization_options = {
            'favorite_editor': {
                'default': 'vim',
            },
        }
