"""
Extension of XBlock Validation class to include information for presentation in Studio.
"""
from xblock.validation import Validation, ValidationMessage


class StudioValidationMessage(ValidationMessage):
    """
    A message containing validation information about an xblock, extended to provide Studio-specific fields.
    """

    # A special message type indicating that the xblock is not yet configured. This message may be rendered
    # in a different way within Studio.
    NOT_CONFIGURED = "not-configured"

    TYPES = [ValidationMessage.WARNING, ValidationMessage.ERROR, NOT_CONFIGURED]

    def __init__(self, message_type, message_text, action_label=None, action_class=None, action_runtime_event=None,
                 action_link=None):
        """
        Create a new message.

        Args:
            message_type (str): The type associated with this message. Must be `WARNING` or `ERROR`.
            message_text (unicode): The textual message.
            action_label (unicode): Text to show on a "fix-up" action (optional). If present, either `action_class`
                or `action_runtime_event` should be specified.
            action_class (str): A class to link to the "fix-up" action (optional). A click handler must be added
                for this class, unless it is "edit-button", "duplicate-button", or "delete-button" (which are all
                handled in general for xblock instances.
            action_runtime_event (str): An event name to be triggered on the xblock client-side runtime when
                the "fix-up" action is clicked (optional).
        """
        super(StudioValidationMessage, self).__init__(message_type, message_text)
        if action_label is not None:
            if not isinstance(action_label, unicode):
                raise TypeError("Action label must be unicode.")
            self.action_label = action_label
        if action_class is not None:
            if not isinstance(action_class, basestring):
                raise TypeError("Action class must be a string.")
            self.action_class = action_class
        if action_runtime_event is not None:
            if not isinstance(action_runtime_event, basestring):
                raise TypeError("Action runtime event must be a string.")
            self.action_runtime_event = action_runtime_event
        if action_link is not None:
            if not isinstance(action_link, basestring):
                raise TypeError("Action link must be a string.")
            self.action_link = action_link

    def to_json(self):
        """
        Convert to a json-serializable representation.

        Returns:
            dict: A dict representation that is json-serializable.
        """
        serialized = super(StudioValidationMessage, self).to_json()
        if hasattr(self, "action_label"):
            serialized["action_label"] = self.action_label
        if hasattr(self, "action_class"):
            serialized["action_class"] = self.action_class
        if hasattr(self, "action_runtime_event"):
            serialized["action_runtime_event"] = self.action_runtime_event
        if hasattr(self, "action_link"):
            serialized["action_link"] = self.action_link
        return serialized


class StudioValidation(Validation):
    """
    Extends `Validation` to add Studio-specific summary message.
    """

    @classmethod
    def copy(cls, validation):
        """
        Copies the `Validation` object to a `StudioValidation` object. This is a shallow copy.

        Args:
            validation (Validation): A `Validation` object to be converted to a `StudioValidation` instance.

        Returns:
            StudioValidation: A `StudioValidation` instance populated with the messages from supplied
                `Validation` object
        """
        if not isinstance(validation, Validation):
            raise TypeError("Copy must be called with a Validation instance")
        studio_validation = cls(validation.xblock_id)
        studio_validation.messages = validation.messages
        return studio_validation

    def __init__(self, xblock_id):
        """
        Create a `StudioValidation` instance.

        Args:
            xblock_id (object): An identification object that must support conversion to unicode.
        """
        super(StudioValidation, self).__init__(xblock_id)
        self.summary = None

    def set_summary(self, message):
        """
        Sets a summary message on this instance. The summary is optional.

        Args:
            message (ValidationMessage): A validation message to set as this instance's summary.
        """
        if not isinstance(message, ValidationMessage):
            raise TypeError("Argument must of type ValidationMessage")
        self.summary = message

    @property
    def empty(self):
        """
        Is this object empty (contains no messages and no summary)?

        Returns:
            bool: True iff this instance has no validation issues and therefore has no messages or summary.
        """
        return super(StudioValidation, self).empty and not self.summary

    def to_json(self):
        """
        Convert to a json-serializable representation.

        Returns:
            dict: A dict representation that is json-serializable.
        """
        serialized = super(StudioValidation, self).to_json()
        if self.summary:
            serialized["summary"] = self.summary.to_json()
        return serialized
