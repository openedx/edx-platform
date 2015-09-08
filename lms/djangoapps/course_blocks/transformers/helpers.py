"""
Transformers helpers functions.
"""
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
# TODO 8874: Make it so we support all schemes instead of manually declaring them here.
INCLUDE_SCHEMES = [CohortPartitionScheme, RandomUserPartitionScheme, ]
SCHEME_SUPPORTS_ASSIGNMENT = [RandomUserPartitionScheme, ]


def get_user_partition_groups(course_key, user_partitions, user):
    """
    Collect group ID for each partition in this course for this user.

    Arguments:
        course_key (CourseKey)
        user_partitions (list[UserPartition])
        user (User)

    Returns:
        dict[int: Group]: Mapping from user partitions to the group to which
            the user belongs in each partition. If the user isn't in a group
            for a particular partition, then that partition's ID will not be
            in the dict.
    """
    partition_groups = {}
    for partition in user_partitions:
        if partition.scheme not in INCLUDE_SCHEMES:
            continue
        group = partition.scheme.get_group_for_user(
            course_key,
            user,
            partition,
            **({'assign': False} if partition.scheme in SCHEME_SUPPORTS_ASSIGNMENT else {})
        )
        if group is not None:
            partition_groups[partition.id] = group
    return partition_groups
