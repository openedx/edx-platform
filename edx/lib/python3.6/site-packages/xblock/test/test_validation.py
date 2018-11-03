"""
Test xblock/validation.py
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest
import pytest

from xblock.validation import ValidationMessage, Validation


class ValidationMessageTest(unittest.TestCase):
    """
    Tests for `ValidationMessage`
    """

    def test_bad_parameters(self):
        """
        Test that `TypeError`s are thrown for bad input parameters.
        """
        with pytest.raises(TypeError):
            ValidationMessage("unknown type", "Unknown type info")

        with pytest.raises(TypeError):
            ValidationMessage(ValidationMessage.WARNING, b"Non-unicode message")

    def test_to_json(self):
        """
        Test the `to_json` method.
        """
        expected = {"type": ValidationMessage.ERROR, "text": "Error message"}
        self.assertEqual(expected, ValidationMessage(ValidationMessage.ERROR, "Error message").to_json())

        expected = {"type": ValidationMessage.WARNING, "text": "Warning message"}
        self.assertEqual(expected, ValidationMessage(ValidationMessage.WARNING, "Warning message").to_json())


class ValidationTest(unittest.TestCase):
    """
    Tests for `Validation` class.
    """

    def test_empty(self):
        """
        Test that `empty` return True iff there are no messages.
        Also test the "bool" property of `Validation`.
        """
        validation = Validation("id")
        self.assertTrue(validation.empty)
        self.assertTrue(validation)

        validation.add(ValidationMessage(ValidationMessage.ERROR, "Error message"))
        self.assertFalse(validation.empty)
        self.assertFalse(validation)

    def test_add_messages(self):
        """
        Test the behavior of adding the messages from another `Validation` object to this instance.
        """
        validation_1 = Validation("id")
        validation_1.add(ValidationMessage(ValidationMessage.ERROR, "Error message"))

        validation_2 = Validation("id")
        validation_2.add(ValidationMessage(ValidationMessage.WARNING, "Warning message"))

        validation_1.add_messages(validation_2)
        self.assertEqual(2, len(validation_1.messages))

        self.assertEqual(ValidationMessage.ERROR, validation_1.messages[0].type)
        self.assertEqual("Error message", validation_1.messages[0].text)

        self.assertEqual(ValidationMessage.WARNING, validation_1.messages[1].type)
        self.assertEqual("Warning message", validation_1.messages[1].text)

    def test_add_messages_error(self):
        """
        Test that calling `add_messages` with something that is not a `Validation` instances throw an error.
        """
        validation = Validation("id")

        with pytest.raises(TypeError):
            validation.add_messages("foo")

    def test_to_json(self):
        """
        Test the ability to serialize a `Validation` instance.
        """
        validation = Validation("id")
        expected = {
            "xblock_id": "id",
            "messages": [],
            "empty": True
        }
        self.assertEqual(expected, validation.to_json())

        validation.add(ValidationMessage(ValidationMessage.ERROR, "Error message"))
        validation.add(ValidationMessage(ValidationMessage.WARNING, "Warning message"))

        expected = {
            "xblock_id": "id",
            "messages": [
                {"type": ValidationMessage.ERROR, "text": "Error message"},
                {"type": ValidationMessage.WARNING, "text": "Warning message"}
            ],
            "empty": False
        }
        self.assertEqual(expected, validation.to_json())
