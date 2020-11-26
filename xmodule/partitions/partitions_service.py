"""
This is a service-like API that assigns tracks which groups users are in for various
user partitions.  It uses the user_service key/value store provided by the LMS runtime to
persist the assignments.
"""


import logging

import six
from django.conf import settings

from openedx.core.lib.cache_utils import request_cached
from openedx.core.lib.dynamic_partitions_generators import DynamicPartitionGeneratorsPluginManager
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import get_partition_from_id

log = logging.getLogger(__name__)

FEATURES = getattr(settings, 'FEATURES', {})


@request_cached()
def get_all_partitions_for_course(course, active_only=False):
    """
    A method that returns all `UserPartitions` associated with a course, as a List.
    This will include the ones defined in course.user_partitions, but it may also
    include dynamically included partitions (such as the `EnrollmentTrackUserPartition`).

    Args:
        course: the course for which user partitions should be returned.
        active_only: if `True`, only partitions with `active` set to True will be returned.

        Returns:
            A List of UserPartitions associated with the course.
    """
    all_partitions = course.user_partitions + _get_dynamic_partitions(course)
    if active_only:
        all_partitions = [partition for partition in all_partitions if partition.active]
    return all_partitions


def get_user_partition_groups(course_key, user_partitions, user, partition_dict_key='name'):
    """
    Collect group ID for each partition in this course for this user.
     Arguments:
        course_key (CourseKey)
        user_partitions (list[UserPartition])
        user (User)
        partition_dict_key - i.e. 'id', 'name' depending on which partition attribute you want as a key.
     Returns:
        dict[partition_dict_key: Group]: Mapping from user partitions to the group to
            which the user belongs in each partition. If the user isn't
            in a group for a particular partition, then that partition's
            ID will not be in the dict.
    """

    partition_groups = {}
    for partition in user_partitions:
        group = partition.scheme.get_group_for_user(
            course_key,
            user,
            partition,
        )

        if group is not None:
            partition_groups[getattr(partition, partition_dict_key)] = group
    return partition_groups


def _get_dynamic_partitions(course):
    """
    Return the dynamic user partitions for this course.
    If none exists, returns an empty array.
    """
    dynamic_partition_generators = DynamicPartitionGeneratorsPluginManager.get_available_plugins().values()
    generated_partitions = []
    for generator in dynamic_partition_generators:
        generated_partition = generator(course)
        if generated_partition:
            generated_partitions.append(generated_partition)

    return generated_partitions


class PartitionService(object):
    """
    This is an XBlock service that returns information about the user partitions associated
    with a given course.
    """

    def __init__(self, course_id, cache=None, course=None):
        self._course_id = course_id
        self._cache = cache
        self.course = course

    def get_course(self):
        """
        Return the course instance associated with this PartitionService.
        This default implementation looks up the course from the modulestore.
        """
        return self.course or modulestore().get_course(self._course_id)

    @property
    def course_partitions(self):
        """
        Return the set of partitions assigned to self._course_id (both those set directly on the course
        through course.user_partitions, and any dynamic partitions that exist). Note: this returns
        both active and inactive partitions.
        """
        return get_all_partitions_for_course(self.get_course())

    def get_user_group_id_for_partition(self, user, user_partition_id):
        """
        If the user is already assigned to a group in user_partition_id, return the
        group_id.

        If not, assign them to one of the groups, persist that decision, and
        return the group_id.

        Args:
            user_partition_id -- an id of a partition that's hopefully in the
                runtime.user_partitions list.

        Returns:
            The id of one of the groups in the specified user_partition_id (as a string).

        Raises:
            ValueError if the user_partition_id isn't found.
        """
        cache_key = "PartitionService.ugidfp.{}.{}.{}".format(
            user.id, self._course_id, user_partition_id
        )

        if self._cache and (cache_key in self._cache):
            return self._cache[cache_key]

        user_partition = self.get_user_partition(user_partition_id)
        if user_partition is None:
            raise ValueError(
                "Configuration problem!  No user_partition with id {0} "
                "in course {1}".format(user_partition_id, self._course_id)
            )

        group = self.get_group(user, user_partition)
        group_id = group.id if group else None

        if self._cache is not None:
            self._cache[cache_key] = group_id

        return group_id

    def get_user_partition(self, user_partition_id):
        """
        Look for a user partition with a matching id in the course's partitions.
        Note that this method can return an inactive user partition.

        Returns:
            A UserPartition, or None if not found.
        """
        return get_partition_from_id(self.course_partitions, user_partition_id)

    def get_group(self, user, user_partition, assign=True):
        """
        Returns the group from the specified user partition to which the user is assigned.
        If the user has not yet been assigned, a group will be chosen for them based upon
        the partition's scheme.
        """
        return user_partition.scheme.get_group_for_user(
            self._course_id, user, user_partition, assign=assign,
        )
