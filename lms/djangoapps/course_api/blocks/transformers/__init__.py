"""
Course API Block Transformers
"""

from student_view import StudentViewTransformer
from block_counts import BlockCountsTransformer
from navigation import BlockNavigationTransformer


class SupportedFieldType(object):
    def __init__(
            self,
            block_field_name,
            transformer=None,
            requested_field_name=None,
            serializer_field_name=None,
            default_value=None
    ):
        self.transformer = transformer
        self.block_field_name = block_field_name
        self.requested_field_name = requested_field_name or block_field_name
        self.serializer_field_name = serializer_field_name or self.requested_field_name
        self.default_value = default_value


SUPPORTED_FIELDS = (
    SupportedFieldType('category', None, 'type'),
    SupportedFieldType('display_name', default_value=''),
    SupportedFieldType('graded'),
    SupportedFieldType('format'),

    SupportedFieldType(StudentViewTransformer.STUDENT_VIEW_DATA, StudentViewTransformer),
    SupportedFieldType(StudentViewTransformer.STUDENT_VIEW_MULTI_DEVICE, StudentViewTransformer),

    # set the block_field_name to None so the entire data for the transformer is serialized
    SupportedFieldType(None, BlockCountsTransformer, BlockCountsTransformer.BLOCK_COUNTS),

    SupportedFieldType(
        BlockNavigationTransformer.BLOCK_NAVIGATION,
        BlockNavigationTransformer,
        requested_field_name='nav_depth',
        serializer_field_name='descendants',
    )
)
