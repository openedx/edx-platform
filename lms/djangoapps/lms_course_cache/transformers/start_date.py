"""
...
"""
from courseware.access import _has_access_to_course
from openedx.core.lib.block_cache.transformer import BlockStructureTransformer


class StartDateTransformer(BlockStructureTransformer):
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
        block_structure.request_xblock_fields('start', 'days_early_for_beta')

    def transform(self, user_info, block_structure):
        """
        Mutates block_structure and block_data based on the given user_info.
        """
        pass  # TODO 8874: Write StartDateTransformation.
