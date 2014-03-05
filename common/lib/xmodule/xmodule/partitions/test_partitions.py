"""
Test the partitions and partitions service

"""

from collections import defaultdict
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

    def test_from_json_broken(self):
        test_id = 5
        name = "Grendel"
        # Bad version
        jsonified = {
            "id": test_id,
            "name": name,
            "version": 9001
        }
        with self.assertRaisesRegexp(TypeError, "has unexpected version"):
            group = Group.from_json(jsonified)

        # Missing key "id"
        jsonified = {
            "name": name,
            "version": Group.VERSION
        }
        with self.assertRaisesRegexp(TypeError, "missing value key 'id'"):
            group = Group.from_json(jsonified)

        # Has extra key - should not be a problem
        jsonified = {
            "id": test_id,
            "name": name,
            "version": Group.VERSION,
            "programmer": "Cale"
        }
        group = Group.from_json(jsonified)
        self.assertNotIn("programmer", group.to_json())


class TestUserPartition(TestCase):
    """Test constructing UserPartitions"""
    def test_construct(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        user_partition = UserPartition(0, 'Test Partition', 'for testing purposes', groups)
        self.assertEqual(user_partition.id, 0)
        self.assertEqual(user_partition.name, "Test Partition")
        self.assertEqual(user_partition.description, "for testing purposes")
        self.assertEqual(user_partition.groups, groups)

    def test_string_id(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        user_partition = UserPartition("70", 'Test Partition', 'for testing purposes', groups)
        self.assertEqual(user_partition.id, 70)

    def test_to_json(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        upid = 0
        upname = "Test Partition"
        updesc = "for testing purposes"
        user_partition = UserPartition(upid, upname, updesc, groups)

        jsonified = user_partition.to_json()
        act_jsonified = {
            "id": upid,
            "name": upname,
            "description": updesc,
            "groups": [group.to_json() for group in groups],
            "version": user_partition.VERSION
        }
        self.assertEqual(jsonified, act_jsonified)

    def test_from_json(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        upid = 1
        upname = "Test Partition"
        updesc = "For Testing Purposes"

        jsonified = {
            "id": upid,
            "name": upname,
            "description": updesc,
            "groups": [group.to_json() for group in groups],
            "version": UserPartition.VERSION
        }
        user_partition = UserPartition.from_json(jsonified)
        self.assertEqual(user_partition.id, upid)
        self.assertEqual(user_partition.name, upname)
        self.assertEqual(user_partition.description, updesc)
        for act_group in user_partition.groups:
            self.assertIn(act_group.id, [0, 1])
            exp_group = groups[act_group.id]
            self.assertEqual(exp_group.id, act_group.id)
            self.assertEqual(exp_group.name, act_group.name)

    def test_from_json_broken(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        upid = 1
        upname = "Test Partition"
        updesc = "For Testing Purposes"

        # Missing field
        jsonified = {
            "name": upname,
            "description": updesc,
            "groups": [group.to_json() for group in groups],
            "version": UserPartition.VERSION
        }
        with self.assertRaisesRegexp(TypeError, "missing value key 'id'"):
            user_partition = UserPartition.from_json(jsonified)

        # Wrong version (it's over 9000!)
        jsonified = {
            'id': upid,
            "name": upname,
            "description": updesc,
            "groups": [group.to_json() for group in groups],
            "version": 9001
        }
        with self.assertRaisesRegexp(TypeError, "has unexpected version"):
            user_partition = UserPartition.from_json(jsonified)

        # Has extra key - should not be a problem
        jsonified = {
            'id': upid,
            "name": upname,
            "description": updesc,
            "groups": [group.to_json() for group in groups],
            "version": UserPartition.VERSION,
            "programmer": "Cale"
        }
        user_partition = UserPartition.from_json(jsonified)
        self.assertNotIn("programmer", user_partition.to_json())


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


class MemoryUserTagsService(object):
    """
    An implementation of a user_tags XBlock service that
    uses an in-memory dictionary for storage
    """
    COURSE_SCOPE = 'course'

    def __init__(self):
        self._tags = defaultdict(dict)

    def get_tag(self, scope, key):
        """Sets the value of ``key`` to ``value``"""
        print 'GETTING', scope, key, self._tags
        return self._tags[scope].get(key)

    def set_tag(self, scope, key, value):
        """Gets the value of ``key``"""
        self._tags[scope][key] = value
        print 'SET', scope, key, value, self._tags


class TestPartitionsService(TestCase):
    """
    Test getting a user's group out of a partition
    """

    def setUp(self):
        groups = [Group(0, 'Group 1'), Group(1, 'Group 2')]
        self.partition_id = 0

        self.user_tags_service = MemoryUserTagsService()

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
