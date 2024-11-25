"""
A "Learning Context" is a course, a library, a program, or some other collection
of content where learning happens.
"""
<<<<<<< HEAD
=======
from openedx.core.types import User as UserType
from opaque_keys.edx.keys import UsageKeyV2
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


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

<<<<<<< HEAD
    def can_edit_block(self, user, usage_key):  # pylint: disable=unused-argument
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to edit it (make changes to the authored
        data store)?
=======
    def can_edit_block(self, user: UserType, usage_key: UsageKeyV2) -> bool:  # pylint: disable=unused-argument
        """
        Assuming a block with the specified ID (usage_key) exists, does the
        specified user have permission to edit it (make changes to the
        fields / authored data store)?
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        user: a Django User object (may be an AnonymousUser)

        usage_key: the UsageKeyV2 subclass used for this learning context

        Must return a boolean.
        """
        return False

<<<<<<< HEAD
    def can_view_block(self, user, usage_key):  # pylint: disable=unused-argument
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to view it and interact with it (call
        handlers, save user state, etc.)?
=======
    def can_view_block_for_editing(self, user: UserType, usage_key: UsageKeyV2) -> bool:
        """
        Assuming a block with the specified ID (usage_key) exists, does the
        specified user have permission to view its fields and OLX details (but
        not necessarily to make changes to it)?
        """
        return self.can_edit_block(user, usage_key)

    def can_view_block(self, user: UserType, usage_key: UsageKeyV2) -> bool:  # pylint: disable=unused-argument
        """
        Assuming a block with the specified ID (usage_key) exists, does the
        specified user have permission to view it and interact with it (call
        handlers, save user state, etc.)? This is also sometimes called the
        "can_learn" permission.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        user: a Django User object (may be an AnonymousUser)

        usage_key: the UsageKeyV2 subclass used for this learning context

        Must return a boolean.
        """
        return False

    def definition_for_usage(self, usage_key, **kwargs):
        """
<<<<<<< HEAD
        Given a usage key for an XBlock in this context, return the
        BundleDefinitionLocator which specifies the actual XBlock definition
        (as a path to an OLX in a specific blockstore bundle).

        usage_key: the UsageKeyV2 subclass used for this learning context

        kwargs: optional additional parameters unique to the learning context

        Must return a BundleDefinitionLocator if the XBlock exists in this
        context, or None otherwise.
        """
        raise NotImplementedError
=======
        Given a usage key in this context, return the key indicating the actual XBlock definition.

        Retuns None if the usage key doesn't exist in this context.
        """
        raise NotImplementedError

    def send_block_updated_event(self, usage_key):
        """
        Send a "block updated" event for the block with the given usage_key in this context.

        usage_key: the UsageKeyV2 subclass used for this learning context
        """
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
