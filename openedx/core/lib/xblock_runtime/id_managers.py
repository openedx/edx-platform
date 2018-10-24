from xblock.runtime import IdReader, IdGenerator
from opaque_keys.edx.locator import BlockUsageLocator
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
        if isinstance(usage_id, BlockUsageLocator):
            # This is a key to a block in split mongo.
            # TODO: is there something more efficient than this mess that can get us the definition key?
            split_modulestore = modulestore().default_modulestore
            course_entry = split_modulestore._lookup_course(usage_id.course_key.for_branch(ModuleStoreEnum.BranchName.published))
            return split_modulestore.create_runtime(course_entry, lazy=True).id_reader.get_definition_id(usage_id)

        # Newer key types should encode their own definition ID:
        return usage_id.definition_key

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
