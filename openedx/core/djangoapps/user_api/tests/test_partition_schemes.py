"""
Test the user api's partition extensions.
"""
from collections import defaultdict
from mock import patch
from unittest import TestCase

from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme, UserPartitionError
from student.tests.factories import UserFactory
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.partitions.tests.test_partitions import PartitionTestCase


class MemoryCourseTagAPI(object):
    """
    An implementation of a user service that uses an in-memory dictionary for storage
    """
    def __init__(self):
        self._tags = defaultdict(dict)

    def get_course_tag(self, __, course_id, key):
        """Sets the value of ``key`` to ``value``"""
        return self._tags[course_id].get(key)

    def set_course_tag(self, __, course_id, key, value):
        """Gets the value of ``key``"""
        self._tags[course_id][key] = value


class TestRandomUserPartitionScheme(PartitionTestCase):
    """
    Test getting a user's group out of a partition
    """

    MOCK_COURSE_ID = "mock-course-id"

    def setUp(self):
        super(TestRandomUserPartitionScheme, self).setUp()
        # Patch in a memory-based user service instead of using the persistent version
        course_tag_api = MemoryCourseTagAPI()
        self.user_service_patcher = patch(
            'openedx.core.djangoapps.user_api.partition_schemes.course_tag_api', course_tag_api
        )
        self.user_service_patcher.start()
        self.addCleanup(self.user_service_patcher.stop)

        # Create a test user
        self.user = UserFactory.create()

    def test_get_group_for_user(self):
        # get a group assigned to the user
        group1_id = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, self.user_partition)

        # make sure we get the same group back out every time
        for __ in range(10):
            group2_id = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, self.user_partition)
            self.assertEqual(group1_id, group2_id)

    def test_get_group_for_user_with_assign(self):
        """
        Make sure get_group_for_user returns None if no group is already
        assigned to a user instead of assigning/creating a group automatically
        """
        # We should not get any group because assign is False which will
        # protect us from automatically creating a group for user
        group = RandomUserPartitionScheme.get_group_for_user(
            self.MOCK_COURSE_ID, self.user, self.user_partition, assign=False
        )

        self.assertIsNone(group)

        # We should get a group automatically assigned to user
        group = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, self.user_partition)

        self.assertIsNotNone(group)

    def test_empty_partition(self):
        empty_partition = UserPartition(
            self.TEST_ID,
            'Test Partition',
            'for testing purposes',
            [],
            scheme=RandomUserPartitionScheme
        )
        # get a group assigned to the user
        with self.assertRaisesRegexp(UserPartitionError, "Cannot assign user to an empty user partition"):
            RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, empty_partition)

    def test_user_in_deleted_group(self):
        # get a group assigned to the user - should be group 0 or 1
        old_group = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, self.user_partition)
        self.assertIn(old_group.id, [0, 1])

        # Change the group definitions! No more group 0 or 1
        groups = [Group(3, 'Group 3'), Group(4, 'Group 4')]
        user_partition = UserPartition(self.TEST_ID, 'Test Partition', 'for testing purposes', groups)

        # Now, get a new group using the same call - should be 3 or 4
        new_group = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, user_partition)
        self.assertIn(new_group.id, [3, 4])

        # We should get the same group over multiple calls
        new_group_2 = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, user_partition)
        self.assertEqual(new_group, new_group_2)

    def test_change_group_name(self):
        # Changing the name of the group shouldn't affect anything
        # get a group assigned to the user - should be group 0 or 1
        old_group = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, self.user_partition)
        self.assertIn(old_group.id, [0, 1])

        # Change the group names
        groups = [Group(0, 'Group 0'), Group(1, 'Group 1')]
        user_partition = UserPartition(
            self.TEST_ID,
            'Test Partition',
            'for testing purposes',
            groups,
            scheme=RandomUserPartitionScheme
        )

        # Now, get a new group using the same call
        new_group = RandomUserPartitionScheme.get_group_for_user(self.MOCK_COURSE_ID, self.user, user_partition)
        self.assertEqual(old_group.id, new_group.id)


class TestExtension(TestCase):
    """
    Ensure that the scheme extension is correctly plugged in (via entry point
    in setup.py)
    """

    def test_get_scheme(self):
        self.assertEqual(UserPartition.get_scheme('random'), RandomUserPartitionScheme)
        with self.assertRaisesRegexp(UserPartitionError, 'Unrecognized scheme'):
            UserPartition.get_scheme('other')
