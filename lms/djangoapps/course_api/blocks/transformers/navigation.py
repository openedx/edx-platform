"""
TODO
"""


from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer

from .block_depth import BlockDepthTransformer


class DescendantList:
    """
    Contain
    """
    def __init__(self):
        self.items = []


class BlockNavigationTransformer(BlockStructureTransformer):
    """
    Creates a table of contents for the course.

    Prerequisites: BlockDepthTransformer must be run before this in the
    transform phase.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1
    BLOCK_NAVIGATION = 'block_nav'
    BLOCK_NAVIGATION_FOR_CHILDREN = 'children_block_nav'

    def __init__(self, nav_depth):
        self.nav_depth = nav_depth

    @classmethod
    def name(cls):
        return "blocks_api:block_navigation"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        # collect basic xblock fields
        block_structure.request_xblock_fields('hide_from_toc')

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure based on the given usage_info.
        """
        if self.nav_depth is None:
            return

        for block_key in block_structure.topological_traversal():

            parents = block_structure.get_parents(block_key)
            parents_descendants_list = set()
            for parent_key in parents:
                parent_nav = block_structure.get_transformer_block_field(
                    parent_key,
                    self,
                    self.BLOCK_NAVIGATION_FOR_CHILDREN,
                )
                if parent_nav is not None:
                    parents_descendants_list |= parent_nav

            children_descendants_list = None
            if (
                    not block_structure.get_xblock_field(block_key, 'hide_from_toc', False) and (
                        not parents or
                        any(parent_desc_list is not None for parent_desc_list in parents_descendants_list)
                    )
            ):
                # add self to parent's descendants
                for parent_desc_list in parents_descendants_list:
                    if parent_desc_list is not None:
                        parent_desc_list.items.append(str(block_key))

                if BlockDepthTransformer.get_block_depth(block_structure, block_key) > self.nav_depth:
                    children_descendants_list = parents_descendants_list
                else:
                    block_nav_list = DescendantList()
                    children_descendants_list = {block_nav_list}
                    block_structure.set_transformer_block_field(
                        block_key,
                        self,
                        self.BLOCK_NAVIGATION,
                        block_nav_list.items
                    )

            block_structure.set_transformer_block_field(
                block_key,
                self,
                self.BLOCK_NAVIGATION_FOR_CHILDREN,
                children_descendants_list
            )
