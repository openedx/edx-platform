"""
Test the partitions and partitions service

"""

from unittest import TestCase
from mock import Mock, MagicMock

from xmodule.partitions.partitions import Group, UserPartition
from xmodule.partitions.partitions_service import PartitionService


class TestGroup(TestCase):
    """Test constructing groups"""
    def test_construct(self):
        test_id = 10
        name = "Grendel"
        group = Group(test_id, name)
        self.assertEqual(group.id, test_id)
        self.assertEqual(group.name, name)

    def test_string_id(self):
        test_id = "10"
        name = "Grendel"
        group = Group(test_id, name)
        self.assertEqual(group.id, 10)

    def test_to_json(self):
        test_id = 10
        name = "Grendel"
        group = Group(test_id, name)
        jsonified = group.to_json()
        act_jsonified = {
            "id": test_id,
            "name": name,
            "version": group.VERSION
        }
        self.assertEqual(jsonified, act_jsonified)

    def test_from_json(self):
        test_id = 5
        name = "Grendel"
        jsonified = {
            "id": test_id,
            "name": name,
            "version": Group.VERSION
        }
        group = Group.from_json(jsonified)
        self.assertEqual(group.id, test_id)
        self.assertEqual(group.name, name)


class StaticPartitionService(PartitionService):
    """
    Mock PartitionService for testing.
    """
    def __init__(self, partitions, **kwargs):
        super(StaticPartitionService, self).__init__(**kwargs)
        self._partitions = partitions

    @property
    def course_partitions(self):
        return self._partitions


class TestPartitionsService(TestCase):
    """
    Test getting a user's group out of a partition

    """

    def setUp(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        self.partition_id = 0

        # construct the user_service
        self.user_tags = dict()
        self.user_tags_service = MagicMock()

        def mock_set_tag(_scope, key, value):
            """Sets the value of ``key`` to ``value``"""
            self.user_tags[key] = value

        def mock_get_tag(_scope, key):
            """Gets the value of ``key``"""
            if key in self.user_tags:
                return self.user_tags[key]
            return None

        self.user_tags_service.set_tag = mock_set_tag
        self.user_tags_service.get_tag = mock_get_tag

        user_partition = UserPartition(self.partition_id, 'Test Partition', 'for testing purposes', groups)
        self.partitions_service = StaticPartitionService(
            [user_partition],
            user_tags_service=self.user_tags_service,
            course_id=Mock(),
            track_function=Mock()
        )

    def test_get_user_group_for_partition(self):
        # get a group assigned to the user
        group1 = self.partitions_service.get_user_group_for_partition(self.partition_id)

        # make sure we get the same group back out if we try a second time
        group2 = self.partitions_service.get_user_group_for_partition(self.partition_id)

        self.assertEqual(group1, group2)

        # test that we error if given an invalid partition id
        with self.assertRaises(ValueError):
            self.partitions_service.get_user_group_for_partition(3)

    def test_user_in_deleted_group(self):
        # get a group assigned to the user - should be group 0 or 1
        old_group = self.partitions_service.get_user_group_for_partition(self.partition_id)
        self.assertIn(old_group, [0, 1])

        # Change the group definitions! No more group 0 or 1
        groups = [Group(3, 'Group 3'), Group(4, 'Group 4')]
        user_partition = UserPartition(self.partition_id, 'Test Partition', 'for testing purposes', groups)
        self.partitions_service = StaticPartitionService(
            [user_partition],
            user_tags_service=self.user_tags_service,
            course_id=Mock(),
            track_function=Mock()
        )

        # Now, get a new group using the same call - should be 3 or 4
        new_group = self.partitions_service.get_user_group_for_partition(self.partition_id)
        self.assertIn(new_group, [3, 4])

        # We should get the same group over multiple calls
        new_group_2 = self.partitions_service.get_user_group_for_partition(self.partition_id)
        self.assertEqual(new_group, new_group_2)

    def test_change_group_name(self):
        # Changing the name of the group shouldn't affect anything
        # get a group assigned to the user - should be group 0 or 1
        old_group = self.partitions_service.get_user_group_for_partition(self.partition_id)
        self.assertIn(old_group, [0, 1])

        # Change the group names
        groups = [Group(0, 'Group 0'), Group(1, 'Group 1')]
        user_partition = UserPartition(self.partition_id, 'Test Partition', 'for testing purposes', groups)
        self.partitions_service = StaticPartitionService(
            [user_partition],
            user_tags_service=self.user_tags_service,
            course_id=Mock(),
            track_function=Mock()
        )

        # Now, get a new group using the same call
        new_group = self.partitions_service.get_user_group_for_partition(self.partition_id)
        self.assertEqual(old_group, new_group)
