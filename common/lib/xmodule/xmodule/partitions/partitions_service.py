"""
This is a service-like API that assigns tracks which groups users are in for various
user partitions.  It uses the user_service key/value store provided by the LMS runtime to
persist the assignments.
"""
from abc import ABCMeta, abstractproperty


class PartitionService(object):
    """
    This is an XBlock service that assigns tracks which groups users are in for various
    user partitions.  It uses the provided user_tags service object to
    persist the assignments.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def course_partitions(self):
        """
        Return the set of partitions assigned to self._course_id
        """
        raise NotImplementedError('Subclasses must implement course_partition')

    def __init__(self, user, course_id, track_function=None, cache=None):
        self._user = user
        self._course_id = course_id
        self._track_function = track_function
        self._cache = cache

    def get_user_group_id_for_partition(self, user_partition_id):
        """
        If the user is already assigned to a group in user_partition_id, return the
        group_id.

        If not, assign them to one of the groups, persist that decision, and
        return the group_id.

        If the group they are assigned to doesn't exist anymore, re-assign to one of
        the existing groups and return its id.

        Args:
            user_partition_id -- an id of a partition that's hopefully in the
                runtime.user_partitions list.

        Returns:
            The id of one of the groups in the specified user_partition_id (as a string).

        Raises:
            ValueError if the user_partition_id isn't found.
        """
        cache_key = "PartitionService.ugidfp.{}.{}.{}".format(
            self._user.id, self._course_id, user_partition_id
        )

        if self._cache and (cache_key in self._cache):
            return self._cache[cache_key]

        user_partition = self._get_user_partition(user_partition_id)
        if user_partition is None:
            raise ValueError(
                "Configuration problem!  No user_partition with id {0} "
                "in course {1}".format(user_partition_id, self._course_id)
            )

        group = self.get_group(user_partition)
        group_id = group.id if group else None

        if self._cache is not None:
            self._cache[cache_key] = group_id

        return group_id

    def _get_user_partition(self, user_partition_id):
        """
        Look for a user partition with a matching id in the course's partitions.

        Returns:
            A UserPartition, or None if not found.
        """
        for partition in self.course_partitions:
            if partition.id == user_partition_id:
                return partition

        return None

    def get_group(self, user_partition, assign=True):
        """
        Returns the group from the specified user partition to which the user is assigned.
        If the user has not yet been assigned, a group will be chosen for them based upon
        the partition's scheme.
        """
        return user_partition.scheme.get_group_for_user(
            self._course_id, self._user, user_partition, assign=assign, track_function=self._track_function
        )
