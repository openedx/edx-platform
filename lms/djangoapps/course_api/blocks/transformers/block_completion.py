"""
Block Completion Transformer
"""

from xblock.completable import XBlockCompletionMode as CompletionMode
from completion.models import BlockCompletion

from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


class BlockCompletionTransformer(BlockStructureTransformer):
    """
    Keep track of the completion of each block within the block structure.
    """
    READ_VERSION = 1
    WRITE_VERSION = 1
    COMPLETION = 'completion'

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

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure adding extra field which contains block's completion.
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
            course_key=usage_info.course_key,
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
