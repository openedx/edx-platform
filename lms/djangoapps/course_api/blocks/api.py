"""
API function for retrieving course blocks data
"""

from .transformers.blocks_api import BlocksAPITransformer
from .transformers.proctored_exam import ProctoredExamTransformer
from .serializers import BlockSerializer, BlockDictSerializer
from lms.djangoapps.course_blocks.api import get_course_blocks, COURSE_BLOCK_ACCESS_TRANSFORMERS


def get_blocks(
        request,
        usage_key,
        user=None,
        depth=None,
        nav_depth=None,
        requested_fields=None,
        block_counts=None,
        student_view_data=None,
        return_type='dict'
):
    """
    Return a serialized representation of the course blocks
    """
    # TODO support user=None by returning all blocks, not just user-specific ones
    if user is None:
        raise NotImplementedError

    # transform blocks
    blocks_api_transformer = BlocksAPITransformer(
        block_counts,
        student_view_data,
        depth,
        nav_depth
    )
    blocks = get_course_blocks(
        user,
        usage_key,
        transformers=COURSE_BLOCK_ACCESS_TRANSFORMERS + [ProctoredExamTransformer(), blocks_api_transformer],
    )

    # serialize
    serializer_context = {
        'request': request,
        'block_structure': blocks,
        'requested_fields': requested_fields or [],
    }

    if return_type == 'dict':
        serializer = BlockDictSerializer(blocks, context=serializer_context, many=False)
    else:
        serializer = BlockSerializer(blocks, context=serializer_context, many=True)

    # return serialized data
    return serializer.data
