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
            StudioValidationMessage("unknown type", u"Unknown type info")

        with pytest.raises(TypeError):
            StudioValidationMessage(StudioValidationMessage.WARNING, u"bad warning", action_class=0)

        with pytest.raises(TypeError):
            StudioValidationMessage(StudioValidationMessage.WARNING, u"bad warning", action_runtime_event=0)

        with pytest.raises(TypeError):
            StudioValidationMessage(StudioValidationMessage.WARNING, u"bad warning", action_label=b"Non-unicode string")

    def test_to_json(self):
        """
        Test the `to_json` method.
        """
        self.assertEqual(
            {
                "type": StudioValidationMessage.NOT_CONFIGURED,
                "text": u"Not Configured message",
                "action_label": u"Action label"
            },
            StudioValidationMessage(
                StudioValidationMessage.NOT_CONFIGURED, u"Not Configured message", action_label=u"Action label"
            ).to_json()
        )

        self.assertEqual(
            {
                "type": StudioValidationMessage.WARNING,
                "text": u"Warning message",
                "action_class": "class-for-action"
            },
            StudioValidationMessage(
                StudioValidationMessage.WARNING, u"Warning message", action_class="class-for-action"
            ).to_json()
        )

        self.assertEqual(
            {
                "type": StudioValidationMessage.ERROR,
                "text": u"Error message",
                "action_runtime_event": "do-fix-up"
            },
            StudioValidationMessage(
                StudioValidationMessage.ERROR, u"Error message", action_runtime_event="do-fix-up"
            ).to_json()
        )


class StudioValidationTest(unittest.TestCase):
    """
    Tests for `StudioValidation` class.
    """

    def test_copy(self):
        validation = Validation("id")
        validation.add(ValidationMessage(ValidationMessage.ERROR, u"Error message"))

        studio_validation = StudioValidation.copy(validation)
        self.assertIsInstance(studio_validation, StudioValidation)
        self.assertFalse(studio_validation)
        self.assertEqual(1, len(studio_validation.messages))
        expected = {
            "type": StudioValidationMessage.ERROR,
            "text": u"Error message"
        }
        self.assertEqual(expected, studio_validation.messages[0].to_json())
        self.assertIsNone(studio_validation.summary)

    def test_copy_studio_validation(self):
        validation = StudioValidation("id")
        validation.add(
            StudioValidationMessage(StudioValidationMessage.WARNING, u"Warning message", action_label=u"Action Label")
        )

        validation_copy = StudioValidation.copy(validation)
        self.assertFalse(validation_copy)
        self.assertEqual(1, len(validation_copy.messages))
        expected = {
            "type": StudioValidationMessage.WARNING,
            "text": u"Warning message",
            "action_label": u"Action Label"
        }
        self.assertEqual(expected, validation_copy.messages[0].to_json())

    def test_copy_errors(self):
        with pytest.raises(TypeError):
            StudioValidation.copy("foo")

    def test_empty(self):
        """
        Test that `empty` return True iff there are no messages and no summary.
        Also test the "bool" property of `Validation`.
        """
        validation = StudioValidation("id")
        self.assertTrue(validation.empty)
        self.assertTrue(validation)

        validation.add(StudioValidationMessage(StudioValidationMessage.ERROR, u"Error message"))
        self.assertFalse(validation.empty)
        self.assertFalse(validation)

        validation_with_summary = StudioValidation("id")
        validation_with_summary.set_summary(
            StudioValidationMessage(StudioValidationMessage.NOT_CONFIGURED, u"Summary message")
        )
        self.assertFalse(validation.empty)
        self.assertFalse(validation)

    def test_add_messages(self):
        """
        Test the behavior of calling `add_messages` with combination of `StudioValidation` instances.
        """
        validation_1 = StudioValidation("id")
        validation_1.set_summary(StudioValidationMessage(StudioValidationMessage.WARNING, u"Summary message"))
        validation_1.add(StudioValidationMessage(StudioValidationMessage.ERROR, u"Error message"))

        validation_2 = StudioValidation("id")
        validation_2.set_summary(StudioValidationMessage(StudioValidationMessage.ERROR, u"Summary 2 message"))
        validation_2.add(StudioValidationMessage(StudioValidationMessage.NOT_CONFIGURED, u"Not configured"))

        validation_1.add_messages(validation_2)
        self.assertEqual(2, len(validation_1.messages))

        self.assertEqual(StudioValidationMessage.ERROR, validation_1.messages[0].type)
        self.assertEqual(u"Error message", validation_1.messages[0].text)

        self.assertEqual(StudioValidationMessage.NOT_CONFIGURED, validation_1.messages[1].type)
        self.assertEqual(u"Not configured", validation_1.messages[1].text)

        self.assertEqual(StudioValidationMessage.WARNING, validation_1.summary.type)
        self.assertEqual(u"Summary message", validation_1.summary.text)

    def test_set_summary_accepts_validation_message(self):
        """
        Test that `set_summary` accepts a ValidationMessage.
        """
        validation = StudioValidation("id")
        validation.set_summary(ValidationMessage(ValidationMessage.WARNING, u"Summary message"))
        self.assertEqual(ValidationMessage.WARNING, validation.summary.type)
        self.assertEqual(u"Summary message", validation.summary.text)

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
        self.assertEqual(expected, validation.to_json())

        validation.add(
            StudioValidationMessage(
                StudioValidationMessage.ERROR,
                u"Error message",
                action_label=u"Action label",
                action_class="edit-button"
            )
        )
        validation.add(
            StudioValidationMessage(
                StudioValidationMessage.NOT_CONFIGURED,
                u"Not configured message",
                action_label=u"Action label",
                action_runtime_event="make groups"
            )
        )
        validation.set_summary(
            StudioValidationMessage(
                StudioValidationMessage.WARNING,
                u"Summary message",
                action_label=u"Summary label",
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
                    "text": u"Error message",
                    "action_label": u"Action label",
                    "action_class": "edit-button"
                },
                {
                    "type": "not-configured",
                    "text": u"Not configured message",
                    "action_label": u"Action label",
                    "action_runtime_event": "make groups"
                }
            ],
            "summary": {
                "type": "warning",
                "text": u"Summary message",
                "action_label": u"Summary label",
                "action_runtime_event": "fix everything"
            },
            "empty": False
        }
        self.assertEqual(expected, validation.to_json())
