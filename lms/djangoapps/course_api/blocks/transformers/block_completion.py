"""
Block Completion Transformer
"""


from completion.models import BlockCompletion
from xblock.completable import XBlockCompletionMode as CompletionMode

from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


class BlockCompletionTransformer(BlockStructureTransformer):
    """
    Keep track of the completion of each block within the block structure.
    """
    READ_VERSION = 1
    WRITE_VERSION = 1
    COMPLETION = 'completion'
    COMPLETE = 'complete'
    RESUME_BLOCK = 'resume_block'

    @classmethod
    def name(cls):
        return "blocks_api:completion"

    @classmethod
    def get_block_completion(cls, block_structure, block_key):
        """
        Return the precalculated completion of a block within the block_structure:

        Arguments:
            block_structure: a BlockStructure instance
            block_key: the key of the block whose completion we want to know

        Returns:
            block_completion: float or None
        """
        return block_structure.get_transformer_block_field(
            block_key,
            cls,
            cls.COMPLETION,
        )

    @classmethod
    def collect(cls, block_structure):
        block_structure.request_xblock_fields('completion_mode')

    @staticmethod
    def _is_block_excluded(block_structure, block_key):
        """
        Checks whether block's completion method is of `EXCLUDED` type.
        """
        completion_mode = block_structure.get_xblock_field(
            block_key, 'completion_mode'
        )

        return completion_mode == CompletionMode.EXCLUDED

    def mark_complete(self, complete_course_blocks, latest_complete_block_key, block_key, block_structure):
        """
        Helper function to mark a block as 'complete' as dictated by
        complete_course_blocks (for problems) or all of a block's children being complete.
        This also sets the 'resume_block' field as that is connected to the latest completed block.

        :param complete_course_blocks: container of complete block keys
        :param latest_complete_block_key: block key for the latest completed block.
        :param block_key: A opaque_keys.edx.locator.BlockUsageLocator object
        :param block_structure: A BlockStructureBlockData object
        """
        if block_key in complete_course_blocks:
            block_structure.override_xblock_field(block_key, self.COMPLETE, True)
            if str(block_key) == str(latest_complete_block_key):
                block_structure.override_xblock_field(block_key, self.RESUME_BLOCK, True)
        elif block_structure.get_xblock_field(block_key, 'completion_mode') == CompletionMode.AGGREGATOR:
            children = block_structure.get_children(block_key)
            all_children_complete = all(block_structure.get_xblock_field(child_key, self.COMPLETE)
                                        for child_key in children
                                        if not self._is_block_excluded(block_structure, child_key))

            if all_children_complete:
                block_structure.override_xblock_field(block_key, self.COMPLETE, True)

