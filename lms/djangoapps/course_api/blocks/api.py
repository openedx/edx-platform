"""
API function for retrieving course blocks data
"""


import lms.djangoapps.course_blocks.api as course_blocks_api
from lms.djangoapps.course_blocks.transformers.access_denied_filter import AccessDeniedMessageFilterTransformer
from lms.djangoapps.course_blocks.transformers.hidden_content import HiddenContentTransformer
from lms.djangoapps.course_blocks.transformers.hide_empty import HideEmptyTransformer
from openedx.core.djangoapps.content.block_structure.transformers import BlockStructureTransformers
from openedx.core.lib.mobile_utils import is_request_from_mobile_app

from .serializers import BlockDictSerializer, BlockSerializer
from .toggles import HIDE_ACCESS_DENIALS_FLAG
from .transformers.block_completion import BlockCompletionTransformer
from .transformers.blocks_api import BlocksAPITransformer
from .transformers.milestones import MilestonesAndSpecialExamsTransformer


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
        hide_access_denials=False,
        allow_start_dates_in_future=False,
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
        hide_access_denials (bool): When True, filter out any blocks that were
            denied access to the user, even if they have access denial messages
            attached.
        allow_start_dates_in_future (bool): When True, will allow blocks to be
            returned that can bypass the StartDateTransformer's filter to show
            blocks with start dates in the future.
    """

    if HIDE_ACCESS_DENIALS_FLAG.is_enabled():
        hide_access_denials = True

    # create ordered list of transformers, adding BlocksAPITransformer at end.
    transformers = BlockStructureTransformers()
    if requested_fields is None:
        requested_fields = []
    include_completion = 'completion' in requested_fields
    include_special_exams = 'special_exam_info' in requested_fields
    include_gated_sections = 'show_gated_sections' in requested_fields

    if user is not None:
        transformers += course_blocks_api.get_course_block_access_transformers(user)
        transformers += [
            MilestonesAndSpecialExamsTransformer(
                include_special_exams=include_special_exams,
                include_gated_sections=include_gated_sections
            ),
            HiddenContentTransformer()
        ]

    if hide_access_denials:
        transformers += [AccessDeniedMessageFilterTransformer()]

    # TODO: Remove this after REVE-52 lands and old-mobile-app traffic falls to < 5% of mobile traffic
    if is_request_from_mobile_app(request):
        transformers += [HideEmptyTransformer()]

    transformers += [
        BlocksAPITransformer(
            block_counts,
            student_view_data,
            depth,
            nav_depth
        )
    ]

    if include_completion:
        transformers += [BlockCompletionTransformer()]

    # transform
    blocks = course_blocks_api.get_course_blocks(
        user, usage_key, transformers, allow_start_dates_in_future=allow_start_dates_in_future)

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
