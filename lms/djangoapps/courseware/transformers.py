"""
Courseware BlockTransformer implementations
"""

from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin,
)


class OpenAssessmentDateTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    BlockTransformer to collect all fields related to dates for openassessment problems.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return 'open_assessment_transformer'

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        block_structure.request_xblock_fields(
            'valid_assessments',
            'submission_start',
            'submission_due',
            'title',
            'graded',
            'format',
            'has_score',
        )

    def transform_block_filters(self, usage_info, block_structure):
        # This Transformer exists only to collect fields needed by other code, so it
        # doesn't transform the tree.
        return block_structure.create_universal_filter()
