"""
Validation information for an xblock instance.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import six


class ValidationMessage(object):
    """
    A message containing validation information about an xblock.
    """

    WARNING = "warning"
    ERROR = "error"

    TYPES = [WARNING, ERROR]

    def __init__(self, message_type, message_text):
        """
        Create a new message.

        Args:
            message_type (unicode): The type associated with this message. Must be included in `TYPES`.
            message_text (unicode): The textual message.
        """
        if message_type not in self.TYPES:
            raise TypeError("Unknown message_type: " + message_type)
        if not isinstance(message_text, six.text_type):
            raise TypeError("Message text must be unicode")
        self.type = message_type
        self.text = message_text

    def to_json(self):
        """
        Convert to a json-serializable representation.

        Returns:
            dict: A dict representation that is json-serializable.
        """
        return {
            "type": self.type,
            "text": self.text
        }


class Validation(object):
    """
    An object containing validation information for an xblock instance.

    An instance of this class can be used as a boolean to determine if the xblock has validation issues,
    where `True` signifies that the xblock passes validation.
    """

    def __init__(self, xblock_id):
        """
        Create a `Validation` instance.

        Args:
            xblock_id (object): An identification object that must support conversion to unicode.
        """
        self.messages = []
        self.xblock_id = xblock_id

    @property
    def empty(self):
        """
        Is this object empty (contains no messages)?

        Returns:
            bool: True iff this instance has no validation issues and therefore has no messages.
        """
        return not self.messages

    def __bool__(self):
        """
        Extended to return True if `empty` returns True

         Returns:
            bool: True iff this instance has no validation issues.
        """
        return self.empty

    __nonzero__ = __bool__

    def add(self, message):
        """
        Add a new validation message to this instance.

        Args:
            message (ValidationMessage): A validation message to add to this instance's list of messages.
        """
        if not isinstance(message, ValidationMessage):
            raise TypeError("Argument must of type ValidationMessage")
        self.messages.append(message)

    def add_messages(self, validation):
        """
        Adds all the messages in the specified `Validation` object to this instance's
        messages array.

        Args:
            validation (Validation): An object containing the messages to add to this instance's messages.
        """
        if not isinstance(validation, Validation):
            raise TypeError("Argument must be of type Validation")

        self.messages.extend(validation.messages)

    def to_json(self):
        """
        Convert to a json-serializable representation.

        Returns:
            dict: A dict representation that is json-serializable.
        """
        return {
            "xblock_id": six.text_type(self.xblock_id),
            "messages": [message.to_json() for message in self.messages],
            "empty": self.empty
        }
