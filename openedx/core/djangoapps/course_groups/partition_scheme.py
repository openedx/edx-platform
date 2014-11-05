"""
Provides a UserPartition driver for cohorts.
"""
import logging

from .cohorts import get_cohort, get_partition_group_id_for_cohort

log = logging.getLogger(__name__)


class CohortPartitionScheme(object):
    """
    This scheme uses lms cohorts (CourseUserGroups) and cohort-partition
    mappings (CourseUserGroupPartitionGroup) to map lms users into Partition
    Groups.
    """

    @classmethod
    def get_group_for_user(cls, course_id, user, user_partition, track_function=None):
        """
        Returns the Group from the specified user partition to which the user
        is assigned, via their cohort membership and any mappings from cohorts
        to partitions / groups that might exist.

        If the user has not yet been assigned to a cohort, an assignment *might*
        be created on-the-fly, as determined by the course's cohort config.
        Any such side-effects will be triggered inside the call to
        cohorts.get_cohort().

        If the user has no cohort mapping, or there is no (valid) cohort ->
        partition group mapping found, the function returns None.
        """
        cohort = get_cohort(user, course_id)
        if cohort is None:
            # student doesn't have a cohort
            return None

        partition_id, group_id = get_partition_group_id_for_cohort(cohort)
        if partition_id is None:
            # cohort isn't mapped to any partition group.
            return None

        if partition_id != user_partition.id:
            # if we have a match but the partition doesn't match the requested
            # one it means the mapping is invalid.  the previous state of the
            # partition configuration may have been modified.
            log.warn(
                "partition mismatch in CohortPartitionScheme: %r",
                {
                    "requested_partition_id": user_partition.id,
                    "found_partition_id": partition_id,
                    "found_group_id": group_id,
                    "cohort_id": cohort.id,
                }
            )
            # fail silently
            return None

        group = user_partition.get_group(group_id)
        if group is None:
            # if we have a match but the group doesn't exist in the partition,
            # it means the mapping is invalid.  the previous state of the
            # partition configuration may have been modified.
            log.warn(
                "group not found in CohortPartitionScheme: %r",
                {
                    "requested_partition_id": user_partition.id,
                    "requested_group_id": group_id,
                    "cohort_id": cohort.id,
                }
            )
            # fail silently
            return None

        return group
