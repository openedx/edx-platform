"""
Implementation of the APIs required for XBlock runtimes to work with
our newer Open edX-specific opaque key formats.
"""


from opaque_keys.edx.keys import UsageKeyV2
from xblock.runtime import IdReader

from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl


class OpaqueKeyReader(IdReader):
    """
    IdReader for :class:`DefinitionKey` and :class:`UsageKey`s.
    """
    def get_definition_id(self, usage_id):
        """Retrieve the definition that a usage is derived from.

        Args:
            usage_id: The id of the usage to query

        Returns:
            The `definition_id` the usage is derived from
        """
        if isinstance(usage_id, UsageKeyV2):
            return get_learning_context_impl(usage_id).definition_for_usage(usage_id)
        raise TypeError("This version of get_definition_id doesn't support the given key type.")

    def get_block_type(self, def_id):
        """Retrieve the block_type of a particular definition

        Args:
            def_id: The id of the definition to query

        Returns:
            The `block_type` of the definition
        """
        return def_id.block_type

    def get_usage_id_from_aside(self, aside_id):
        """
        Retrieve the XBlock `usage_id` associated with this aside usage id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `usage_id` of the usage the aside is commenting on.
        """
        return aside_id.usage_key

    def get_definition_id_from_aside(self, aside_id):
        """
        Retrieve the XBlock `definition_id` associated with this aside definition id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `definition_id` of the usage the aside is commenting on.
        """
        return aside_id.definition_key

    def get_aside_type_from_usage(self, aside_id):
        """
        Retrieve the XBlockAside `aside_type` associated with this aside
        usage id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `aside_type` of the aside.
        """
        return aside_id.aside_type

    def get_aside_type_from_definition(self, aside_id):
        """
        Retrieve the XBlockAside `aside_type` associated with this aside
        definition id.

        Args:
            aside_id: The definition id of the XBlockAside.

        Returns:
            The `aside_type` of the aside.
        """
        return aside_id.aside_type
