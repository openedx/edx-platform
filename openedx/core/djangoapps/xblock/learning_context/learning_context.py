"""
A "Learning Context" is a course, a library, a program, or some other collection
of content where learning happens.
"""


class LearningContext:
    """
    Abstract base class for learning context implementations.

    A "Learning Context" is a course, a library, a program,
    or some other collection of content where learning happens.

    Additional learning contexts can be implemented as plugins, by subclassing
    this class and registering in the 'openedx.learning_context' entry point.
    """

    def __init__(self, **kwargs):
        """
        Initialize this learning context.

        Subclasses should pass **kwargs to this constructor to allow for future
        parameters without changing the API.
        """

    def can_edit_block(self, user, usage_key):  # pylint: disable=unused-argument
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to edit it (make changes to the authored
        data store)?

        user: a Django User object (may be an AnonymousUser)

        usage_key: the UsageKeyV2 subclass used for this learning context

        Must return a boolean.
        """
        return False

    def can_view_block(self, user, usage_key):  # pylint: disable=unused-argument
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to view it and interact with it (call
        handlers, save user state, etc.)?

        user: a Django User object (may be an AnonymousUser)

        usage_key: the UsageKeyV2 subclass used for this learning context

        Must return a boolean.
        """
        return False

    def definition_for_usage(self, usage_key, **kwargs):
        """
        Given a usage key in this context, return the key indicating the actual XBlock definition.

        Retuns None if the usage key doesn't exist in this context.
        """
        raise NotImplementedError

    def send_block_updated_event(self, usage_key):
        """
        Send a "block updated" event for the block with the given usage_key in this context.

        usage_key: the UsageKeyV2 subclass used for this learning context
        """
