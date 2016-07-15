"""
API function for retrieving course blocks data
"""

from lms.djangoapps.course_blocks.api import get_course_blocks, COURSE_BLOCK_ACCESS_TRANSFORMERS
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.lib.block_structure.transformers import BlockStructureTransformers

from .transformers.blocks_api import BlocksAPITransformer
from .transformers.proctored_exam import ProctoredExamTransformer
from .serializers import BlockSerializer, BlockDictSerializer


def get_blocks(
        request,
        usage_key,
        user=None,
        depth=None,
        nav_depth=None,
        requested_fields=None,
        block_counts=None,
        student_view_data=None,
        return_type='dict',
        block_types_filter=None,
):
    """
    Return a serialized representation of the course blocks.

    Arguments:
        request (HTTPRequest): Used for calling django reverse.
        usage_key (UsageKey): Identifies the starting block of interest.
        user (User): Optional user object for whom the blocks are being
            retrieved. If None, blocks are returned regardless of access checks.
        depth (integer or None): Identifies the depth of the tree to return
            starting at the root block.  If None, the entire tree starting at
            the root is returned.
        nav_depth (integer): Optional parameter that indicates how far deep to
            traverse into the block hierarchy before bundling all the
            descendants for navigation.
        requested_fields (list): Optional list of names of additional fields
            to return for each block.  Supported fields are listed in
            transformers.SUPPORTED_FIELDS.
        block_counts (list): Optional list of names of block types for which to
            return an aggregate count of blocks.
        student_view_data (list): Optional list of names of block types for
            which blocks to return their student_view_data.
        return_type (string): Possible values are 'dict' or 'list'. Indicates
            the format for returning the blocks.
        block_types_filter (list): Optional list of block type names used to filter
            the final result of returned blocks.
    """
    # create ordered list of transformers, adding BlocksAPITransformer at end.
    transformers = BlockStructureTransformers()
    if user is not None:
        transformers += COURSE_BLOCK_ACCESS_TRANSFORMERS + [ProctoredExamTransformer()]
    transformers += [
        BlocksAPITransformer(
            block_counts,
            student_view_data,
            depth,
            nav_depth
        )
    ]

    # transform
    try:
        blocks = get_course_blocks(user, usage_key, transformers)
    except KeyError:
        # If KeyError raises trying to exchange usage_key between mongo and split modulestores may fix the error.
        if usage_key.deprecated: # old_mongo usage_key changing this to split usage_key.
            new_usage_key_string = "block-v1:" + usage_key._to_string()
        else: # split usage_key change this to old_mongo usage_key.
            new_usage_key_string = usage_key._to_deprecated_string()
        usage_key = BlockUsageLocator.from_string(new_usage_key_string).replace(org=usage_key.org,
                                                                                run=usage_key.run,
                                                                                course=usage_key.course)
        blocks = get_course_blocks(user, usage_key, transformers)

    # filter blocks by types
    if block_types_filter:
        block_keys_to_remove = []
        for block_key in blocks:
            block_type = blocks.get_xblock_field(block_key, 'category')
            if block_type not in block_types_filter:
                block_keys_to_remove.append(block_key)
        for block_key in block_keys_to_remove:
            blocks.remove_block(block_key, keep_descendants=True)

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
