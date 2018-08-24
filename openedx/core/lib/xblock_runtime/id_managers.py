from xblock.runtime import IdReader, IdGenerator
from opaque_keys.edx.asides import AsideUsageKeyV2, AsideDefinitionKeyV2

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


# TODO: this code was copied from x_module.py and modified. Remove it from
# x_module.py ?


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
        # TODO: if this is a usage v2, then extract the definition from the key
        # else:

        # TODO: there has got to be a better way:
        split_modulestore = modulestore().default_modulestore
        course_entry = split_modulestore._lookup_course(usage_id.course_key.for_branch(ModuleStoreEnum.BranchName.published))
        return split_modulestore.create_runtime(course_entry, lazy=True).id_reader.get_definition_id(usage_id)

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


class AsideKeyGenerator(IdGenerator):
    """
    An :class:`.IdGenerator` that only provides facilities for constructing new XBlockAsides.
    """
    def create_aside(self, definition_id, usage_id, aside_type):
        """
        Make a new aside definition and usage ids, indicating an :class:`.XBlockAside` of type `aside_type`
        commenting on an :class:`.XBlock` usage `usage_id`

        Returns:
            (aside_definition_id, aside_usage_id)
        """
        def_key = AsideDefinitionKeyV2(definition_id, aside_type)
        usage_key = AsideUsageKeyV2(usage_id, aside_type)
        return (def_key, usage_key)

    def create_usage(self, def_id):
        """Make a usage, storing its definition id.

        Returns the newly-created usage id.
        """
        raise NotImplementedError("Open edX does not support create_usage")

    def create_definition(self, block_type, slug=None):
        """Make a definition, storing its block type.

        If `slug` is provided, it is a suggestion that the definition id
        incorporate the slug somehow.

        Returns the newly-created definition id.

        """
        raise NotImplementedError("Open edX does not support create_definition")
