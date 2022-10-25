"""
Test xblock/validation.py
"""


import unittest

import pytest
from xblock.validation import Validation, ValidationMessage

from xmodule.validation import StudioValidation, StudioValidationMessage


class StudioValidationMessageTest(unittest.TestCase):
    """
    Tests for `ValidationMessage`
    """

    def test_bad_parameters(self):
        """
        Test that `TypeError`s are thrown for bad input parameters.
        """
        with pytest.raises(TypeError):
            StudioValidationMessage("unknown type", "Unknown type info")

        with pytest.raises(TypeError):
            StudioValidationMessage(StudioValidationMessage.WARNING, "bad warning", action_class=0)

        with pytest.raises(TypeError):
            StudioValidationMessage(StudioValidationMessage.WARNING, "bad warning", action_runtime_event=0)

        with pytest.raises(TypeError):
            StudioValidationMessage(StudioValidationMessage.WARNING, "bad warning", action_label=b"Non-unicode string")

    def test_to_json(self):
        """
        Test the `to_json` method.
        """
        assert \
            {'type': StudioValidationMessage.NOT_CONFIGURED,
             'text': 'Not Configured message', 'action_label': 'Action label'} == \
            StudioValidationMessage(StudioValidationMessage.NOT_CONFIGURED,
                                    'Not Configured message', action_label='Action label').to_json()

        assert \
            {'type': StudioValidationMessage.WARNING,
             'text': 'Warning message',
             'action_class': 'class-for-action'} ==\
            StudioValidationMessage(StudioValidationMessage.WARNING, 'Warning message',
                                    action_class='class-for-action').to_json()

        assert \
            {'type': StudioValidationMessage.ERROR,
             'text': 'Error message', 'action_runtime_event': 'do-fix-up'} ==\
            StudioValidationMessage(StudioValidationMessage.ERROR,
                                    'Error message', action_runtime_event='do-fix-up').to_json()


class StudioValidationTest(unittest.TestCase):
    """
    Tests for `StudioValidation` class.
    """

    def test_copy(self):
        validation = Validation("id")
        validation.add(ValidationMessage(ValidationMessage.ERROR, "Error message"))

        studio_validation = StudioValidation.copy(validation)
        assert isinstance(studio_validation, StudioValidation)
        assert not studio_validation
        assert 1 == len(studio_validation.messages)
        expected = {
            "type": StudioValidationMessage.ERROR,
            "text": "Error message"
        }
        assert expected == studio_validation.messages[0].to_json()
        assert studio_validation.summary is None

    def test_copy_studio_validation(self):
        validation = StudioValidation("id")
        validation.add(
            StudioValidationMessage(StudioValidationMessage.WARNING, "Warning message", action_label="Action Label")
        )

        validation_copy = StudioValidation.copy(validation)
        assert not validation_copy
        assert 1 == len(validation_copy.messages)
        expected = {
            "type": StudioValidationMessage.WARNING,
            "text": "Warning message",
            "action_label": "Action Label"
        }
        assert expected == validation_copy.messages[0].to_json()

    def test_copy_errors(self):
        with pytest.raises(TypeError):
            StudioValidation.copy("foo")

    def test_empty(self):
        """
        Test that `empty` return True iff there are no messages and no summary.
        Also test the "bool" property of `Validation`.
        """
        validation = StudioValidation("id")
        assert validation.empty
        assert validation

        validation.add(StudioValidationMessage(StudioValidationMessage.ERROR, "Error message"))
        assert not validation.empty
        assert not validation

        validation_with_summary = StudioValidation("id")
        validation_with_summary.set_summary(
            StudioValidationMessage(StudioValidationMessage.NOT_CONFIGURED, "Summary message")
        )
        assert not validation.empty
        assert not validation

    def test_add_messages(self):
        """
        Test the behavior of calling `add_messages` with combination of `StudioValidation` instances.
        """
        validation_1 = StudioValidation("id")
        validation_1.set_summary(StudioValidationMessage(StudioValidationMessage.WARNING, "Summary message"))
        validation_1.add(StudioValidationMessage(StudioValidationMessage.ERROR, "Error message"))

        validation_2 = StudioValidation("id")
        validation_2.set_summary(StudioValidationMessage(StudioValidationMessage.ERROR, "Summary 2 message"))
        validation_2.add(StudioValidationMessage(StudioValidationMessage.NOT_CONFIGURED, "Not configured"))

        validation_1.add_messages(validation_2)
        assert 2 == len(validation_1.messages)

        assert StudioValidationMessage.ERROR == validation_1.messages[0].type
        assert 'Error message' == validation_1.messages[0].text

        assert StudioValidationMessage.NOT_CONFIGURED == validation_1.messages[1].type
        assert 'Not configured' == validation_1.messages[1].text

        assert StudioValidationMessage.WARNING == validation_1.summary.type
        assert 'Summary message' == validation_1.summary.text

    def test_set_summary_accepts_validation_message(self):
        """
        Test that `set_summary` accepts a ValidationMessage.
        """
        validation = StudioValidation("id")
        validation.set_summary(ValidationMessage(ValidationMessage.WARNING, "Summary message"))
        assert ValidationMessage.WARNING == validation.summary.type
        assert 'Summary message' == validation.summary.text

    def test_set_summary_errors(self):
        """
        Test that `set_summary` errors if argument is not a ValidationMessage.
        """
        with pytest.raises(TypeError):
            StudioValidation("id").set_summary("foo")

    def test_to_json(self):
        """
        Test the ability to serialize a `StudioValidation` instance.
        """
        validation = StudioValidation("id")
        expected = {
            "xblock_id": "id",
            "messages": [],
            "empty": True
        }
        assert expected == validation.to_json()

        validation.add(
            StudioValidationMessage(
                StudioValidationMessage.ERROR,
                "Error message",
                action_label="Action label",
                action_class="edit-button"
            )
        )
        validation.add(
            StudioValidationMessage(
                StudioValidationMessage.NOT_CONFIGURED,
                "Not configured message",
                action_label="Action label",
                action_runtime_event="make groups"
            )
        )
        validation.set_summary(
            StudioValidationMessage(
                StudioValidationMessage.WARNING,
                "Summary message",
                action_label="Summary label",
                action_runtime_event="fix everything"
            )
        )

        # Note: it is important to test all the expected strings here because the client-side model depends on them
        # (for instance, "warning" vs. using the xblock constant ValidationMessageTypes.WARNING).
        expected = {
            "xblock_id": "id",
            "messages": [
                {
                    "type": "error",
                    "text": "Error message",
                    "action_label": "Action label",
                    "action_class": "edit-button"
                },
                {
                    "type": "not-configured",
                    "text": "Not configured message",
                    "action_label": "Action label",
                    "action_runtime_event": "make groups"
                }
            ],
            "summary": {
                "type": "warning",
                "text": "Summary message",
                "action_label": "Summary label",
                "action_runtime_event": "fix everything"
            },
            "empty": False
        }
        assert expected == validation.to_json()
