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

            if any(block_structure.get_xblock_field(child_key, self.RESUME_BLOCK) for child_key in children):
                block_structure.override_xblock_field(block_key, self.RESUME_BLOCK, True)

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure adding three extra fields which contains block's completion,
        complete status, and if the block is a resume_block, indicating it is the most recently
        completed block.

        IMPORTANT!: There is a subtle, but important difference between 'completion' and 'complete'
        which are both set in this transformer:
        'completion': Returns a percentile (0.0 - 1.0) of completion for a _problem_. This field will
            be None for all other blocks that are not leaves and captured in BlockCompletion.
        'complete': Returns a boolean indicating whether the block is complete. For problems, this will
            be taken from a BlockCompletion 1.0 entry existing. For all other blocks, it will be marked True
            if all of the children of the block are all marked complete (this is calculated recursively)
        """
        def _is_block_an_aggregator_or_excluded(block_key):
            """
            Checks whether block's completion method
            is of `AGGREGATOR` or `EXCLUDED` type.
            """
            completion_mode = block_structure.get_xblock_field(
                block_key, 'completion_mode'
            )

            return completion_mode in (CompletionMode.AGGREGATOR, CompletionMode.EXCLUDED)

        completions = BlockCompletion.objects.filter(
            user=usage_info.user,
            context_key=usage_info.course_key,
        ).values_list(
            'block_key',
            'completion',
        )

        completions_dict = {
            block.map_into_course(usage_info.course_key): completion
            for block, completion in completions
        }

        for block_key in block_structure.topological_traversal():
            if _is_block_an_aggregator_or_excluded(block_key):
                completion_value = None
            elif block_key in completions_dict:
                completion_value = completions_dict[block_key]
            else:
                completion_value = 0.0

            block_structure.set_transformer_block_field(
                block_key, self, self.COMPLETION, completion_value
            )

        complete_blocks = completions.filter(completion=1.0)
        latest_complete_key = complete_blocks.latest()[0] if complete_blocks else None
        if latest_complete_key:
            complete_keys = {key for key, completion in completions_dict.items() if completion == 1.0}
            for block_key in block_structure.post_order_traversal():
                self.mark_complete(complete_keys, latest_complete_key, block_key, block_structure)
