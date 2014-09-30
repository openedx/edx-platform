"""Defines ``Group`` and ``UserPartition`` models for partitioning"""
from collections import namedtuple
# We use ``id`` in this file as the IDs of our Groups and UserPartitions,
# which Pylint disapproves of.
# pylint: disable=invalid-name, redefined-builtin


class Group(namedtuple("Group", "id name")):
    """
    An id and name for a group of students.  The id should be unique
    within the UserPartition this group appears in.
    """
    # in case we want to add to this class, a version will be handy
    # for deserializing old versions.  (This will be serialized in courses)
    VERSION = 1

    def __new__(cls, id, name):
        # pylint: disable=super-on-old-class
        return super(Group, cls).__new__(cls, int(id), name)

    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the group.
        """
        # pylint: disable=no-member
        return {
            "id": self.id,
            "name": self.name,
            "version": Group.VERSION
        }

    @staticmethod
    def from_json(value):
        """
        Deserialize a Group from a json-like representation.

        Args:
            value: a dictionary with keys for the properties of the group.

        Raises TypeError if the value doesn't have the right keys.
        """
        if isinstance(value, Group):
            return value

        for key in ('id', 'name', 'version'):
            if key not in value:
                raise TypeError("Group dict {0} missing value key '{1}'".format(
                    value, key))

        if value["version"] != Group.VERSION:
            raise TypeError("Group dict {0} has unexpected version".format(
                value))

        return Group(value["id"], value["name"])


class UserPartition(namedtuple("UserPartition", "id name description groups")):
    """
    A named way to partition users into groups, primarily intended for running
    experiments.  It is expected that each user will be in at most one group in a
    partition.

    A Partition has an id, name, description, and a list of groups.
    The id is intended to be unique within the context where these are used. (e.g. for
    partitions of users within a course, the ids should be unique per-course)
    """
    VERSION = 1

    def __new__(cls, id, name, description, groups):
        # pylint: disable=super-on-old-class
        return super(UserPartition, cls).__new__(cls, int(id), name, description, groups)

    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the partition.
        """
        # pylint: disable=no-member
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "groups": [g.to_json() for g in self.groups],
            "version": UserPartition.VERSION
        }

    @staticmethod
    def from_json(value):
        """
        Deserialize a Group from a json-like representation.

        Args:
            value: a dictionary with keys for the properties of the group.

        Raises TypeError if the value doesn't have the right keys.
        """
        if isinstance(value, UserPartition):
            return value

        for key in ('id', 'name', 'description', 'version', 'groups'):
            if key not in value:
                raise TypeError("UserPartition dict {0} missing value key '{1}'"
                                .format(value, key))

        if value["version"] != UserPartition.VERSION:
            raise TypeError("UserPartition dict {0} has unexpected version"
                            .format(value))

        groups = [Group.from_json(g) for g in value["groups"]]

        return UserPartition(
            value["id"],
            value["name"],
            value["description"],
            groups
        )
