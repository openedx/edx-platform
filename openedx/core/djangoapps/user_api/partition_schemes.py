"""
Provides partition support to the user service.
"""
import logging
import random
import course_tag.api as course_tag_api

from xmodule.partitions.partitions import UserPartitionError, NoSuchUserPartitionGroupError

log = logging.getLogger(__name__)


class RandomUserPartitionScheme(object):
    """
    This scheme randomly assigns users into the partition's groups.
    """
    RANDOM = random.Random()

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition, assign=True, track_function=None):
        """
        Returns the group from the specified user position to which the user is assigned.
        If the user has not yet been assigned, a group will be randomly chosen for them if assign flag is True.
        """
        partition_key = cls.key_for_partition(user_partition)
        group_id = course_tag_api.get_course_tag(user, course_key, partition_key)

        group = None
        if group_id is not None:
            # attempt to look up the presently assigned group
            try:
                group = user_partition.get_group(int(group_id))
            except NoSuchUserPartitionGroupError:
                # jsa: we can turn off warnings here if this is an expected case.
                log.warn(
                    "group not found in RandomUserPartitionScheme: %r",
                    {
                        "requested_partition_id": user_partition.id,
                        "requested_group_id": group_id,
                    },
                    exc_info=True
                )

        if group is None and assign:
            if not user_partition.groups:
                raise UserPartitionError('Cannot assign user to an empty user partition')

            # pylint: disable=fixme
            # TODO: had a discussion in arch council about making randomization more
            # deterministic (e.g. some hash).  Could do that, but need to be careful not
            # to introduce correlation between users or bias in generation.
            group = cls.RANDOM.choice(user_partition.groups)

            # persist the value as a course tag
            course_tag_api.set_course_tag(user, course_key, partition_key, group.id)

            if track_function:
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
                # pylint: disable=fixme
                # TODO: Use the XBlock publish api instead
                track_function('xmodule.partitions.assigned_user_to_partition', event_info)

        return group

    @classmethod
    def key_for_partition(cls, user_partition):
        """
        Returns the key to use to look up and save the user's group for a given user partition.
        """
        return 'xblock.partition_service.partition_{0}'.format(user_partition.id)
