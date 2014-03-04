"""
This is a service-like API that assigns tracks which groups users are in for various
user partitions.  It uses the user_service key/value store provided by the LMS runtime to
persist the assignments.
"""
import random
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

    def __init__(self, user_tags_service, course_id, track_function):
        self.random = random.Random()
        self._user_tags_service = user_tags_service
        self._course_id = course_id
        self._track_function = track_function

    def get_user_group_for_partition(self, user_partition_id):
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
        user_partition = self._get_user_partition(user_partition_id)
        if user_partition is None:
            raise ValueError(
                "Configuration problem!  No user_partition with id {0} "
                "in course {1}".format(user_partition_id, self._course_id)
            )

        group_id = self._get_group(user_partition)

        return group_id

    def _get_user_partition(self, user_partition_id):
        """
        Look for a user partition with a matching id in
        in the course's partitions.

        Returns:
            A UserPartition, or None if not found.
        """
        for partition in self.course_partitions:
            if partition.id == user_partition_id:
                return partition

        return None

    def _key_for_partition(self, user_partition):
        """
        Returns the key to use to look up and save the user's group for a particular
        condition.  Always use this function rather than constructing the key directly.
        """
        return 'xblock.partition_service.partition_{0}'.format(user_partition.id)

    def _get_group(self, user_partition):
        """
        Return the group of the current user in user_partition.  If they don't already have
        one assigned, pick one and save it.  Uses the runtime's user_service service to look up
        and persist the info.
        """
        key = self._key_for_partition(user_partition)
        scope = self._user_tags_service.COURSE

        group_id = self._user_tags_service.get_tag(scope, key)
        if group_id is not None:
            group_id = int(group_id)

        partition_group_ids = [group.id for group in user_partition.groups]

        # If a valid group id has been saved already, return it
        if group_id is not None and group_id in partition_group_ids:
            return group_id

        # TODO: what's the atomicity of the get above and the save here?  If it's not in a
        # single transaction, we could get a situation where the user sees one state in one
        # thread, but then that decision gets overwritten--low probability, but still bad.

        # (If it is truly atomic, we should be fine--if one process is in the
        # process of finding no group and making one, the other should block till it
        # appears.  HOWEVER, if we allow reads by the second one while the first
        # process runs the transaction, we have a problem again: could read empty,
        # have the first transaction finish, and pick a different group in a
        # different process.)

        # If a group id hasn't yet been saved, or the saved group id is invalid,
        # we need to pick one, save it, then return it

        # TODO: had a discussion in arch council about making randomization more
        # deterministic (e.g. some hash).  Could do that, but need to be careful not
        # to introduce correlation between users or bias in generation.

        # See note above for explanation of local_random()
        group = self.random.choice(user_partition.groups)
        self._user_tags_service.set_tag(scope, key, group.id)

        # emit event for analytics
        # FYI - context is always user ID that is logged in, NOT the user id that is
        # being operated on. If instructor can move user explicitly, then we should
        # put in event_info the user id that is being operated on.
        event_info = {
            'group_id': group.id,
            'group_name': group.name,
            'partition_id': user_partition.id,
            'partition_name': user_partition.name
        }
        # TODO: Use the XBlock publish api instead
        self._track_function('xmodule.partitions.assigned_user_to_partition', event_info)

        return group.id
