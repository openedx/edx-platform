"""
This is a service-like API that assigns tracks which groups users are in for various
user partitions.  It uses the user_service key/value store provided by the LMS runtime to
persist the assignments.
"""

import random

# tl;dr: global state is bad.  The capa library reseeds random every time a problem is
# loaded.  Even if and when that's fixed, it's a good idea to have a local generator to
# avoid any other code that messes with the global random module.
_local_random = None

def local_random():
    """
    Get the local random number generator.  In a function so that we don't run
    random.Random() at import time.
    """
    # ironic, isn't it?
    global _local_random

    if _local_random is None:
        _local_random = random.Random()

    return _local_random



def get_user_group_for_partition(runtime, user_partition_id):
    """
    If the user is already assigned to a group in user_partition_id, return the
    group_id.

    If not, assign them to one of the groups, persist that decision, and
    return the group_id.

    If the group they are assigned to doesn't exist anymore, re-assign to one of
    the existing groups and return its id.

    Args:
         runtime: a runtime object.  Expected to have keys
             course_id -- the current course id
             user_service -- the User service
             user_partitions -- the list of partition.UserPartition objects defined in
                 this course
        user_partition_id -- an id of a partition that's hopefully in the
            runtime.user_partitions list.

    Returns:
        The id of one of the groups in the specified user_partition_id (as a string).

    Raises:
        ValueError if the user_partition_id isn't found.
    """
    user_partition = _get_user_partition(runtime, user_partition_id)
    if user_partition is None:
        raise ValueError(
            "Configuration problem!  No user_partition with id {0} "
            "in course {1}".format(user_partition_id, runtime.course_id))

    group_id = _get_group(runtime, user_partition)
    
    return group_id


def _get_user_partition(runtime, user_partition_id):
    """
    Look for a user partition with a matching id in
    in the course's partitions.

    Returns:
        A UserPartition, or None if not found.
    """
    for partition in runtime.user_partitions:
        if partition.id == user_partition_id:
            return partition

    return None


def _key_for_partition(user_partition):
    """
    Returns the key to use to look up and save the user's group for a particular
    condition.  Always use this function rather than constructing the key directly.
    """
    return 'xblock.partition_service.partition_{0}'.format(user_partition.id)


def _get_group(runtime, user_partition):
    """
    Return the group of the current user in user_partition.  If they don't already have
    one assigned, pick one and save it.  Uses the runtime's user_service service to look up
    and persist the info.
    """
    key = _key_for_partition(user_partition)
    scope = runtime.user_service.COURSE

    group_id = runtime.user_service.get_tag(scope, key)

    if group_id != None:
        # TODO: check whether this id is valid.  If not, create a new one.
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


    # otherwise, we need to pick one, save it, then return it

    # TODO: had a discussion in arch council about making randomization more
    # deterministic (e.g. some hash).  Could do that, but need to be careful not
    # to introduce correlation between users or bias in generation.

    # See note above for explanation of local_random()
    group = local_random().choice(user_partition.groups)
    runtime.user_service.set_tag(scope, key, group.id)

    # emit event for analytics:
    # TODO: is this all the needed info?
    event_info = {'group_id': group.id,
             'group_name': group.name,
             'partition_id': user_partition.id,
             'partition_name': user_partition.name}
    runtime.track_function('assigned_user_to_partition', event_info)

    return group.id

