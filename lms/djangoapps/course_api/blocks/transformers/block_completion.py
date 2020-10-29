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

    def mark_complete(self, course_block_completions, latest_completion_block_key, block_key, block_structure):
        """
        Helper function to mark a block as 'complete' as dictated by
        course_block_completions (for problems) or all of a block's children being complete.
        This also sets the 'resume_block' field as that is connected to the latest completed block.

        :param course_block_completions: dict[course_completion_object] =  completion_value
        :param latest_completion_block_key: block key for the latest completed block.
        :param block_key: A opaque_keys.edx.locator.BlockUsageLocator object
        :param block_structure: A BlockStructureBlockData object
        """
        if block_key in course_block_completions:
            block_structure.override_xblock_field(block_key, self.COMPLETE, True)
            if block_key == latest_completion_block_key:
                block_structure.override_xblock_field(block_key, self.RESUME_BLOCK, True)

        children = block_structure.get_children(block_key)
        non_discussion_children = (child_key for child_key in children
                                   if block_structure.get_xblock_field(child_key, 'category') != 'discussion')
        child_complete = (block_structure.get_xblock_field(child_key, self.COMPLETE)
                          for child_key in non_discussion_children)
        if children and all(child_complete):
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
        'completion': Returns a percentile (0.0 - 1.0) of correctness for a _problem_. This field will
            be None for all other blocks that are not leaves and captured in BlockCompletion.
        'complete': Returns a boolean indicating whether the block is complete. For problems, this will
            be taken from a BlockCompletion entry existing. For all other blocks, it will be marked True
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

        latest_completion = completions.latest() if completions.exists() else None
        if latest_completion:
            latest_completion_block_key = latest_completion[0]
            for block_key in block_structure.post_order_traversal():
                self.mark_complete(completions_dict, latest_completion_block_key, block_key, block_structure)
