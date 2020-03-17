"""
A "Learning Context" is a course, a library, a program, or some other collection
of content where learning happens.
"""


class LearningContext(object):
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
        Given a usage key for an XBlock in this context, return the
        BundleDefinitionLocator which specifies the actual XBlock definition
        (as a path to an OLX in a specific blockstore bundle).

        usage_key: the UsageKeyV2 subclass used for this learning context

        kwargs: optional additional parameters unique to the learning context

        Must return a BundleDefinitionLocator if the XBlock exists in this
        context, or None otherwise.
        """
        raise NotImplementedError

    def usage_for_child_include(self, parent_usage, parent_definition, parsed_include):
        """
        Method that the runtime uses when loading a block's child, to get the
        ID of the child. Must return a usage key.

        The child is always from an <xblock-include /> element.

        parent_usage: the UsageKeyV2 subclass key of the parent

        parent_definition: the BundleDefinitionLocator key of the parent (same
            as returned by definition_for_usage(parent_usage) but included here
            as an optimization since it's already known.)

        parsed_include: the XBlockInclude tuple containing the data from the
            parsed <xblock-include /> element. See xblock.runtime.olx_parsing.

        Must return a UsageKeyV2 subclass
        """
        raise NotImplementedError

    # Future functionality:
    # def get_field_overrides(self, user, usage_key):
    #     """
    #     Each learning context may have a way for authors to specify field
    #     overrides that apply to XBlocks in the context.

    #     For example, courses might allow an instructor to specify that all
    #     'problem' blocks in her course have 'num_attempts' set to '5',
    #     regardless of the 'num_attempts' value in the underlying problem XBlock
    #     definitions.
    #     """
    #     raise NotImplementedError
