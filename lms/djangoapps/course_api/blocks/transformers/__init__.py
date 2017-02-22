"""
Course API Block Transformers
"""

from lms.djangoapps.course_blocks.transformers.visibility import VisibilityTransformer
from .student_view import StudentViewTransformer
from .block_counts import BlockCountsTransformer
from .navigation import BlockNavigationTransformer


class SupportedFieldType(object):
    """
    Metadata about fields supported by different transformers
    """
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


# A list of metadata for additional requested fields to be used by the
# BlockSerializer` class.  Each entry provides information on how that field can
# be requested (`requested_field_name`), can be found (`transformer` and
# `block_field_name`), and should be serialized (`serializer_field_name` and
# `default_value`).

SUPPORTED_FIELDS = [
    SupportedFieldType('category', requested_field_name='type'),
    SupportedFieldType('display_name', default_value=''),
    SupportedFieldType('graded'),
    SupportedFieldType('format'),
    SupportedFieldType('due'),
    # 'student_view_data'
    SupportedFieldType(StudentViewTransformer.STUDENT_VIEW_DATA, StudentViewTransformer),
    # 'student_view_multi_device'
    SupportedFieldType(StudentViewTransformer.STUDENT_VIEW_MULTI_DEVICE, StudentViewTransformer),

    # set the block_field_name to None so the entire data for the transformer is serialized
    SupportedFieldType(None, BlockCountsTransformer, BlockCountsTransformer.BLOCK_COUNTS),

    SupportedFieldType(
        BlockNavigationTransformer.BLOCK_NAVIGATION,
        BlockNavigationTransformer,
        requested_field_name='nav_depth',
        serializer_field_name='descendants',
    ),

    # Provide the staff visibility info stored when VisibilityTransformer ran previously
    SupportedFieldType(
        'merged_visible_to_staff_only',
        VisibilityTransformer,
        requested_field_name='visible_to_staff_only',
    )
]
