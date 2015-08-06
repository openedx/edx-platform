"""
...
"""
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class VisibilityTransformer(BlockStructureTransformer):
    """
    ...
    """
    VERSION = 1

    @classmethod
    def collect(self, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        block_structure.request_xblock_fields('visible_to_staff_only')

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.
        """
        if user_info.has_staff_access:
            return

        block_structure.remove_block_if(
            lambda block_key: block_structure.get_xblock_field(block_key, 'visible_to_staff_only')
        )
