"""
...
"""
from .block_cache_operations import (
    get_cached_block_structure,
    get_cached_block_data_dict,
    create_block_structure,
    create_block_data_dict,
    cache_block_structure,
    cache_block_data_dict,
    filter_block_data_dict,
    get_user_course_info,
)


def get_course_blocks(user, course_key, root_block_key, transformations):
    """
    Arguments:
        user (User)
        course_key (CourseKey): Course to which desired blocks belong.
        root_block_key (UsageKey): Usage key for root block in the subtree
            for which block information will be returned. Passing in the usage
            key of a course will return the entire user-specific course
            hierarchy.
        transformations (list[Transformation])

    Returns:
        (CourseBlockStructure, dict[UsageKey: CourseBlockData])
    """
    # Load the cached course structure.
    full_block_structure = get_cached_block_structure(course_key)

    # If the structure is in the cache, then extract the requested sub-structure
    # and load the necessary block data.
    if full_block_structure:
        block_structure = full_block_structure.get_sub_structure(root_block_key)
        block_data_dict = get_cached_block_data_dict(full_block_structure.get_block_keys())

    # Else:
    # (1) Load the entire course and extract its structure.
    # (2) Load block data for the entire course structure.
    # (3) Cache this information.
    # (4) Extract the requested sub-structure.
    # (5) Load the necessary block data.
    else:
        full_block_structure, xblock_dict = create_block_structure(course_key)
        full_block_data_dict = create_block_data_dict(full_block_structure, xblock_dict, ALL_COURSE_TRANSFORMATIONS)
        cache_block_structure(course_key, full_block_structure)
        cache_block_data_dict(full_block_structure)
        block_structure = full_block_structure.get_sub_structure(root_block_key)
        block_data_dict = filter_block_data_dict(full_block_data_dict, block_structure)

    # Load user data and apply transformations to course structure and data.
    user_info = get_user_course_info(user, course_key)
    for transformation in transformations:
        transformation.apply(user_info, block_structure, block_data_dict)

    # Filter out blocks that were removed during transformation application.
    return filter_block_data_dict(block_data_dict, block_structure)


del (
    get_cached_block_structure,
    get_cached_block_data_dict,
    create_block_structure,
    create_block_data_dict,
    cache_block_structure,
    cache_block_data_dict,
    filter_block_data_dict,
    get_user_course_info,
)
